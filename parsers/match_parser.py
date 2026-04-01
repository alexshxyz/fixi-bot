"""
Основная логика парсинга одного матча.
Координация: загрузка страницы, инициализация браузера, вызов парсеров и отправка результатов.
"""
import asyncio
import re
import traceback
from datetime import datetime, timedelta
from playwright.async_api import Page, TimeoutError
from core.config import RATE
from database.database import insert_match_to_db, check_match_exists
from .playwright_utils import wait_for_JS_object
from telegram.telegram_client import send_message
from database.models import Match
from .helpers import has_red, has_black, sanitize_league_name, sanitize_team_name
from .match_validator import validate_and_get_final_data
from .over_parser import parse_over_odds
from .handicap_parser import parse_asian_handicap
from utils.utils import strip_html_tags


async def parse_match(page: Page, match_id: str):
    """
    Парсит матч с сайта nowgoal.com и извлекает коэффициенты Over/Under и Asian Handicap.
    Отправляет найденные матчи в Telegram и сохраняет в БД.
    
    Args:
        page: Playwright Page объект
        match_id: ID матча на nowgoal.com
    """
    try:
        print(f"PARSING {match_id}")
        url = f'https://live5.nowgoal26.com/oddscomp/{match_id}'
        
        # Повторные попытки загрузки страницы (до 3 раз)
        for attempt in range(3):
            try:
                # Используем commit вместо load для более надежной загрузки
                await page.goto(url, wait_until='domcontentloaded', timeout=90000)
                # Дополнительно даем время на загрузку JavaScript
                await asyncio.sleep(1)
                break
            except Exception as e:
                error_str = str(e).lower()
                # ERR_ABORTED, ERR_CONNECTION_RESET и подобные ошибки - просто пропускаем матч
                if 'aborted' in error_str or 'reset' in error_str or 'refused' in error_str or 'blocke' in error_str:
                    return
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    return

        # Проверяем что мы на правильной странице (не на about:blank)
        current_url = page.url
        if 'about:blank' in current_url or current_url == '':
            return
        
        # Ждём h1 элемента
        try:
            await page.wait_for_selector('h1', timeout=15000)
        except Exception as e:
            return

        await asyncio.sleep(1)

        # Ожидание загрузки JS-объекта _oddsDetailWin
        try:
            await wait_for_JS_object(page, '_oddsDetailWin', timeout_ms=30000)
        except TimeoutError:
            # Если объект не загружается, пробуем переместить страницу (refresh) или выходим
            try:
                await page.reload(wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)
                # Проверяем ещё раз
                result = await page.evaluate("typeof _oddsDetailWin !== 'undefined'")
                if not result:
                    return
            except Exception as e:
                return

        # Проверяем что объект действительно существует перед вызовом
        try:
            obj_exists = await page.evaluate("typeof _oddsDetailWin !== 'undefined' && _oddsDetailWin !== null")
            if not obj_exists:
                return
        except Exception as e:
            return

        # Вызываем JS функцию с защитой от ошибок
        try:
            result = await page.evaluate(f"""
                (function() {{
                    try {{
                        if (typeof _oddsDetailWin !== 'undefined' && _oddsDetailWin && _oddsDetailWin.open) {{
                            _oddsDetailWin.open('{match_id}', 3, 'Crown', -1, ('0' == 1));
                            return true;
                        }} else {{
                            return false;
                        }}
                    }} catch (e) {{
                        console.error('open() error:', e);
                        return false;
                    }}
                }})()
            """)
            if not result:
                return
        except Exception as e:
            return
        
        # Ждём инициализации _oddsDetailWin после open()
        await asyncio.sleep(3)

        # Инициализация хранилищ данных
        over_values = {'half': None, 'full': None}
        over_meta = {'half': {'over': None, 'goals': "", 'tab': "", 'red': False},
                     'full': {'over': None, 'goals': "", 'tab': "", 'red': False}}
        ah_meta = {'half': {'val': None, 'red': False, 'ok': False}, 'full': {'val': None, 'red': False, 'ok': False}}
        datetime_object = None
        rate_value = RATE
        liga = ""

        # Парсим для обеих временных половин (HT и FT)
        for state in (True, False):
            try:
                # Проверяем что объект всё ещё существует перед использованием (ВАЖНО: не обращаемся к методам!)
                try:
                    obj_exists = await page.evaluate("typeof _oddsDetailWin !== 'undefined' && _oddsDetailWin !== null")
                    if not obj_exists:
                        continue
                except Exception as e:
                    continue
                
                # Вызываем JS функцию для переключения временной половины
                state_str = "true" if state else "false"
                state_name = "First Half" if state else "Full Time"
                try:
                    await page.evaluate(f"_oddsDetailWin.checkedHF({state_str})")
                    await asyncio.sleep(2)  # Ждём загрузки данных после переключения
                except Exception as e:
                    error_str = str(e).lower()
                    if 'this.restore is not a function' in str(e):
                        await asyncio.sleep(4)
                    elif 'cannot read properties of null' in error_str:
                        continue
                    elif 'destroyed' in error_str or 'undefined' in error_str or 'null' in error_str:
                        continue
                    else:
                        await asyncio.sleep(2)

                # Ждём таблицу
                try:
                    await page.wait_for_selector('#oudetail', timeout=10000)
                except Exception:
                    continue

                await asyncio.sleep(0.5)

                # Получаем HTML таблицы
                try:
                    table_html = await page.inner_html('#oudetail')
                except Exception as e:
                    continue

                # Проверяем наличие "No Data!" в таблице - пропускаем весь матч
                if 'nodata' in table_html.lower() or 'no data' in table_html.lower():
                    return

                # Извлекаем строки таблицы
                rows_html = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
                
                # Фильтруем строки без 'flexed' класса
                rows_html = [r for r in rows_html if 'flexed' not in r]
                
                if not rows_html:
                    continue

                # Пропускаем таблицу, если коэффициенты чёрные (#222)
                try:
                    if any(has_black(r) for r in rows_html):
                        continue
                except Exception:
                    pass

                # Извлекаем дату первый раз
                if datetime_object is None:
                    try:
                        # Ищем элемент с классом time и парсим data-t атрибут
                        time_elem = await page.query_selector('td.time[data-t]')
                        if time_elem:
                            data_t = await time_elem.get_attribute('data-t')
                            if data_t:
                                # Парсим дату из строки вроде "Sat Mar 14 2026 13:19:37 GMT+0300..."
                                try:
                                    # Пытаемся парсить:
                                    from datetime import datetime as dt
                                    # Убираем часовой пояс и другой текст после GMT
                                    date_part = data_t.split('GMT')[0].strip()  # "Sat Mar 14 2026 13:19:37"
                                    datetime_object = dt.strptime(date_part, "%a %b %d %Y %H:%M:%S")
                                except Exception as parse_err:
                                    datetime_object = datetime.utcnow()
                        else:
                            datetime_object = datetime.utcnow()
                    except Exception as e:
                        datetime_object = datetime.utcnow()

                # Пытаемся получить лигу с этой половины
                if not liga:
                    try:
                        liga_raw = await page.text_content('.LName')
                        if liga_raw:
                            liga = sanitize_league_name(liga_raw.strip())
                    except Exception as e:
                        pass

                key = 'half' if state else 'full'
                
                # Парсим Over коэффициенты
                await parse_over_odds(page, match_id, key, state, over_values, over_meta)

                # Парсим Asian Handicap
                await parse_asian_handicap(page, key, state, ah_meta, rate_value)

            except Exception as e:
                print(f"[ERROR] Ошибка при обработке state={state} для {url}: {e}")
                traceback.print_exc()
                continue

        if over_values['half'] is None and over_values['full'] is None:
            return

        # === ЯВНОЕ ОЖИДАНИЕ ВСЕХ ЭЛЕМЕНТОВ ДО ОТПРАВКИ ===
        # Даем браузеру время загрузить все нужные элементы перед отправкой
        
        # Явно ждем появления критичных элементов
        elements_ready = False
        for attempt in range(3):
            try:
                # Проверяем что все критичные элементы загружены
                checks = {
                    'Liga (.LName)': await page.query_selector('.LName'),
                    'H1 (команды)': await page.query_selector('h1'),
                    'Score (.score)': await page.query_selector_all('.score'),
                }
                
                all_ready = True
                for elem_name, elem in checks.items():
                    if isinstance(elem, list):
                        ready = len(elem) >= 2
                    else:
                        ready = elem is not None
                    
                    if not ready:
                        all_ready = False
                
                if all_ready:
                    elements_ready = True
                    break
                else:
                    if attempt < 2:
                        await asyncio.sleep(2)
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2)

        # Если datetime_object не инициализирован, используем текущее время
        if datetime_object is None:
            datetime_object = datetime.utcnow()

        # Проверяем время (матч должен быть свежим)
        delta = datetime.utcnow() - timedelta(hours=2) - datetime_object
        time_ok = delta.total_seconds() > 60

        try:
            rate_value = float(rate_value)
        except Exception:
            pass

        # Определяем, какие Over view сработали
        triggered_kinds = []
        for kind, val in over_values.items():
            if val is None:
                continue
            red_here = bool(over_meta.get(kind, {}).get('red', False))
            goals = over_meta.get(kind, {}).get('goals', "")
            tab = over_meta.get(kind, {}).get('tab', "")
            
            if not red_here:
                pass
            elif not time_ok:
                pass
            elif val > rate_value:
                pass
            else:
                triggered_kinds.append(kind)

        # Определяем, какие AH view сработали
        triggered_ah_kinds = []
        for kind in ('half', 'full'):
            ah = ah_meta.get(kind, {})
            val = ah.get('val')
            red_here = bool(ah.get('red', False))
            handicap_text = ah.get('handicap_text', "")
            
            if val is None:
                continue
            
            if not red_here:
                pass
            elif not time_ok:
                pass
            else:
                try:
                    if float(val) > float(rate_value):
                        pass
                    else:
                        triggered_ah_kinds.append(kind)
                except Exception as e:
                    pass

        # Отправляем Over матчи
        if triggered_kinds:
            # Переполучаем все данные перед отправкой - гарантируем что счет есть
            validated = await validate_and_get_final_data(page, match_id)
            
            # Используем переполученные данные (даже если браузер переместился)
            liga = validated['liga'] or liga
            first_team = validated['first_team'] or first_team
            second_team = validated['second_team'] or second_team
            first_score = validated['first_score'] or first_score
            second_score = validated['second_score'] or second_score
            
            for kind in triggered_kinds:
                meta = over_meta.get(kind, {})
                try:
                    # Определяем исход: 'half' -> 'HT', 'full' -> 'FT'
                    if kind == 'half':
                        tab_label = "HT"
                    elif kind == 'full':
                        tab_label = "FT"
                    else:
                        tab_label = kind
                    
                    # ВАЛИДАЦИЯ ПЕРЕД ОТПРАВКОЙ
                    if match_id not in url:
                        print(f"[ERROR] URL не содержит match_id! url='{url}', match_id='{match_id}'")
                        continue
                    
                    meta_tab = meta.get('tab', '')
                    if meta_tab and meta_tab != tab_label:
                        print(f"[ERROR] Несоответствие исхода!")
                        continue
                    
                    validation_errors = []
                    if not liga:
                        validation_errors.append("Liga")
                    if not first_team or not second_team:
                        validation_errors.append("Teams")
                    if not first_score or not second_score:
                        validation_errors.append("Score")
                    
                    if validation_errors:
                        print(f"[ERROR] No data for Over: {', '.join(validation_errors)}")
                        continue
                    
                    
                    match = Match(
                        liga=liga,
                        first_team=first_team,
                        second_team=second_team,
                        first_team_score=first_score,
                        second_team_score=second_score,
                        goals=str(meta.get('goals', "")),
                        over=None,
                        tab=tab_label,
                        url=url,
                        over_half=over_values.get('half'),
                        over_full=over_values.get('full'),
                        chosen_kind=kind,
                        chosen_over=meta.get('over')
                    )
                    msg = str(match)
                    
                    # Извлекаем prediction текст из сформированного сообщения
                    msg_lines = msg.splitlines()
                    prediction_text = msg_lines[3] if len(msg_lines) > 3 else ""
                    # ВАЖНО: очищаем HTML теги, как делает insert_match_to_db
                    prediction_text = strip_html_tags(prediction_text)
                    
                    # Логируем для отладки
                    print(f"[DEBUG] Over: url={url}, prediction_text='{prediction_text}'")
                    
                    # Проверяем комбинацию link + prediction через БД
                    if check_match_exists(url, prediction=prediction_text):
                        print(f"[SKIP] Over сигнал уже отправлен (найден в БД): {url} | {prediction_text}")
                        continue
                    
                    print("ALERT SENT")
                    send_message(msg)
                    try:
                        print("MATCH INSERT INTO DB")
                        insert_match_to_db(match, prediction_text=prediction_text)
                    except Exception as e:
                        print(f"[ERROR] insert to DB failed: {e}")
                except Exception as e:
                    print(f"[ERROR] Ошибка при создании/отправке матча для {url} (kind={kind}): {e}")

        # Отправляем AH матчи
        if triggered_ah_kinds:
            validated = await validate_and_get_final_data(page, match_id)
            
            # Используем переполученные данные (даже если браузер переместился)
            liga = validated['liga'] or liga
            first_team = validated['first_team'] or first_team
            second_team = validated['second_team'] or second_team
            first_score = validated['first_score'] or first_score
            second_score = validated['second_score'] or second_score
            
            for kind in triggered_ah_kinds:
                ah_kind = f"ah_{kind}"
                try:
                    handicap_text = ah_meta.get(kind, {}).get('handicap_text', "") or ""
                    span_main_raw = ah_meta.get(kind, {}).get('span_main_raw', "") or ""
                    val_for_display = ah_meta.get(kind, {}).get('val')
                    main_val_for_msg = ah_meta.get(kind, {}).get('main_val', None)
                    
                    if handicap_text:
                        display_handicap = handicap_text
                    elif span_main_raw:
                        display_handicap = span_main_raw
                    elif val_for_display is not None:
                        display_handicap = str(val_for_display)
                    else:
                        display_handicap = ""

                    # Определяем, отрицательная ли фора по наличию "-" в тексте
                    # Примеры: "0/-0.5" содержит "-", значит отрицательная
                    #          "0/0.5" не содержит "-", значит положительная
                    is_negative_handicap = '-' in display_handicap
                    
                    # Если фора положительная (без "-"), добавляем минус перед ней
                    # Примеры: "0/0.5" → "-0/0.5", "1.5" → "-1.5"
                    if not is_negative_handicap:
                        s = display_handicap.strip()
                        if s and not s.startswith('-'):
                            if '/' in s:
                                left, right = [p.strip() for p in s.split('/', 1)]
                                display_handicap = f"-{left}/{right}"
                            else:
                                display_handicap = f"-{s}"
                    
                    # Определяем команду по знаку форы
                    # Если фора отрицательная ("-" в тексте), то гостевая команда (second_team)
                    # Если фора положительная (нет "-"), то домашняя команда (first_team)
                    if is_negative_handicap:
                        team_name = second_team
                    else:
                        team_name = first_team

                    tab_label = "HT" if kind == 'half' else "FT"
                    goals_field = f"{display_handicap} {team_name}".strip()
                    
                    # ВАЛИДАЦИЯ ПЕРЕД ОТПРАВКОЙ AH
                    if match_id not in url:
                        print(f"[ERROR] URL не содержит match_id! url='{url}', match_id='{match_id}'")
                        continue
                    
                    validation_errors = []
                    if not liga:
                        validation_errors.append("Liga")
                    if not first_team or not second_team:
                        validation_errors.append("Teams")
                    if not first_score or not second_score:
                        validation_errors.append("Score")
                    if not display_handicap:
                        validation_errors.append("Handicap")
                    
                    if validation_errors:
                        print(f"[ERROR] No data for AH: {', '.join(validation_errors)}")
                        continue
                    
                    ah = ah_meta.get(kind, {})

                    match = Match(
                        liga=liga,
                        first_team=first_team,
                        second_team=second_team,
                        first_team_score=first_score,
                        second_team_score=second_score,
                        goals=str(goals_field),
                        over=None,
                        tab=tab_label,
                        url=url,
                        over_half=over_values.get('half'),
                        over_full=over_values.get('full'),
                        chosen_kind=ah_kind,
                        chosen_over=ah_meta.get(kind, {}).get('val')
                    )
                    msg = str(match)
                    
                    # Извлекаем prediction текст из сформированного сообщения
                    msg_lines = msg.splitlines()
                    prediction_text = msg_lines[3] if len(msg_lines) > 3 else ""
                    # ВАЖНО: очищаем HTML теги, как делает insert_match_to_db
                    prediction_text = strip_html_tags(prediction_text)
                    
                    # Логируем для отладки
                    print(f"[DEBUG] AH: url={url}, prediction_text='{prediction_text}'")
                    
                    # Проверяем комбинацию link + prediction через БД
                    if check_match_exists(url, prediction=prediction_text):
                        print(f"[SKIP] AH сигнал уже отправлен (найден в БД): {url} | {prediction_text}")
                        continue
                    
                    print("ALERT SENT")
                    send_message(msg)
                    try:
                        print("MATCH INSERT INTO DB")
                        insert_match_to_db(match, prediction_text=prediction_text)
                    except Exception as e:
                        print(f"[ERROR] insert to DB failed: {e}")
                except Exception as e:
                    print(f"[ERROR] Ошибка при создании/отправке AH-матча для {url} (kind={kind}): {e}")

    except Exception as e:
        print(f"[ERROR] Ошибка браузера для {match_id}: {e}")
        traceback.print_exc()
    finally:
        # Очищаем страницу для следующего использования
        try:
            # Ждем короткое время перед переходом на about:blank
            await asyncio.sleep(0.5)
            await page.goto("about:blank", wait_until='domcontentloaded', timeout=10000)
        except Exception as e:
            print(f"[CLEANUP ERROR] Failed to clear page for {match_id}: {e}")
            # Даже если очистка не удалась, продолжаем

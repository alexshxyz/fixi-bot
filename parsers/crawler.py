"""
Сборщик матчей и параллельная обработка.
Получение списка всех матчей со страницы и их парсинг с помощью пула Playwright страниц.
"""
import asyncio
import re
from playwright.async_api import Page
from core.config import MAX_WORKERS
from .playwright_utils import init_browser, cleanup_browser
from .match_parser import parse_match


async def parse_all_matches():
    """
    Парсит все живые матчи со страницы https://live5.nowgoal26.com/
    и запускает параллельный парсинг каждого матча используя пул страниц.
    """
    # Инициализируем браузер с пулом страниц
    try:
        browser, context, pages = await init_browser(max_pages=MAX_WORKERS)
    except Exception as e:
        print(f"[ERROR] Failed to initialize browser: {e}")
        return
    
    # Резервируем первую страницу для сбора матчей, остальные для парсинга
    main_page = pages[0]
    worker_pages = pages[1:]  # Страницы 1-9 для парсинга матчей
    
    try:
        # Загружаем главную страницу
        for retry in range(3):
            try:
                await main_page.goto('https://live5.nowgoal26.com/', wait_until='domcontentloaded', timeout=60000)
                break
            except Exception as e:
                if retry < 2:
                    await asyncio.sleep(2)
                else:
                    raise
        
        # Надёжный клик по кнопке Live для фильтрации только живых матчей
        click_success = False
        for click_attempt in range(5):
            try:
                # Ждём видимость кнопки Live
                await main_page.wait_for_selector("#li_FilterLive", timeout=5000)
                
                # Проверяем, активна ли уже кнопка Live
                is_active = await main_page.evaluate("""
                    () => {
                        const elem = document.querySelector('#li_FilterLive');
                        return elem && elem.classList.contains('on');
                    }
                """)
                
                if is_active:
                    click_success = True
                    break
                
                # Пытаемся кликнуть
                await main_page.click("#li_FilterLive", force=True)
                await asyncio.sleep(5)
                
                # Проверяем что Live теперь активна
                is_now_active = await main_page.evaluate("""
                    () => {
                        const elem = document.querySelector('#li_FilterLive');
                        return elem && elem.classList.contains('on');
                    }
                """)
                
                if is_now_active:
                    click_success = True
                    break
                else:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                if click_attempt < 4:
                    await asyncio.sleep(2)
                else:
                    print(f"[ERROR] Не удалось активировать Live фильтр: {e}")
                    return
        
        if not click_success:
            print("[ERROR] Live фильтр не активирован после всех попыток")
            return
        
        print("PARSING STARTED")
        
        # Выбираем Crown в dropdown CompanySel и дожидаемся обновления данных
        try:
            # Ждём видимость dropdown
            await main_page.wait_for_selector("#CompanySel", timeout=10000)

            # Используем select_option для выбора значения (правильный способ для select элементов)
            await main_page.select_option("#CompanySel", value="3")

            # Ждём, что селект окончательно установится на Crown
            await main_page.wait_for_function(
                "() => { const select = document.querySelector('#CompanySel'); return select && select.value === '3'; }",
                timeout=5000,
            )

            # Снимок текущего состояния таблицы до обновления
            previous_rows = await main_page.evaluate(
                "() => Array.from(document.querySelectorAll('table.tbl_max tbody tr.tds')).map(row => row.innerText.trim()).join('||')"
            )

            # Ждём обновления данных таблицы после смены конторы
            try:
                await main_page.wait_for_function(
                    "prev => { const rows = Array.from(document.querySelectorAll('table.tbl_max tbody tr.tds')); const snapshot = rows.map(row => row.innerText.trim()).join('||'); return snapshot !== prev; }",
                    previous_rows,
                    timeout=15000,
                )
            except Exception:
                await asyncio.sleep(3)

            print("[INFO] ✓ Crown выбран в CompanySelect и данные обновились")
        except Exception as e:
            print(f"[WARNING] Не удалось выбрать Crown: {e}")

        matches = []
        # Собираем ID матчей только из Live таблицы - используем JavaScript для надежности
        try:
            # Используем JS для поиска - это надежнее чем селекторы
            matches = await main_page.evaluate("""
                () => {
                    const matches = [];
                    // Ищем все элементы с id^="time_"
                    const timeElements = document.querySelectorAll('[id^="time_"]');
                    
                    timeElements.forEach(elem => {
                        // Проверяем что элемент видимый и в Live таблице
                        const isVisible = elem.offsetParent !== null;
                        if (isVisible) {
                            const matchId = elem.id.replace('time_', '');
                            if (matchId && !matches.includes(matchId)) {
                                // Получаем строку таблицы (tr) этого матча
                                const row = elem.closest('tr');
                                if (row) {
                                    // Ищем в строке элемент odds с классом odds1 или odds2
                                    const hasOdds = row.querySelector('p.odds1, p.odds2') !== null;
                                    if (hasOdds) {
                                        matches.push(matchId);
                                    }
                                }
                            }
                        }
                    });
                    
                    return matches;
                }
            """)
            
        except Exception as e:
            # Fallback: старый способ через query_selector_all
            try:
                rows = await main_page.query_selector_all('table.tbl_max tbody tr.tds')
                
                for row in rows:
                    try:
                        # Ищем элемент времени матча с id="time_*"
                        time_element = await row.query_selector('td.status.handpoint[id^="time_"]')
                        if time_element:
                            match_id_attr = await time_element.get_attribute('id')
                            if match_id_attr and 'time_' in match_id_attr:
                                match_id = match_id_attr.replace('time_', '')
                                if match_id and match_id not in matches:
                                    # Проверяем наличие odds в строке
                                    odds_element = await row.query_selector('p.odds1, p.odds2')
                                    if odds_element:
                                        matches.append(match_id)
                    except Exception:
                        continue
            except Exception as e2:
                pass

        # Fallback: если первый способ не сработал, ищем через JS с фильтром odds
        if not matches:
            try:
                # Используем JavaScript как fallback с фильтром по odds
                matches = await main_page.evaluate("""
                    () => {
                        const matches = [];
                        const rows = document.querySelectorAll('table.tbl_max tbody tr.tds');
                        
                        rows.forEach(row => {
                            const timeElement = row.querySelector('td.status.handpoint[id^="time_"]');
                            if (timeElement) {
                                const matchId = timeElement.id.replace('time_', '');
                                // Проверяем наличие odds в строке
                                const hasOdds = row.querySelector('p.odds1, p.odds2') !== null;
                                if (matchId && hasOdds && !matches.includes(matchId)) {
                                    matches.push(matchId);
                                }
                            }
                        });
                        
                        return matches;
                    }
                """)
            except Exception as e:
                print(f"[ERROR] Fallback поиск не сработал: {e}")

        if not matches:
            print("[ERROR] Матчи не найдены.")
            return

        print(f"FOUND {len(matches)}")

        # Создаём ОЧЕРЕДЬ для обработки матчей вместо цикличного распределения
        # Это гарантирует, что одна страница обрабатывает один матч за раз
        match_queue = asyncio.Queue()
        for match_id in matches:
            await match_queue.put(match_id)
        
        async def worker(page_idx):
            """Рабочий процесс для парсинга матчей из очереди"""
            page = worker_pages[page_idx]
            while True:
                try:
                    # Получаем матч из очереди (non-blocking)
                    match_id = match_queue.get_nowait()
                except asyncio.QueueEmpty:
                    # Очередь пуста, рабочий завершает работу
                    break
                
                try:
                    # Парсим матч (только один матч на одной странице одновременно)
                    await parse_match(page, match_id)
                except Exception as e:
                    print(f"[ERROR] Worker error for match {match_id}: {e}")
                finally:
                    # Сигнализируем, что задача завершена
                    match_queue.task_done()
        
        # Запускаем рабочих (по числу страниц)
        workers = []
        for page_idx in range(len(worker_pages)):
            task = asyncio.create_task(worker(page_idx))
            workers.append(task)
        
        # Ждём, пока все задачи в очереди будут обработаны
        await match_queue.join()
        
        # Отменяем рабочие задачи (они уже вышли из цикла)
        for task in workers:
            if not task.done():
                task.cancel()
        
        # Ждём завершения всех рабочих
        await asyncio.gather(*workers, return_exceptions=True)

    except Exception as e:
        print(f"[ERROR] Ошибка при сборе матчей: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем браузер
        await cleanup_browser()

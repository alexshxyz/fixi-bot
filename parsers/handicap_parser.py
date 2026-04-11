"""
Парсинг Asian Handicap коэффициентов из таблицы #ahdetail.
"""
import re
from playwright.async_api import Page
from .helpers import has_red


async def parse_asian_handicap(page: Page, key: str, is_half_time: bool, ah_meta: dict, rate_value: float, actual_tab_label: str = None):
    """
    Парсит Asian Handicap из таблицы #ahdetail.
    
    Коэффициент: ПЕРВЫЙ span[data-o] если main_val > 0, ТРЕТИЙ span[data-o] если main_val < 0
    Исход: ТРЕТИЙ span[data-o] если main_val < 0
    
    Args:
        page: Playwright Page объект
        key: 'half' или 'full'
        is_half_time: bool - True для HT (первый тайм), False для FT (полный матч)
        ah_meta: dict для сохранения метаданных handicap
        rate_value: максимальное значение коэффициента для фильтрации
        actual_tab_label: 'HT' или 'FT' если доступно из UI
    """
    try:
        if actual_tab_label in ('HT', 'FT'):
            ah_meta[key]['tab'] = actual_tab_label
        else:
            ah_meta[key]['tab'] = "HT" if is_half_time else "FT"
        
        # Ищем таблицу #ahdetail
        try:
            ah_table = await page.query_selector('#ahdetail')
            if not ah_table:
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                ah_meta[key]['red'] = False
                return
        except Exception as e:
            pass
            ah_meta[key]['val'] = None
            ah_meta[key]['ok'] = False
            ah_meta[key]['red'] = False
            return

        # Ищем первую строку с <td> элементами для проверки красности
        try:
            ah_rows = await ah_table.query_selector_all('tr')
            data_row = None
            for r in ah_rows:
                try:
                    tds = await r.query_selector_all('td')
                    if tds:
                        data_row = r
                        break
                except Exception:
                    continue
        except Exception as e:
            data_row = None
        
        # Проверяем красность
        if data_row:
            try:
                data_row_html = await data_row.inner_html()
                is_red = has_red(data_row_html)
                ah_meta[key]['red'] = is_red
            except Exception:
                ah_meta[key]['red'] = False
        else:
            ah_meta[key]['red'] = False

        # Проверяем наличие "No Data!" в таблице AH - пропускаем эту половину
        try:
            ah_table_html = await ah_table.inner_html()
            if 'nodata' in ah_table_html.lower() or 'no data' in ah_table_html.lower():
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                return
        except Exception:
            pass

        # Ищем ВСЕ span[data-o] в таблице #ahdetail
        try:
            all_spans = await ah_table.query_selector_all('span[data-o]')
            
            if len(all_spans) < 2:
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                return
            
            # ИСХОД из ВТОРОГО span[data-o] (например 0/0.5)
            second_span = all_spans[1]
            # Берем ТЕКСТОВОЕ содержимое для вычисления main_val, не data-o!
            raw_outcome = await second_span.text_content() or ""
            raw_outcome = (raw_outcome or "").strip()
            ah_meta[key]['handicap_text'] = raw_outcome
            ah_meta[key]['span_main_raw'] = raw_outcome
            
            # Вычисляем main_val из исхода
            main_val = None
            try:
                if '/' in raw_outcome:
                    left_s, right_s = [p.strip() for p in raw_outcome.split('/', 1)]
                    
                    def to_float(s):
                        try:
                            return float(s)
                        except Exception:
                            m = re.search(r'[-+]?\d+(?:[.,]\d+)?', s)
                            if m:
                                return float(m.group(0).replace(',', '.'))
                            return None
                    
                    l = to_float(left_s)
                    r = to_float(right_s)
                    if l is not None and r not in (None, 0):
                        main_val = l / r
                else:
                    main_val = float(raw_outcome.replace(',', '.'))
            except Exception as e:
                main_val = None
            
            ah_meta[key]['main_val'] = main_val
            
            # Пропускаем ТОЛЬКО нулевую фору (0/0), но НЕ фору вроде 0/-0.5!
            # raw_outcome содержит исходное значение для проверки
            if main_val is None or (main_val == 0 and raw_outcome == '0'):
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                return
            
            # КОЭФФИЦИЕНТ в зависимости от исходного знака форы
            # Если в raw_outcome есть "-" → ОТРИЦАТЕЛЬНАЯ фора → беру ТРЕТИЙ span[data-o] (индекс 2)
            # Если в raw_outcome нет "-" → ПОЛОЖИТЕЛЬНАЯ фора → беру ПЕРВЫЙ span[data-o] (индекс 0)
            # ВАЖНО: используем raw_outcome, потому что main_val может быть -0.0 что == 0 в Python
            coeff_index = 2 if '-' in raw_outcome else 0
            
            if len(all_spans) <= coeff_index:
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                return
            
            chosen_span = all_spans[coeff_index]
            raw_coeff = await chosen_span.get_attribute('data-o') or ""
            raw_coeff = (raw_coeff or "").strip().replace(',', '.')
            
            if not raw_coeff:
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                return
            
            try:
                found_val = float(raw_coeff)
            except ValueError:
                ah_meta[key]['val'] = None
                ah_meta[key]['ok'] = False
                return
            
            ah_meta[key]['val'] = found_val
            ah_meta[key]['ok'] = (found_val is not None and float(found_val) <= float(rate_value) and ah_meta[key]['red'])
        
        except Exception as e:
            ah_meta[key]['val'] = None
            ah_meta[key]['ok'] = False
        
    except Exception as e:
        ah_meta[key]['val'] = None
        ah_meta[key]['ok'] = False
        ah_meta[key]['red'] = ah_meta[key].get('red', False)

"""
Парсинг Over/Under коэффициентов из таблицы #oudetail.
"""
from playwright.async_api import Page
from .helpers import has_red


async def parse_over_odds(page: Page, match_id: str, key: str, is_half_time: bool, over_values: dict, over_meta: dict):
    """
    Парсит Over коэффициенты для заданной половины матча из таблицы #oudetail.
    
    Коэффициент: ПЕРВЫЙ span[data-o]
    Исход: ВТОРОЙ span[data-o]
    
    Args:
        page: Playwright Page объект
        match_id: ID матча (для логирования)
        key: 'half' или 'full'
        is_half_time: bool - True для HT (первый тайм), False для FT (полный матч)
        over_values: dict для сохранения значений коэффициентов
        over_meta: dict для сохранения метаданных
    """
    try:
        # Ищем таблицу #oudetail
        try:
            table = await page.query_selector('#oudetail')
            if not table:
                over_values[key] = None
                over_meta[key]['over'] = None
                return
        except Exception as e:
            pass
            over_values[key] = None
            over_meta[key]['over'] = None
            return
        
        # Ищем ВСЕ span[data-o] в таблице
        try:
            all_spans = await table.query_selector_all('span[data-o]')
            
            if len(all_spans) < 1:
                over_values[key] = None
                over_meta[key]['over'] = None
                return
            
            # КОЭФФИЦИЕНТ из ПЕРВОГО span[data-o]
            first_span = all_spans[0]
            raw_coeff = await first_span.get_attribute('data-o') or ""
            raw_coeff = (raw_coeff or "").strip().replace(',', '.')
            
            if not raw_coeff:
                over_values[key] = None
                over_meta[key]['over'] = None
                return
            
            # Парсим коэффициент
            try:
                val = float(raw_coeff)
                over_values[key] = val
                over_meta[key]['over'] = val
            except ValueError:
                part = raw_coeff.split('/')[0].strip() if '/' in raw_coeff else raw_coeff
                try:
                    val = float(part)
                    over_values[key] = val
                    over_meta[key]['over'] = val
                except ValueError:
                    over_values[key] = None
                    over_meta[key]['over'] = None
                    return
            
            # ИСХОД из ВТОРОГО span[data-o]
            goals_text = ""
            if len(all_spans) >= 2:
                second_span = all_spans[1]
                # Берем ТЕКСТОВОЕ содержимое, не data-o атрибут!
                goals_raw = await second_span.text_content() or ""
                goals_text = (goals_raw or "").strip()
            else:
                goals_text = ""
            
            over_meta[key]['goals'] = goals_text or ""
        
        except Exception as e:
            over_values[key] = None
            over_meta[key]['over'] = None
            return

        # Определяем tab на основе параметра is_half_time (детерминированно, без ненадёжного UI селектора)
        over_meta[key]['tab'] = "HT" if is_half_time else "FT"
        
        # Проверяем красный ли коэффициент (первая строка с данными)
        try:
            rows = await table.query_selector_all('tr')
            data_row = None
            for row in rows:
                tds = await row.query_selector_all('td')
                if tds:
                    data_row = row
                    break
            
            if data_row:
                data_row_html = await data_row.inner_html()
                is_red = has_red(data_row_html)
                over_meta[key]['red'] = is_red
            else:
                over_meta[key]['red'] = False
        except Exception as e:
            pass
            over_meta[key]['red'] = False
        
    except Exception as e:
        over_values[key] = None
        over_meta[key]['over'] = None

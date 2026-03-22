"""
Функции для извлечения данных из страницы матча.
Получение имён команд, счётов, и другой информации.
"""
import asyncio
import re
from playwright.async_api import Page
from .helpers import sanitize_team_name


async def fetch_teams_and_scores(page: Page, wait_seconds: int = 5):
    """
    Надёжное получение имён команд и счётов с ЯВНЫМ ОЖИДАНИЕМ каждого элемента.
    
    Ждет явного появления:
    1. h1 элемента с именами команд (до wait_seconds)
    2. .score элементов со счетом (до wait_seconds)
    
    Args:
        page: Playwright Page объект
        wait_seconds: максимальное время ожидания каждого элемента
        
    Returns:
        tuple: (first_team, second_team, first_score, second_score)
    """
    first_team = second_team = first_score = second_score = ""

    # 1) ЯВНОЕ ОЖИДАНИЕ h1 - ждем его появления
    print(f"[FETCH_TEAMS] ⏳ Ожидаю h1 элемент (до {wait_seconds}сек)...")
    try:
        await page.wait_for_selector('h1', timeout=wait_seconds * 1000)
        h1_text = await page.text_content('h1')
        if h1_text:
            h = h1_text.strip()
            print(f"[FETCH_TEAMS] ✓ H1 найден: '{h}'")
            if h:
                m = re.search(r'(.+?)\s+[–—-]\s+(.+)', h) or \
                    re.search(r'(.+?)\s+v(?:s)?\.?\s+(.+)', h, re.I) or \
                    re.search(r'(.+?)\s+vs\.?\s+(.+)', h, re.I)
                if m:
                    left, right = m.group(1).strip(), m.group(2).strip()
                    if left:
                        first_team = left
                    if right:
                        second_team = right
                    print(f"[FETCH_TEAMS] ✓ Команды из H1: '{first_team}' vs '{second_team}'")
    except Exception as e:
        print(f"[FETCH_TEAMS] ⚠ H1 не найден или ошибка: {str(e)[:60]}")
        pass

    # 2) ЯВНОЕ ОЖИДАНИЕ счёта в .score элементах
    print(f"[FETCH_TEAMS] ⏳ Ожидаю .score элементы (до {wait_seconds}сек)...")
    try:
        # Ждем появления хотя бы 2 элементов со счетом
        score_retries = 3
        for attempt in range(score_retries):
            try:
                # Проверяем наличие .score элементов
                score_elements = await page.query_selector_all('.score')
                
                if len(score_elements) >= 2:
                    scores = []
                    for elem in score_elements:
                        text = await elem.text_content()
                        if text:
                            text = text.strip()
                            if text:
                                scores.append(text)
                    
                    if len(scores) >= 2:
                        first_score, second_score = scores[0], scores[1]
                        print(f"[FETCH_TEAMS] ✓ Счет получен (попытка {attempt+1}): '{first_score}' - '{second_score}'")
                        break
                    else:
                        print(f"[FETCH_TEAMS] ⚠ .score найдены но содержимое пусто (попытка {attempt+1})")
                else:
                    print(f"[FETCH_TEAMS] ⚠ Найдено {len(score_elements)} .score элементов, нужно минимум 2 (попытка {attempt+1})")
                
                if attempt < score_retries - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                print(f"[FETCH_TEAMS] ⚠ Ошибка получения .score (попытка {attempt+1}): {str(e)[:50]}")
                if attempt < score_retries - 1:
                    await asyncio.sleep(0.5)
                    
    except Exception as e:
        print(f"[FETCH_TEAMS] ⚠ Score error: {e}")
        pass

    # 3) Если команды не получены из h1 - пробуем .sclassName
    if not first_team or not second_team:
        print(f"[FETCH_TEAMS] ⚠ Команды из h1 не получены, пробую .sclassName...")
        try:
            end_time = asyncio.get_event_loop().time() + wait_seconds
            while asyncio.get_event_loop().time() < end_time:
                try:
                    elems = await page.query_selector_all('.sclassName')
                    texts = []
                    for elem in elems:
                        text = await elem.text_content()
                        if text:
                            text = text.strip()
                            if text:
                                texts.append(text)
                    if len(texts) >= 2:
                        if not first_team:
                            first_team = texts[0]
                        if not second_team:
                            second_team = texts[1]
                        print(f"[FETCH_TEAMS] ✓ Команды из .sclassName: '{first_team}' vs '{second_team}'")
                        break
                    elif len(texts) == 1:
                        if not first_team:
                            first_team = texts[0]
                except Exception as e:
                    print(f"[FETCH_TEAMS] ⚠ sclassName error: {e}")
                    pass
                await asyncio.sleep(0.12)
        except Exception as e:
            print(f"[FETCH_TEAMS] ⚠ sclassName loop error: {e}")
            pass

    # Финальная очистка
    first_team = sanitize_team_name(first_team or "")
    second_team = sanitize_team_name(second_team or "")
    first_score = (first_score or "").strip()
    second_score = (second_score or "").strip()
    print(f"[FETCH_TEAMS] ✅ Финал: '{first_team}' {first_score} - {second_score} '{second_team}'")
    return first_team, second_team, first_score, second_score

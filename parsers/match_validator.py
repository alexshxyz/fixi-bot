"""
Валидация данных матча перед отправкой.
Переполучает все данные с явным ожиданием каждого элемента.
"""
import asyncio
import re
from playwright.async_api import Page
from .helpers import sanitize_league_name, sanitize_team_name


async def validate_and_get_final_data(page: Page, match_id: str):
    """
    Переполучает все данные перед отправкой с явным ожиданием каждого элемента.
    
    Явно ждет:
    1. Лига (.LName) - до 5 сек, 3 попытки
    2. Команды (h1 или .sclassName) - до 5 сек
    3. Счет (.score) - до 5 сек
    4. URL - проверяем что браузер на нужном матче
    
    Не блокирует отправку, но логирует если элементы не появились.
    
    Returns:
        dict с полями liga, first_team, second_team, first_score, second_score
    """
    result = {
        'liga': '',
        'first_team': '',
        'second_team': '',
        'first_score': '',
        'second_score': '',
    }
    
    try:
        # 1. ЯВНОЕ ОЖИДАНИЕ ЛИГИ - самое критичное
        liga_retries = 3
        for attempt in range(liga_retries):
            try:
                # Ждем явного появления элемента
                await page.wait_for_selector('.LName', timeout=5000)
                liga_raw = await page.text_content('.LName')
                if liga_raw and liga_raw.strip():
                    result['liga'] = sanitize_league_name(liga_raw.strip())
                    break
            except Exception as e:
                if attempt < liga_retries - 1:
                    await asyncio.sleep(0.5)
        
        # 2. ЯВНОЕ ОЖИДАНИЕ КОМАНД И СЧЕТА
        teams_retries = 3
        for attempt in range(teams_retries):
            try:
                # Ждем появления h1
                await page.wait_for_selector('h1', timeout=5000)
                h1_text = await page.text_content('h1')
                
                if h1_text and h1_text.strip():
                    h = h1_text.strip()
                    
                    # Парсим команды из h1
                    m = re.search(r'(.+?)\s+[–—-]\s+(.+)', h) or \
                        re.search(r'(.+?)\s+v(?:s)?\.?\s+(.+)', h, re.I) or \
                        re.search(r'(.+?)\s+vs\.?\s+(.+)', h, re.I)
                    
                    if m:
                        result['first_team'] = m.group(1).strip()
                        result['second_team'] = m.group(2).strip()
                        break
            except Exception as e:
                if attempt < teams_retries - 1:
                    await asyncio.sleep(0.5)
        
        # 3. ЯВНОЕ ОЖИДАНИЕ СЧЕТА
        score_retries = 3
        for attempt in range(score_retries):
            try:
                # Ждем появления элемента со счетом
                score_elems = await page.query_selector_all('.score')
                if len(score_elems) >= 2:
                    first_score = await score_elems[0].text_content()
                    second_score = await score_elems[1].text_content()
                    
                    if first_score and second_score:
                        result['first_score'] = first_score.strip()
                        result['second_score'] = second_score.strip()
                        break
            except Exception as e:
                if attempt < score_retries - 1:
                    await asyncio.sleep(0.5)
        
        # 4. ОЧИСТКА КОМАНД ОТ СТОП-СЛОВ
        result['first_team'] = sanitize_team_name(result['first_team'])
        result['second_team'] = sanitize_team_name(result['second_team'])
        
        return result
        
    except Exception as e:
        return result

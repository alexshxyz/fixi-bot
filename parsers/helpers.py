"""
Вспомогательные функции для парсера.
Проверка наличия цветов в элементах и санитизация текста.
"""
import re


def has_red(html_content: str) -> bool:
    """
    Проверяет, используется ли красный цвет в HTML контенте.
    
    Args:
        html_content: HTML строка или текстовое содержимое элемента
        
    Returns:
        bool: True если найден красный цвет
    """
    try:
        if isinstance(html_content, str):
            content_lower = html_content.lower()
            
            # Проверяем различные варианты красного цвета
            if 'class="red"' in content_lower:
                return True
            if "class='red'" in content_lower:
                return True
            if 'class="red ' in content_lower:
                return True
            if ' red"' in content_lower:
                return True
            if 'color:red' in content_lower.replace(' ', ''):
                return True
            if 'color: red' in content_lower.replace(' ', ''):
                return True
            if '#ff0000' in content_lower or 'ff0000' in content_lower:
                return True
            if 'rgb(255,0,0)' in content_lower.replace(' ', ''):
                return True
            
            # Более мягкая проверка
            if 'red' in content_lower and '<span' in content_lower:
                return True
    except Exception:
        pass
    return False


def has_black(html_content: str) -> bool:
    """
    Проверяет, используется ли чёрный цвет (#222) в HTML контенте.
    Если чёрный цвет присутствует — коэффициенты считаются ненадёжными.
    
    Args:
        html_content: HTML строка или текстовое содержимое элемента
        
    Returns:
        bool: True если найден чёрный цвет
    """
    try:
        if isinstance(html_content, str):
            content_lower = html_content.lower()
            content_compact = content_lower.replace(' ', '')
            
            # Проверяем различные варианты чёрного цвета
            if '#222' in content_compact:
                return True
            if 'color:#222' in content_compact:
                return True
            if 'rgb(34,34,34' in content_compact:
                return True
            if 'rgba(34,34,34' in content_compact:
                return True
    except Exception:
        pass
    return False


def sanitize_team_name(s: str) -> str:
    """Очищает имя команды от стоп-слов вроде 'Live Score and Analysis'"""
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r'\s*(-\s*)?Live\s*Score(?:\s*(?:and|&)\s*Analysis)?\s*$', '', s, flags=re.I).strip()
    s = re.sub(r'\s*Live\s*Score(?:\s*(?:and|&)\s*Analysis)?\s*$', '', s, flags=re.I).strip()
    return s


def sanitize_league_name(s: str) -> str:
    """Очищает имя лиги, оставляя только часть до точки-разделителя"""
    if not s:
        return ""
    parts = s.split('·', 1)
    return parts[0].strip()

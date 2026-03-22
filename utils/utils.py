"""
Вспомогательные функции для обработки текста и кодировок.
"""
import re


def strip_html_tags(text):
    """
    Убирает HTML-теги из строки.
    
    Args:
        text: строка с потенциальными HTML-тегами
        
    Returns:
        Очищенная строка без тегов
    """
    if not text:
        return text
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def ensure_text(val):
    """
    Преобразует значение в строку или None.
    Обрабатывает различные кодировки (UTF-8, CP1251, Latin-1).
    
    Args:
        val: значение любого типа
        
    Returns:
        str или None
        
    Logic:
        - Если val is None -> None
        - Если уже str -> возвращает как есть
        - Если bytes -> пытается декодировать UTF-8, затем CP1251, затем Latin-1
        - Для других типов делает str(val)
    """
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, bytes):
        try:
            return val.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return val.decode('cp1251')
            except UnicodeDecodeError:
                try:
                    return val.decode('latin-1')
                except UnicodeDecodeError:
                    return val.decode('utf-8', errors='replace')
    try:
        return str(val)
    except Exception:
        return repr(val)

#!/usr/bin/env python3
"""
Диагностический скрипт для проверки почему не работает проверка дубликатов.
Запустите этот скрипт перед тем как запускать бота.
"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from utils.utils import strip_html_tags

print("\n" + "=" * 80)
print("ДИАГНОСТИКА ПРОВЕРКИ ДУБЛИКАТОВ")
print("=" * 80)

# Тест 1: Проверяем функцию strip_html_tags
print("\n[TEST 1] Тестирование strip_html_tags():\n")

test_cases = [
    "<b>Over 2.5 HT</b>",
    "Over 2.5 FT",
    "<b>Handicap</b> -0/0.5 Home Team",
    "<b>Crown</b>, Liverpool vs Man Utd, 2-1, <b>Over 2.5 HT</b>",
]

for test_input in test_cases:
    result = strip_html_tags(test_input)
    print(f"  Input:  '{test_input}'")
    print(f"  Output: '{result}'")
    print()

# Тест 2: Попытка подключиться к БД и проверить что там есть
print("\n[TEST 2] Проверка доступности БД:\n")

try:
    from database.database import check_match_exists, get_match_from_db
    from core.config import TABLE_NAME
    import psycopg2
    from core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
    
    print(f"  Конфиг БД:")
    print(f"    - HOST: {DB_HOST}")
    print(f"    - PORT: {DB_PORT}")
    print(f"    - DB: {DB_NAME}")
    print(f"    - TABLE: {TABLE_NAME}")
    
    # Пытаемся подключиться
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    
    # Получаем статистику
    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total_count = cur.fetchone()[0]
    print(f"  ✅ Успешно подключено!")
    print(f"  Всего записей в таблице: {total_count}")
    
    # Показываем последние 5 записей
    cur.execute(f"""
        SELECT id, link, prediction FROM {TABLE_NAME} 
        ORDER BY id DESC LIMIT 5
    """)
    last_records = cur.fetchall()
    
    if last_records:
        print(f"\n  Последние 5 записей:")
        for record_id, link, pred in last_records:
            print(f"    ID {record_id}:")
            print(f"      Link: {link}")
            print(f"      Prediction: '{pred}'")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"  ❌ Ошибка подключения: {e}")
    import traceback
    traceback.print_exc()

# Тест 3: Пример логики парсинга
print("\n[TEST 3] Пример логики парсинга prediction из сообщения:\n")

# Симулируем сообщение как его генерирует Match.__str__()
example_message = """<b>Crown</b>
Liverpool vs Manchester United
<b>2 - 1</b>
<b>Over 2.5 HT</b>
Odds 1.5"""

lines = example_message.splitlines()
prediction_from_msg = lines[3] if len(lines) > 3 else ""
print(f"  Сообщение (lines[3]): '{prediction_from_msg}'")

cleaned_pred = strip_html_tags(prediction_from_msg)
print(f"  После strip_html_tags: '{cleaned_pred}'")

print("\n" + "=" * 80)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 80)
print("\n💡 Советы:")
print("  1. Запустите этот скрипт и проверьте вывод")
print("  2. Используйте debug_duplicates.py для интерактивной проверки")
print("  3. Проверьте логи при запуске бота - там будут [DB DEBUG] сообщения")
print()

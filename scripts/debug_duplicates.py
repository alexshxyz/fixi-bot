"""
Скрипт отладки для проверки данных в БД.
Помогает найти причину, почему не работает проверка дубликатов.
"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from database.database import check_match_exists, get_match_from_db
import psycopg2
from core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, TABLE_NAME

print("=" * 80)
print("СКРИПТ ОТЛАДКИ: Проверка дубликатов в БД")
print("=" * 80)

# Подключаемся к БД и получаем последние добавленные матчи
try:
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    
    # Получаем последние 10 записей
    print(f"\n[INFO] Последние 10 записей из таблицы '{TABLE_NAME}':\n")
    cur.execute(f"""
        SELECT link, prediction FROM {TABLE_NAME} 
        ORDER BY id DESC LIMIT 10
    """)
    
    results = cur.fetchall()
    
    if not results:
        print("❌ В таблице нет записей!")
    else:
        for i, (link, prediction) in enumerate(results, 1):
            print(f"{i}. Link: {link}")
            print(f"   Prediction: {prediction}")
            print()
    
    cur.close()
    
    # Интерактивная проверка
    print("\n" + "=" * 80)
    print("ИНТЕРАКТИВНАЯ ПРОВЕРКА")
    print("=" * 80)
    
    while True:
        print("\nВведите URL матча для проверки (или 'exit' для выхода):")
        url = input("URL: ").strip()
        
        if url.lower() == 'exit':
            break
        
        if not url:
            print("❌ URL не может быть пустым!")
            continue
        
        print(f"\n📋 Проверяю {url}...")
        
        # Показываем что в БД
        results = get_match_from_db(url)
        
        # Готовим prediction для теста (пользователь может ввести)
        print("\nВведите prediction для проверки (или просто нажмите Enter чтобы пропустить):")
        prediction = input("Prediction: ").strip()
        
        if prediction:
            print(f"\n🔍 Проверяю комбинацию link + prediction...")
            exists = check_match_exists(url, prediction=prediction)
            if exists:
                print(f"✅ НАЙДЕНО! Матч с таким прогнозом уже в БД")
            else:
                print(f"✅ НЕ НАЙДЕНО! Матч можно отправлять")
        else:
            print(f"\n🔍 Проверяю только по link...")
            exists = check_match_exists(url)
            if exists:
                print(f"✅ НАЙДЕНО! Матч уже есть в БД")
            else:
                print(f"✅ НЕ НАЙДЕНО! Матч можно отправлять")
    
    conn.close()
    
except Exception as e:
    print(f"\n❌ Ошибка подключения к БД: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("Отладка завершена")
print("=" * 80)

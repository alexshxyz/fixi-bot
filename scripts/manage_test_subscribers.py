"""
Скрипт для управления тестовыми подписчиками во время разработки.
Позволяет быстро добавлять/удалять chat_id без редактирования JSON файла вручную.
"""
import json
import sys
from pathlib import Path

# Получаем путь к файлу подписчиков
SUBSCRIBERS_FILE = Path(__file__).parent.parent / 'subscribers.json'


def load_subscribers():
    """Загружает список оборотных подписчиков"""
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('subscribers', [])
    except:
        return []


def save_subscribers(subscribers):
    """Сохраняет список подписчиков"""
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump({'subscribers': subscribers}, f)
    print(f"✅ Сохранено {len(subscribers)} подписчиков")


def add_subscriber(chat_id):
    """Добавляет подписчика"""
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        print(f"✅ Подписчик {chat_id} добавлен")
    else:
        print(f"⚠️  Подписчик {chat_id} уже в списке")


def remove_subscriber(chat_id):
    """Удаляет подписчика"""
    subscribers = load_subscribers()
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        print(f"✅ Подписчик {chat_id} удален")
    else:
        print(f"⚠️  Подписчик {chat_id} не найден")


def list_subscribers():
    """Выводит список подписчиков"""
    subscribers = load_subscribers()
    if subscribers:
        print(f"\n📋 Текущие тестовые подписчики ({len(subscribers)} шт):")
        for sub in subscribers:
            print(f"  - {sub}")
    else:
        print("\n📭 Список подписчиков пуст")


def clear_all():
    """Очищает все подписчики"""
    save_subscribers([])
    print("✅ Все подписчики удалены")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python manage_test_subscribers.py add <chat_id>")
        print("  python manage_test_subscribers.py remove <chat_id>")
        print("  python manage_test_subscribers.py list")
        print("  python manage_test_subscribers.py clear")
        print("\nПример:")
        print("  python manage_test_subscribers.py add 299338754")
        sys.exit(1)

    command = sys.argv[1].lower()
    
    if command == 'add' and len(sys.argv) == 3:
        try:
            add_subscriber(int(sys.argv[2]))
        except ValueError:
            print("❌ Chat ID должен быть числом")
    elif command == 'remove' and len(sys.argv) == 3:
        try:
            remove_subscriber(int(sys.argv[2]))
        except ValueError:
            print("❌ Chat ID должен быть числом")
    elif command == 'list':
        list_subscribers()
    elif command == 'clear':
        clear_all()
    else:
        print("❌ Неверная команда")

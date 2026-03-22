"""
Скрипт для отправки сообщения "Тест" всем подписчикам бота
"""
import sys
from pathlib import Path

# Добавляем текущую директорию в sys.path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from telegram.telegram_client import send_message_to_all


def main():
    """Отправляет сообщение всем подписчикам"""
    message = "Тест"
    print(f"[INFO] Начинаем отправку сообщения '{message}' всем подписчикам...")
    send_message_to_all(message)
    print("[INFO] Рассылка завершена!")


if __name__ == "__main__":
    main()

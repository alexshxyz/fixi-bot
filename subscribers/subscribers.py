"""
Управление подписчиками Telegram бота.
Загрузка, сохранение, добавление и удаление подписчиков из JSON файла.
"""
import os
import json
from core.config import USERS_FILE


def load_subscribers():
    """
    Загружает список подписчиков из JSON файла.
    
    Returns:
        set: множество chat_id подписчиков
    """
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('subscribers', []))
    except Exception as e:
        print(f"[SUBSCRIBERS] Ошибка при загрузке подписчиков: {e}")
    return set()


def save_subscribers(subscribers):
    """
    Сохраняет список подписчиков в JSON файл.
    
    Args:
        subscribers: множество chat_id для сохранения
    """
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump({'subscribers': list(subscribers)}, f)
    except Exception as e:
        print(f"[SUBSCRIBERS] Ошибка при сохранении подписчиков: {e}")


def add_subscriber(chat_id):
    """
    Добавляет нового подписчика.
    
    Args:
        chat_id: ID чата для добавления
    """
    subscribers = load_subscribers()
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    print(f"[SUBSCRIBERS] Добавлен подписчик: {chat_id}")


def remove_subscriber(chat_id):
    """
    Удаляет подписчика.
    
    Args:
        chat_id: ID чата для удаления
    """
    subscribers = load_subscribers()
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    print(f"[SUBSCRIBERS] Удалён подписчик: {chat_id}")

"""
Telegram клиент для отправки сообщений.
Низкоуровневые функции для коммуникации с Telegram API.
"""
import json
import requests
from core.config import BOT_TOKEN
from subscribers.subscribers import load_subscribers


def send_telegram_message(chat_id, text, reply_markup=None):
    """
    Отправляет сообщение конкретному пользователю.
    
    Args:
        chat_id: ID чата получателя
        text: текст сообщения (поддерживает HTML форматирование)
        reply_markup: клавиатура (словарь с keyboard)
        
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        
        response = requests.post(url, data=params, timeout=5)
        return response.json().get('ok', False)
    except Exception as e:
        print(f"[TELEGRAM] Ошибка при отправке: {e}")
        return False


def send_message_to_all(text):
    """
    Отправляет сообщение всем подписчикам.
    
    Каждый пользователь, когда написал /start в боте, будет получать это уведомление.
    
    Args:
        text: текст сообщения для рассылки
    """
    print(f"[TELEGRAM] Отправляю сообщение:\n{text}\n---")
    subscribers = load_subscribers()
    
    if not subscribers:
        print("[TELEGRAM] Нет подписчиков для отправки уведомлений")
        return
    
    for chat_id in subscribers:
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
            params = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            response = requests.post(url, data=params, timeout=5)
            result = response.json()
            if result.get('ok'):
                print(f"[TELEGRAM] Сообщение отправлено пользователю {chat_id}")
            else:
                print(f"[TELEGRAM] Ошибка отправки пользователю {chat_id}: {result.get('description')}")
        except Exception as e:
            print(f"[TELEGRAM] Ошибка при отправке пользователю {chat_id}: {e}")


def send_message(text):
    """
    УСТАРЕВШАЯ ФУНКЦИЯ (для обратной совместимости).
    Теперь используй send_message_to_all(text) для отправки всем подписчикам.
    
    Args:
        text: текст сообщения для рассылки
    """
    send_message_to_all(text)


def send_photo_to_chat(chat_id, photo_bytes, caption=None):
    """
    Отправляет фотографию конкретному пользователю.
    
    Args:
        chat_id: ID чата получателя
        photo_bytes: BytesIO объект с изображением
        caption: подпись к фото (опционально)
        
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
        files = {
            'photo': photo_bytes,
        }
        data = {
            'chat_id': chat_id,
        }
        if caption:
            data['caption'] = caption
            data['parse_mode'] = 'HTML'
        
        response = requests.post(url, data=data, files=files, timeout=10)
        return response.json().get('ok', False)
    except Exception as e:
        print(f"[TELEGRAM] Ошибка при отправке фото: {e}")
        return False

"""
Обработчик команд Telegram бота.
Polling и маршрутизация команд (/start, /stop, /help, /stats) и кнопок.
"""
import time
import requests
from core.config import BOT_TOKEN, BOT_POLLING_INTERVAL
from subscribers.subscribers import add_subscriber, remove_subscriber
from telegram.telegram_client import send_telegram_message, send_photo_to_chat
from telegram.keyboards import send_main_menu, show_menu_buttons, send_stats_submenu, show_stats_menu_buttons
from stats.stats import get_full_stats, get_top_leagues, get_worst_leagues, get_last_5_matches, get_profit_graph, get_this_month_stats, get_total_profit


# ============================================================================
# СОСТОЯНИЕ POLLING'А
# ============================================================================

last_update_id = None


# ============================================================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================================================

def _handle_start_command(chat_id, user_name):
    """Обрабатывает команду /start — подписка на уведомления."""
    add_subscriber(chat_id)
    send_main_menu(chat_id)
    print(f"[BOT] Пользователь {user_name} ({chat_id}) выполнил /start")


def _handle_stop_command(chat_id, user_name):
    """Обрабатывает команду /stop — отписка от уведомлений."""
    remove_subscriber(chat_id)
    goodbye_message = "Ты отписался от уведомлений. Если захочешь снова подписаться, напиши /start"
    send_telegram_message(chat_id, goodbye_message)
    print(f"[BOT] Пользователь {user_name} ({chat_id}) выполнил /stop")


def _handle_help_command(chat_id, user_name):
    """Обрабатывает команду /help — отправка справки."""
    help_text = (
        "❓ <b>Help:</b>\n\n"
        "▶️ Start - Notification On\n"
        "⏹️ Stop - Notification Off\n"
        "📊 Stats - View Statistics\n"
        "❓ Help - Help\n\n"
        "Bot is under development, documentation available at "
        "<a href='https://telegra.ph/Rukovodstvo-po-ispolzovaniyu-bota-03-12'>link</a> and will also be updated."
    )
    send_telegram_message(chat_id, help_text)
    print(f"[BOT] Пользователь {user_name} ({chat_id}) запросил /help")


def _handle_stats_command(chat_id, user_name):
    """Обрабатывает команду /stats — показ меню статистики."""
    send_stats_submenu(chat_id)
    print(f"[BOT] Пользователь {user_name} ({chat_id}) запросил /stats")


# ============================================================================
# ОБРАБОТЧИКИ КНОПОК МЕНЮ
# ============================================================================

def _handle_menu_button(chat_id):
    """Обрабатывает нажатие кнопки 🎲 Меню."""
    show_menu_buttons(chat_id)


def _handle_start_button(chat_id):
    """Обрабатывает нажатие кнопки ▶️ Start."""
    add_subscriber(chat_id)
    response_text = "✅ Notification On!"
    send_telegram_message(chat_id, response_text)


def _handle_stop_button(chat_id):
    """Обрабатывает нажатие кнопки ⏹️ Stop."""
    remove_subscriber(chat_id)
    response_text = "❌ Notification Off!"
    send_telegram_message(chat_id, response_text)


def _handle_stats_button(chat_id):
    """Обрабатывает нажатие кнопки 📊 Stats."""
    send_stats_submenu(chat_id)


def _handle_full_stats_button(chat_id):
    """Обрабатывает нажатие кнопки 📚 Summary."""
    stats_text = get_full_stats()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)
    
    # Отправляем график прибыли отдельно
    graph_image = get_profit_graph()
    if graph_image:
        profit_text = get_total_profit()
        send_photo_to_chat(chat_id, graph_image, caption=profit_text)


def _handle_last_5_button(chat_id):
    """Обрабатывает нажатие кнопки ⚡️ Last 5."""
    stats_text = get_last_5_matches()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_this_month_button(chat_id):
    """Обрабатывает нажатие кнопки 📅 This Month."""
    stats_text = get_this_month_stats()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_top_leagues_button(chat_id):
    """Обрабатывает нажатие кнопки 🏆 Top Leagues."""
    stats_text = get_top_leagues()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_worst_leagues_button(chat_id):
    """Обрабатывает нажатие кнопки 📉 Worst Leagues."""
    stats_text = get_worst_leagues()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_back_stats_button(chat_id):
    """Обрабатывает нажатие кнопки ↩️ Назад к статистике."""
    show_stats_menu_buttons(chat_id)


def _handle_back_menu_button(chat_id):
    """Обрабатывает нажатие кнопки ↩️ Назад в меню."""
    show_menu_buttons(chat_id)


def _handle_help_button(chat_id):
    """Обрабатывает нажатие кнопки ❓ Help."""
    help_text = (
        "❓ <b>Help:</b>\n\n"
        "▶️ Start - Notification On\n"
        "⏹️ Stop - Notification Off\n"
        "📊 Stats - View Statistics\n"
        "❓ Help - This Help\n\n"
        "Bot is under development, documentation available at "
        "<a href='https://telegra.ph/Rukovodstvo-po-ispolzovaniyu-bota-03-12'>link</a> and will be updated."
    )
    keyboard = {
        'keyboard': [
            [{'text': '🎲 Menu'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, help_text, reply_markup=keyboard)


def _handle_unknown_command(chat_id):
    """Обрабатывает неизвестную команду."""
    unknown_message = (
        "❓ Unknown command.\n\n"
        "Available commands:\n"
        "/start - Subscribe\n"
        "/stop - Unsubscribe\n"
        "/help - Help\n"
        "/stats - View Statistics\n\n"
        "Or use the 🎲 Menu button for navigation."
    )
    send_telegram_message(chat_id, unknown_message)


# ============================================================================
# МАРШРУТИЗАТОР КОМАНД
# ============================================================================

def _route_message(chat_id, user_name, text):
    """
    Маршрутизирует сообщение на соответствующий обработчик.
    
    Args:
        chat_id: ID чата
        user_name: имя пользователя
        text: текст сообщения
    """
    # Текстовые команды
    if text == '/start' or text.startswith('/start '):
        _handle_start_command(chat_id, user_name)
    elif text == '/stop' or text.startswith('/stop '):
        _handle_stop_command(chat_id, user_name)
    elif text == '/help' or text.startswith('/help '):
        _handle_help_command(chat_id, user_name)
    elif text == '/stats' or text.startswith('/stats '):
        _handle_stats_command(chat_id, user_name)
    
    # Кнопки меню
    elif text == '🎲 Menu':
        _handle_menu_button(chat_id)
    elif text == '▶️ Start':
        _handle_start_button(chat_id)
    elif text == '⏹️ Stop':
        _handle_stop_button(chat_id)
    elif text == '📊 Stats':
        _handle_stats_button(chat_id)
    
    # Кнопки статистики
    elif text == '📚 Summary':
        _handle_full_stats_button(chat_id)
    elif text == '⚡️ Last 5':
        _handle_last_5_button(chat_id)
    elif text == '📅 This Month':
        _handle_this_month_button(chat_id)
    elif text == '🏆 Top Leagues':
        _handle_top_leagues_button(chat_id)
    elif text == '⛔️ Worst Leagues':
        _handle_worst_leagues_button(chat_id)
    
    # Кнопки навигации
    elif text == '↩️ Back to Stats':
        _handle_back_stats_button(chat_id)
    elif text == '↩️ Back to Menu':
        _handle_back_menu_button(chat_id)
    elif text == '❓ Help':
        _handle_help_button(chat_id)
    
    # Неизвестная команда
    else:
        _handle_unknown_command(chat_id)


# ============================================================================
# POLLING ОБРАБОТЧИК
# ============================================================================

def handle_telegram_commands():
    """
    Обрабатывает команды и нажатия кнопок, отправленные боту (polling mode).
    
    Слушает:
    - Текстовые команды: /start, /stop, /help, /stats
    - Нажатия на кнопки меню и навигации
    
    Работает в бесконечном цикле с обработкой исключений.
    """
    global last_update_id
    
    while True:
        try:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
            params = {}
            if last_update_id:
                params['offset'] = last_update_id + 1
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if not data.get('ok'):
                time.sleep(BOT_POLLING_INTERVAL)
                continue
            
            updates = data.get('result', [])
            
            for update in updates:
                last_update_id = update.get('update_id')
                
                # Обрабатываем текстовые сообщения
                if 'message' in update:
                    message = update['message']
                    chat_id = message.get('chat', {}).get('id')
                    text = message.get('text', '').strip()
                    user_name = message.get('from', {}).get('first_name', 'User')
                    
                    if chat_id and text:
                        print(f"[BOT] Сообщение от {user_name} ({chat_id}): {text}")
                        _route_message(chat_id, user_name, text)
            
            time.sleep(BOT_POLLING_INTERVAL)
            
        except Exception as e:
            print(f"[BOT] Ошибка в polling'е команд: {e}")
            time.sleep(5)

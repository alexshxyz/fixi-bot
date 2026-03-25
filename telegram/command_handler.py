"""
Обработчик команд Telegram бота.
Polling и маршрутизация команд (/start, /stop, /help, /stats) и кнопок.
"""
import time
import requests
from core.config import BOT_TOKEN, BOT_POLLING_INTERVAL
from subscribers.subscribers import add_subscriber, remove_subscriber
from telegram.telegram_client import send_telegram_message, send_and_delete_message, send_photo_to_chat, delete_telegram_message
from telegram.keyboards import send_main_menu, show_menu_buttons, send_stats_submenu, show_stats_menu_buttons
from stats.stats import get_full_stats, get_top_leagues, get_worst_leagues, get_last_5_matches, get_profit_graph, get_this_month_stats, get_total_profit, get_match_details_by_id


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

def _handle_menu_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки 🎲 Меню."""
    # Удаляем сообщение пользователя (его нажатие кнопки)
    if message_id:
        delete_telegram_message(chat_id, message_id)
    # Отправляем главное меню с кнопками
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


def _handle_stats_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки 📊 Stats."""
    if message_id:
        delete_telegram_message(chat_id, message_id)
    send_stats_submenu(chat_id)


def _handle_full_stats_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки 📚 Summary."""
    stats_text = get_full_stats()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    
    # Удаляем предыдущее сообщение "Choose Statistics:"
    if message_id:
        delete_telegram_message(chat_id, message_id)
    
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)
    
    # Отправляем график прибыли отдельно
    graph_image = get_profit_graph()
    if graph_image:
        profit_text = get_total_profit()
        send_photo_to_chat(chat_id, graph_image, caption=profit_text)


def _handle_last_5_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки ⚡️ Last 5."""
    # Удаляем предыдущее сообщение "Choose Statistics:"
    if message_id:
        delete_telegram_message(chat_id, message_id)
    
    stats_text, matches_data = get_last_5_matches()
    
    # Создаем inline-кнопки для каждого матча с emoji результата
    inline_keyboard = []
    for match in matches_data:
        emoji = match.get('result_emoji', '?')
        button_text = f"{emoji} {match['home_team']} - {match['away_team']}"
        callback_data = f"match_{match['id']}"
        inline_keyboard.append([{'text': button_text, 'callback_data': callback_data}])
    
    # Добавляем кнопку закрытия
    inline_keyboard.append([{'text': 'Close', 'callback_data': 'close_last_5'}])
    
    keyboard = {
        'inline_keyboard': inline_keyboard
    }
    send_telegram_message(chat_id, "<b>⚡️ LAST 5</b>", reply_markup=keyboard)


def _handle_this_month_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки 📅 This Month."""
    # Удаляем предыдущее сообщение "Choose Statistics:"
    if message_id:
        delete_telegram_message(chat_id, message_id)
    
    stats_text = get_this_month_stats()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_top_leagues_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки 🏆 Top Leagues."""
    # Удаляем предыдущее сообщение "Choose Statistics:"
    if message_id:
        delete_telegram_message(chat_id, message_id)
    
    stats_text = get_top_leagues()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_worst_leagues_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки 📉 Worst Leagues."""
    # Удаляем предыдущее сообщение "Choose Statistics:"
    if message_id:
        delete_telegram_message(chat_id, message_id)
    
    stats_text = get_worst_leagues()
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Back to Stats'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def _handle_back_stats_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки ↩️ Назад к статистике."""
    # Удаляем текущее сообщение со статистикой
    if message_id:
        delete_telegram_message(chat_id, message_id)
    
    show_stats_menu_buttons(chat_id)


def _handle_back_menu_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки ↩️ Назад в меню."""
    if message_id:
        delete_telegram_message(chat_id, message_id)
    show_menu_buttons(chat_id)


def _handle_help_button(chat_id, message_id=None):
    """Обрабатывает нажатие кнопки ❓ Help."""
    if message_id:
        delete_telegram_message(chat_id, message_id)
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

def _route_message(chat_id, user_name, text, message_id=None):
    """
    Маршрутизирует сообщение на соответствующий обработчик.
    
    Args:
        chat_id: ID чата
        user_name: имя пользователя
        text: текст сообщения
        message_id: ID отправленного сообщения (для удаления меню)
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
        _handle_menu_button(chat_id, message_id)
    elif text == '▶️ Start':
        _handle_start_button(chat_id)
    elif text == '⏹️ Stop':
        _handle_stop_button(chat_id)
    elif text == '📊 Stats':
        _handle_stats_button(chat_id, message_id)
    
    # Кнопки статистики
    elif text == '📚 Summary':
        _handle_full_stats_button(chat_id, message_id)
    elif text == '⚡️ Last 5':
        _handle_last_5_button(chat_id, message_id)
    elif text == '📅 This Month':
        _handle_this_month_button(chat_id, message_id)
    elif text == '🏆 Top Leagues':
        _handle_top_leagues_button(chat_id, message_id)
    elif text == '⛔️ Worst Leagues':
        _handle_worst_leagues_button(chat_id, message_id)
    
    # Кнопки навигации
    elif text == '↩️ Back to Stats':
        _handle_back_stats_button(chat_id, message_id)
    elif text == '↩️ Back to Menu':
        _handle_back_menu_button(chat_id, message_id)
    elif text == '❓ Help':
        _handle_help_button(chat_id, message_id)
    
    # Неизвестная команда
    else:
        _handle_unknown_command(chat_id)


# ============================================================================
# МАРШРУТИЗАТОР CALLBACK'S
# ============================================================================

def _route_callback(chat_id, callback_data, message_id=None):
    """
    Маршрутизирует callback query на соответствующий обработчик.
    
    Args:
        chat_id: ID чата
        callback_data: данные callback'а
        message_id: ID сообщения с кнопками (для удаления)
    """
    if callback_data.startswith('match_'):
        match_id = callback_data.split('_')[1]
        _handle_match_callback(chat_id, int(match_id))
    elif callback_data == 'back_to_stats':
        show_stats_menu_buttons(chat_id)
    elif callback_data == 'back_to_last_5':
        _handle_last_5_button(chat_id)
    elif callback_data == 'close_last_5':
        _handle_close_last_5(chat_id, message_id)
    elif callback_data == 'close_match_details':
        _handle_close_match_details(chat_id, message_id)


def _handle_match_callback(chat_id, match_id):
    """
    Обрабатывает нажатие на матч в меню Last 5.
    Отправляет подробную информацию о матче.
    
    Args:
        chat_id: ID чата
        match_id: ID матча в БД
    """
    match_details = get_match_details_by_id(match_id)
    
    if match_details:
        emoji = match_details['emoji']
        home_team = match_details['home_team']
        away_team = match_details['away_team']
        league = match_details['league']
        prediction = match_details['prediction']
        final_score = match_details['final_score']
        date = match_details['date']
        link = match_details['link']
        odds = match_details['odds']
        
        match_title = f"{emoji} <a href=\"{link}\"><b>{home_team} - {away_team}</b></a>"
        
        match_info = (
            f"{match_title}\n"
            f"{league}\n"
            f"{prediction}\n"
            f"Odds {odds if odds else '?'}\n"
            f"Final score: {final_score}\n"
            f"<b>{date}</b>"
        )
        
        keyboard = {
            'inline_keyboard': [
                [{'text': 'Close', 'callback_data': 'close_match_details'}]
            ]
        }
        
        send_telegram_message(chat_id, match_info, reply_markup=keyboard)
    else:
        send_telegram_message(chat_id, "❌ Матч не найден.")


def _handle_close_last_5(chat_id, message_id):
    """
    Удаляет сообщение со списком Last 5 при нажатии на Close.
    
    Args:
        chat_id: ID чата
        message_id: ID сообщения для удаления
    """
    if message_id:
        delete_telegram_message(chat_id, message_id)
    else:
        print(f"[BOT] Невозможно удалить сообщение - message_id не найден")


def _handle_close_match_details(chat_id, message_id):
    """
    Удаляет сообщение с деталями матча при нажатии на Close.
    
    Args:
        chat_id: ID чата
        message_id: ID сообщения для удаления
    """
    if message_id:
        delete_telegram_message(chat_id, message_id)
    else:
        print(f"[BOT] Невозможно удалить сообщение - message_id не найден")


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
                    message_id = message.get('message_id')
                    
                    if chat_id and text:
                        print(f"[BOT] Сообщение от {user_name} ({chat_id}): {text}")
                        _route_message(chat_id, user_name, text, message_id)
                
                # Обрабатываем callback query (нажатия на inline-кнопки)
                elif 'callback_query' in update:
                    callback_query = update['callback_query']
                    callback_id = callback_query.get('id')
                    message = callback_query.get('message', {})
                    chat_id = message.get('chat', {}).get('id')
                    message_id = message.get('message_id')
                    callback_data = callback_query.get('data', '')
                    user_name = callback_query.get('from', {}).get('first_name', 'User')
                    
                    if chat_id and callback_data:
                        print(f"[BOT] Callback от {user_name} ({chat_id}): {callback_data}")
                        _route_callback(chat_id, callback_data, message_id)
            
            time.sleep(BOT_POLLING_INTERVAL)
            
        except Exception as e:
            print(f"[BOT] Ошибка в polling'е команд: {e}")
            time.sleep(5)

"""
Telegram клавиатуры и интерфейс меню.
Функции для отправки различных меню и кнопок.
"""
from telegram.telegram_client import send_telegram_message


# ============================================================================
# ГЛАВНОЕ МЕНЮ И НАВИГАЦИЯ
# ============================================================================

def send_main_menu(chat_id):
    """
    Отправляет главное меню с приветствием и кнопкой меню (при /start).
    
    Args:
        chat_id: ID чата получателя
    """
    menu_text = (
        "👋🏻 Привет! Я бот для мониторинга прогрузов по БК Crown.\n\n"
        "▶️ Start - подписаться на уведомления\n"
        "⏹️ Stop - отписаться от уведомлений\n"
        "📊 Stats - посмотреть статистику\n"
        "❓ Help - справка\n\n"
        "Нажми на кнопку меню для управления."
    )
    
    keyboard = {
        'keyboard': [
            [{'text': '🎲 Меню'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    
    send_telegram_message(chat_id, menu_text, reply_markup=keyboard)


def show_menu_buttons(chat_id):
    """
    Показывает главное меню со всеми кнопками (при возврате в меню).
    
    Args:
        chat_id: ID чата получателя
    """
    keyboard = {
        'keyboard': [
            [{'text': '▶️ Start'}, {'text': '⏹️ Stop'}],
            [{'text': '📊 Stats'}],
            [{'text': '❓ Help'}],
            [{'text': '🎲 Меню'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    
    send_telegram_message(chat_id, 'Главное меню', reply_markup=keyboard)


# ============================================================================
# МЕНЮ СТАТИСТИКИ
# ============================================================================

def show_stats_menu_buttons(chat_id):
    """
    Показывает меню выбора статистики (при возврате из статистики).
    
    Args:
        chat_id: ID чата получателя
    """
    keyboard = {
        'keyboard': [
            [{'text': '📈 Full Stats'}],
            [{'text': '🏆 Top Leagues'}],
            [{'text': '📉 Worst Leagues'}],
            [{'text': '↩️ Назад в меню'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    
    send_telegram_message(chat_id, 'Выбери статистику:', reply_markup=keyboard)


def send_stats_submenu(chat_id):
    """
    Отправляет подменю с опциями статистики (при выборе Stats).
    
    Args:
        chat_id: ID чата получателя
    """
    keyboard = {
        'keyboard': [
            [{'text': '📈 Full Stats'}],
            [{'text': '🏆 Top Leagues'}],
            [{'text': '📉 Worst Leagues'}],
            [{'text': '↩️ Назад в меню'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    
    send_telegram_message(chat_id, 'Выбери статистику:', reply_markup=keyboard)


# ============================================================================
# КЛАВИАТУРЫ ДЛЯ ОТДЕЛЬНЫХ ЭКРАНОВ
# ============================================================================

def send_stats_back_keyboard(chat_id, stats_text):
    """
    Отправляет статистику с кнопкой возврата к меню статистики.
    
    Args:
        chat_id: ID чата получателя
        stats_text: текст статистики для отправки
    """
    keyboard = {
        'keyboard': [
            [{'text': '↩️ Назад к статистике'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    send_telegram_message(chat_id, stats_text, reply_markup=keyboard)


def send_main_menu_keyboard(chat_id, help_text=None):
    """
    Отправляет текст с кнопкой возврата в главное меню.
    
    Args:
        chat_id: ID чата получателя
        help_text: текст для отправки (справка и т.д.)
    """
    keyboard = {
        'keyboard': [
            [{'text': '🎲 Меню'}]
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }
    
    if help_text:
        send_telegram_message(chat_id, help_text, reply_markup=keyboard)
    else:
        show_menu_buttons(chat_id)

"""
NowGoal Bot - Microservices Architecture
Микросервисная архитектура для мониторинга прогрузов по БК Crown.

Структура слоев:
- config: конфигурация и переменные окружения
- database: работа с PostgreSQL БД
- utils: вспомогательные функции для текста
- selenium_utils: управление Selenium WebDriver
- subscribers: управление подписчиками (load, save, add, remove)
- telegram_client: отправка сообщений в Telegram API
- keyboards: клавиатуры и меню
- stats: получение и форматирование статистики
- command_handler: обработка команд и polling Telegram бота
- parsers: парсинг матчей и коэффициентов (Over/Under, Asian Handicap)
- models: модели данных (Match, MetaMatch)
- main: точка входа приложения с управлением жизненным циклом
"""

from .config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, TABLE_NAME,
    BOT_TOKEN, USERS_FILE, BOT_POLLING_INTERVAL,
    RATE, DRIVER_PATH, CHROME_BINARY, HEADLESS, MAX_WORKERS,
    RESTART_HOURS, RESTART_INTERVAL
)

from .database import get_db_conn, insert_match_to_db
from .utils import strip_html_tags, ensure_text
from .selenium_utils import create_driver, cleanup_selenium_chromes, safe_click

# Telegram сервис - управление подписчиками
from .subscribers import load_subscribers, save_subscribers, add_subscriber, remove_subscriber

# Telegram сервис - отправка сообщений
from .telegram_client import send_telegram_message, send_message_to_all, send_message

# Telegram сервис - клавиатуры и меню
from .keyboards import (
    send_main_menu, show_menu_buttons, show_stats_menu_buttons, send_stats_submenu,
    send_stats_back_keyboard, send_main_menu_keyboard
)

# Telegram сервис - статистика
from .stats import get_full_stats, get_top_leagues, get_worst_leagues

# Telegram сервис - обработка команд
from .command_handler import handle_telegram_commands

# Модели данных
from .models import Match, MetaMatch
from .parsers import parse_match, parse_all_matches

__all__ = [
    # config
    'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASS', 'TABLE_NAME',
    'BOT_TOKEN', 'USERS_FILE', 'BOT_POLLING_INTERVAL',
    'RATE', 'DRIVER_PATH', 'CHROME_BINARY', 'HEADLESS', 'MAX_WORKERS',
    'RESTART_HOURS', 'RESTART_INTERVAL',
    # database
    'get_db_conn', 'insert_match_to_db',
    # utils
    'strip_html_tags', 'ensure_text',
    # selenium_utils
    'create_driver', 'cleanup_selenium_chromes', 'safe_click',
    # subscribers
    'load_subscribers', 'save_subscribers', 'add_subscriber', 'remove_subscriber',
    # telegram_client
    'send_telegram_message', 'send_message_to_all', 'send_message',
    # keyboards
    'send_main_menu', 'show_menu_buttons', 'show_stats_menu_buttons', 'send_stats_submenu',
    'send_stats_back_keyboard', 'send_main_menu_keyboard',
    # stats
    'get_full_stats', 'get_top_leagues', 'get_worst_leagues',
    # command_handler
    'handle_telegram_commands',
    # parsers
    'parse_match', 'parse_all_matches',
    # models
    'Match', 'MetaMatch',
]

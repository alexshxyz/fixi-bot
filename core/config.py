"""
Конфигурация и переменные окружения для бота
"""
import os

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DB_HOST = os.environ.get('PG_HOST', 'localhost')
DB_PORT = os.environ.get('PG_PORT', '5432')
DB_NAME = os.environ.get('PG_NAME', 'postgres')
DB_USER = os.environ.get('PG_USER', 'postgres')
DB_PASS = os.environ.get('PG_PASS', 'postgres')
TABLE_NAME = os.environ.get('PG_TABLE', 'matches')

# ============================================================================
# TELEGRAM BOT CONFIGURATION
# ============================================================================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8616346587:AAGLsNDIt-kQSNnjNlCTdC2sWfAMLPR5kms')  # MAIN BOT ТОКЕН
USERS_FILE = os.environ.get('USERS_FILE', 'new_bot_playwrite/subscribers.json')  # Файл для хранения chat_ids подписчиков
BOT_POLLING_INTERVAL = 1  # интервал polling'а для получения команд (в секундах)

# ============================================================================
# TEST MODE CONFIGURATION
# ============================================================================
TEST_MODE = True  # Включить тестовый режим (используется новый бот, пустой список подписчиков)

# ============================================================================
# PARSING & ODDS CONFIGURATION
# ============================================================================
RATE = 0.61

# ============================================================================
# PLAYWRIGHT & BROWSER CONFIGURATION
# ============================================================================
HEADLESS = True
MAX_WORKERS = 7 # количество параллельных вкладок в одном браузере

# ============================================================================
# RESTART CONFIGURATION
# ============================================================================
RESTART_HOURS = 10  # restart script after this many hours from startup
RESTART_INTERVAL = RESTART_HOURS * 3600

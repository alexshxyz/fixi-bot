"""
Точка входа приложения NowGoal Bot.
Запускает polling команд Telegram в отдельном потоке и циклирует парсинг матчей в основном потоке.
"""
import os
import sys
import time
import asyncio
import threading
import signal
import atexit
from pathlib import Path

# Добавляем текущую директорию в sys.path для работы с модулями как packages
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Теперь можем импортировать модули
from core.config import RESTART_HOURS, RESTART_INTERVAL
from parsers.playwright_utils import cleanup_chrome_processes, cleanup_browser
from telegram.command_handler import handle_telegram_commands
from parsers.parsers import parse_all_matches


def main():
    """Основная точка входа приложения"""
    
    # Флаг для graceful shutdown
    shutdown_event = threading.Event()
    
    def signal_handler(signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print("\n[INFO] Получен сигнал выхода, завершаем работу...")
        shutdown_event.set()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Терминирование процесса
    
    # Регистрируем очистку при выходе
    def cleanup_on_exit():
        """Финальная очистка при выходе"""
        print("[CLEANUP] Выполняем финальную очистку...")
        try:
            cleanup_chrome_processes()
        except Exception:
            pass
        try:
            # Пытаемся поочистить Playwright асинхронно если возможно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(cleanup_browser())
            loop.close()
        except Exception:
            pass
    
    atexit.register(cleanup_on_exit)
    
    # Очищаем оставшиеся Chrome процессы
    cleanup_chrome_processes()
    
    # Запускаем polling для команд бота в отдельном потоке
    bot_thread = threading.Thread(target=handle_telegram_commands, daemon=True)
    bot_thread.start()
    print("[BOT] 🤖 Polling для команд запущен в отдельном потоке")
    
    # Отслеживаем время работы и перезапускаем процесс через интервал RESTART_INTERVAL
    start_time = time.time()
    while not shutdown_event.is_set():
        try:
            # Проверяем, не пора ли перезагрузить процесс
            if time.time() - start_time >= RESTART_INTERVAL:
                print(f"[INFO] Достигнут интервал перезагрузки ({RESTART_HOURS}ч). Выполняем чистый перезапуск...")
                # Попытка очистить Chrome процессы перед заменой процесса
                try:
                    cleanup_chrome_processes()
                except Exception:
                    pass
                # Заменяем текущий процесс Python новым экземпляром с теми же аргументами
                os.execv(sys.executable, [sys.executable] + sys.argv)
            
            # Основной цикл: парсим все матчи (async)
            asyncio.run(parse_all_matches())
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("[INFO] Выход...")
            shutdown_event.set()
        except Exception as e:
            print(f"[ERROR] Неожиданная ошибка: {e}")
            time.sleep(5)


if __name__ == '__main__':
    main()

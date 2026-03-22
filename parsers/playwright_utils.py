"""
Утилиты для работы с Playwright и управления браузерными процессами.
Реализует пул с 1 браузером и несколькими страницами для параллельной обработки.
"""
import asyncio
import os
import psutil
import warnings
import gc
from playwright.async_api import async_playwright, Page, BrowserContext
from core.config import HEADLESS

# Подавляем ResourceWarning для asyncio subprocess (проблема с закрытием pipe)
warnings.filterwarnings('ignore', category=ResourceWarning, module='asyncio')
# Переводим остальные ResourceWarning в debug режим (не выводим в консоль)
warnings.filterwarnings('ignore', message='.*unclosed transport.*')


# Глобальный браузер и пул контекстов/страниц
_browser = None
_pages: list[Page] = []
_context: BrowserContext = None


async def init_browser(max_pages: int = 10):
    """
    Инициализирует один браузер с несколькими страницами.
    
    Args:
        max_pages: максимальное количество параллельных страниц
    """
    global _browser, _pages, _context
    
    playwright = await async_playwright().start()
    
    # Запускаем Chromium с оптимальными параметрами
    _browser = await playwright.chromium.launch(
        headless=HEADLESS,
    )
    
    # Создаём контекст с нужными параметрами
    _context = await _browser.new_context(
        user_agent="Lynx: Lynx/2.8.8pre.4 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.12.23",
        ignore_https_errors=True,
    )
    
    # Инициализируем пул страниц
    _pages = []
    for _ in range(max_pages):
        page = await _context.new_page()
        # Устанавливаем параметры страницы
        await page.route('**/*', lambda route: handle_route(route))
        _pages.append(page)
    
    print(f"[BROWSER] Инициализирован браузер с {len(_pages)} страницами")
    return _browser, _context, _pages


async def handle_route(route):
    """Обработчик маршрутов для оптимизации загрузки страниц"""
    request = route.request
    # Разрешаем ВСЕ основные ресурсы для корректной работы UI
    # Блокируем только тяжёлые аналитику и объявления если нужно оптимизировать
    resource_type = request.resource_type
    
    # Разрешаем все ресурсы (HTML, CSS, JS, изображения, шрифты и т.д.)
    await route.continue_()


async def get_page() -> Page:
    """Получает свободную страницу из пула"""
    if not _pages:
        raise RuntimeError("Пул страниц не инициализирован. Вызовите init_browser() сначала.")
    return _pages[0]


async def release_page(page: Page):
    """Освобождает страницу (очищает её и возвращает в пул)"""
    try:
        # Очищаем страницу
        await page.goto("about:blank")
    except Exception:
        pass


async def cleanup_browser():
    """Закрывает браузер и все страницы с агрессивной очисткой ресурсов"""
    global _browser, _pages, _context
    
    try:
        if _pages:
            # Закрываем все страницы с timeout
            for page in _pages:
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', category=ResourceWarning)
                        # Используем timeout чтобы предотвратить зависание
                        try:
                            await asyncio.wait_for(page.close(), timeout=5.0)
                        except asyncio.TimeoutError:
                            # Если страница не закрывается, просто игнорируем
                            pass
                except Exception:
                    pass
            _pages = []
        
        if _context:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', category=ResourceWarning)
                    try:
                        await asyncio.wait_for(_context.close(), timeout=5.0)
                    except asyncio.TimeoutError:
                        pass
            except Exception:
                pass
            _context = None
        
        if _browser:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', category=ResourceWarning)
                    try:
                        await asyncio.wait_for(_browser.close(), timeout=5.0)
                    except asyncio.TimeoutError:
                        pass
            except Exception:
                pass
            _browser = None
        
        # Принудительно запускаем garbage collection чтобы освободить ресурсы
        gc.collect()
        
        print("[CLEANUP] Браузер закрыт корректно")
    except Exception as e:
        print(f"[CLEANUP WARNING] {e}")
        # Даже при ошибке очистки, пытаемся запустить GC
        gc.collect()


def cleanup_chrome_processes():
    """
    Закрывает оставшиеся Chrome процессы (для совместимости со старым кодом).
    """
    current_pid = os.getpid()
    killed = 0

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'] or ''
            cmd = ' '.join(proc.info.get('cmdline') or [])
            pid = proc.info['pid']

            if pid == current_pid:
                continue

            if (
                'chromedriver' in name.lower()
                or ('chrome' in name.lower() and (
                    '--remote-debugging-port' in cmd or
                    '--user-data-dir' in cmd and 'Temp' in cmd or
                    '--disable-blink-features=AutomationControlled' in cmd
                ))
            ):
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            print(f"[CLEANUP WARNING] {e}")

    if killed:
        print(f"[CLEANUP] Закрыто {killed} Chrome процессов.")
    else:
        print("[CLEANUP] Нечего закрывать (чисто).")


async def safe_click(page: Page, selector: str, wait_ms: int = 15000, retries: int = 3, poll_ms: int = 500):
    """
    Надёжный клик с несколькими попытками.
    
    Стратегия:
    1. Ждёт видимости элемента
    2. Пробует обычный click()
    3. Скроллит элемент в центр экрана и пробует снова
    4. Пробует JavaScript click() как последний вариант
    5. Повторяет несколько раз при ошибках
    
    Args:
        page: Page объект Playwright
        selector: CSS селектор элемента
        wait_ms: максимальное время ожидания элемента (миллисекунды)
        retries: количество попыток клика
        poll_ms: интервал опроса (миллисекунды)
        
    Returns:
        bool: True если клик успешен
        
    Raises:
        Exception: если не удалось кликнуть после всех попыток
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            # Ждём видимости элемента
            await page.wait_for_selector(selector, timeout=wait_ms)
            
            # Пробуем обычный клик
            try:
                await page.click(selector)
                return True
            except Exception as e_click:
                last_exc = e_click
                # Скроллим в центр и пробуем снова
                try:
                    await page.evaluate(f"""
                        el => el.scrollIntoView({{block: 'center'}});
                    """, await page.query_selector(selector))
                    await asyncio.sleep(0.15)
                    await page.click(selector)
                    return True
                except Exception:
                    last_exc = Exception("normal click failed: " + repr(last_exc))
                    # Финальный вариант: JS click
                    try:
                        await page.evaluate(f"el => el.click();", await page.query_selector(selector))
                        return True
                    except Exception as e_js:
                        last_exc = e_js
        except Exception as e_wait:
            last_exc = e_wait
        
        # Небольшая пауза перед повторной попыткой
        await asyncio.sleep(0.3)
    
    # Если дошли сюда — не удалось
    raise last_exc or Exception("safe_click failed")


async def wait_for_JS_object(page: Page, obj_name: str, timeout_ms: int = 30000):
    """
    Ждёт пока JavaScript объект будет определён на странице.
    
    Args:
        page: Page объект Playwright
        obj_name: имя объекта (e.g., '_oddsDetailWin')
        timeout_ms: timeout в миллисекундах
        
    Returns:
        bool: True если объект найден
    """
    try:
        start_time = asyncio.get_event_loop().time()
        while True:
            try:
                result = await page.evaluate(f"typeof {obj_name} !== 'undefined'")
                if result:
                    return True
            except Exception:
                pass
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            if elapsed > timeout_ms:
                raise TimeoutError(f"JS object '{obj_name}' not defined after {timeout_ms}ms")
            
            await asyncio.sleep(0.1)
    except Exception as e:
        raise e

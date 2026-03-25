"""
Слой работы с БД PostgreSQL.
Функции для подключения, вставки матчей и получения статистики.
"""
import psycopg2
from psycopg2 import sql
from datetime import datetime
from core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, TABLE_NAME
from utils.utils import ensure_text, strip_html_tags


def get_db_conn():
    """
    Возвращает подключение к PostgreSQL базе данных.
    Использует переменные окружения из config.
    """
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


def insert_match_to_db(match, prediction_text=None, table=TABLE_NAME):
    """
    Вставляет матч в указанную таблицу.
    
    Args:
        match: объект Match с атрибутами liga, first_team, second_team, chosen_over, odds, url
        prediction_text: текст прогноза (опционально)
        table: имя таблицы для вставки
        
    Ожидаемые колонки таблицы: league, home_team, away_team, prediction, odds, 
                                final_score, result, link, script
    """
    # --- подготовка полей из объекта match ---
    league = getattr(match, 'liga', '') or getattr(match, 'league', '') or ''
    home = getattr(match, 'first_team', '') or getattr(match, 'home_team', '') or ''
    away = getattr(match, 'second_team', '') or getattr(match, 'away_team', '') or ''
    
    # подготовка prediction и odds
    prediction = ensure_text(prediction_text) if prediction_text else ''
    prediction = strip_html_tags(prediction)  # удаляем HTML-теги
    
    odds = None
    try:
        # если в match хранится "added" value как chosen_over (например 0.56) — добавим 1.0
        if getattr(match, 'chosen_over', None) is not None:
            odds = float(match.chosen_over) + 1.0
        else:
            # либо напрямую поле odds
            if getattr(match, 'odds', None) is not None:
                odds = float(match.odds)
    except Exception:
        odds = None

    final_score = ''  # как просил — пустое
    result = ''       # пустое
    link = getattr(match, 'url', '') or getattr(match, 'link', '') or ''
    script_flag = None  # оставляем NULL, можно поставить True/False
    match_date = datetime.now().strftime('%Y-%m-%d')  # текущая дата в формате YYYY-MM-DD для PostgreSQL

    params = (league, home, away, prediction, odds, final_score, result, link, script_flag, match_date)

    # --- используем psycopg2.sql для безопасной подстановки имени таблицы ---
    insert_query = sql.SQL("""
        INSERT INTO {table} (id, league, home_team, away_team, prediction, odds, final_score, result, link, script, date, row_order)
        VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT)
    """).format(table=sql.Identifier(table))

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(insert_query, params)
        conn.commit()
        cur.close()
        print(f"[DB] Inserted into {table}: {league} — {home} vs {away} (odds={odds})")
    except Exception as e:
        print(f"[DB ERROR] Failed to insert match into {table}: {e}")
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        raise
    finally:
        if conn:
            conn.close()


def check_match_exists(link: str, prediction: str = None, table=TABLE_NAME) -> bool:
    """
    Проверяет наличие матча в БД по link (URL) и prediction.
    
    Используется для предотвращения отправки дубликатов уведомлений.
    Один матч может иметь несколько разных прогнозов (Over HT, Over FT, AH и т.д.),
    но один и тот же прогноз не должен отправляться дважды.
    
    Args:
        link: URL матча (например, 'https://www.nowgoal.com/oddscomp/12345')
        prediction: текст прогноза (например, 'Over 2.5 HT', 'Asian Handicap -0/0.5')
        table: имя таблицы для проверки
        
    Returns:
        bool: True если такой же матч с таким же прогнозом найден в БД, False если нет
    """
    if not link or not isinstance(link, str):
        print(f"[DB DEBUG] check_match_exists: link невалидный: {link}")
        return False
    
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Если prediction не указан, проверяем только по link
        if prediction is None or prediction == "":
            check_query = sql.SQL("SELECT COUNT(*) FROM {table} WHERE link = %s").format(
                table=sql.Identifier(table)
            )
            params = (link,)
            cur.execute(check_query, params)
            count = cur.fetchone()[0]
            cur.close()
            
            print(f"[DB DEBUG] Проверка по link '{link}': найдено {count} записей")
            return count > 0
        else:
            # Проверяем комбинацию link + prediction для избежания дубликатов одного сигнала
            # Сначала получаем что есть в БД для этого матча
            select_query = sql.SQL("SELECT link, prediction FROM {table} WHERE link = %s").format(
                table=sql.Identifier(table)
            )
            cur.execute(select_query, (link,))
            existing_rows = cur.fetchall()
            
            if existing_rows:
                print(f"[DB DEBUG] Для link '{link}' найдено {len(existing_rows)} записей:")
                for row in existing_rows:
                    l, p = row
                    print(f"  - prediction: '{p}'")
            else:
                print(f"[DB DEBUG] Для link '{link}' записей в БД не найдено")
            
            # Пытаемся найти точное совпадение
            check_query = sql.SQL("SELECT COUNT(*) FROM {table} WHERE link = %s AND prediction = %s").format(
                table=sql.Identifier(table)
            )
            params = (link, prediction)
            cur.execute(check_query, params)
            count = cur.fetchone()[0]
            cur.close()
            
            print(f"[DB DEBUG] Проверка link + prediction: ")
            print(f"  - link: '{link}'")
            print(f"  - prediction: '{prediction}'")
            print(f"  - результат: найдено {count} совпадения(й)")
            
            # Если есть точное совпадение, то это дубликат
            if count > 0:
                print(f"[DB] ✗ Этот сигнал уже отправлен (найдено в БД)")
                return True
            else:
                print(f"[DB] ✓ Новый сигнал, можно отправлять")
                return False
    
    except Exception as e:
        print(f"[DB ERROR] Ошибка при проверке матча в БД: {e}")
        import traceback
        traceback.print_exc()
        # В случае ошибки БД, возвращаем False (отправляем матч, чтобы не потерять уведомление)
        return False
    finally:
        if conn:
            conn.close()


def get_match_from_db(link: str, table=TABLE_NAME):
    """
    Возвращает данные матча из БД по link (для отладки).
    
    Args:
        link: URL матча
        table: имя таблицы
        
    Returns:
        tuple с (link, prediction) или None если не найдено
    """
    if not link or not isinstance(link, str):
        return None
    
    check_query = sql.SQL("""
        SELECT link, prediction FROM {table} WHERE link = %s LIMIT 5
    """).format(table=sql.Identifier(table))
    
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(check_query, (link,))
        results = cur.fetchall()
        cur.close()
        
        if results:
            print(f"[DB DEBUG] Найдено {len(results)} записей для {link}:")
            for row in results:
                link_val, pred_val = row
                print(f"  - link: {link_val}")
                print(f"  - prediction: '{pred_val}'")
        else:
            print(f"[DB DEBUG] Записей для {link} не найдено")
        
        return results
    except Exception as e:
        print(f"[DB ERROR] Ошибка при получении матча: {e}")
        return None
    finally:
        if conn:
            conn.close()

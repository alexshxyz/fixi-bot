"""
Сервис получения статистики матчей из БД.
Функции для расчёта и форматирования статистики по лигам и в целом.
"""
from database.database import get_db_conn


def get_full_stats():
    """
    Получает полную статистику со всей базы данных.
    
    Returns:
        str: отформатированный HTML-текст с общей статистикой
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        query = """
        SELECT
            COUNT(*) AS total_matches, 
            SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'Lost' THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids,
            ROUND(
                SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0),
                0
            ) AS win_percent
        FROM matches;
        """
        
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            total_matches, wins, losses, voids, win_percent = result
            wins = wins or 0
            losses = losses or 0
            voids = voids or 0
            win_percent = int(win_percent) if win_percent else 0
            
            stats_text = (
                f"📈 <b>Full Stats</b>\n\n"
                f"Всего матчей: <b>{total_matches}</b>\n\n"
                f"✅: <b>{wins}</b> "
                f"❌: <b>{losses}</b> "
                f"🔁: <b>{voids}</b>\n\n"
                f"Процент побед: <b>{win_percent}%</b>"
            )
            return stats_text
        else:
            return "📈 <b>Full Stats</b>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении полной статистики: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_top_leagues():
    """
    Получает топ 3 лиги по количеству побед.
    
    Returns:
        str: отформатированный HTML-текст с топ лигами
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        query = """
        SELECT 
            league,
            COUNT(*) AS total_matches,
            SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'Lost' THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids,
            ROUND(
                SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END)::numeric 
                / NULLIF(COUNT(*), 0) * 100,
                0
            ) AS win_percent
        FROM matches
        GROUP BY league
        ORDER BY 
            wins DESC,
            losses ASC
        LIMIT 3
        """
        
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if results:
            stats_text = "🏆 <b>Top Leagues</b>\n\n"
            for league, total_matches, wins, losses, voids, win_percent in results:
                wins = wins or 0
                losses = losses or 0
                voids = voids or 0
                win_percent = int(win_percent) if win_percent else 0
                
                stats_text += (
                    f"<i>{league}</i>\n"
                    f"<blockquote>{wins}+ {losses}- {voids}=</blockquote>\n"
                    f"Процент побед: <b>{win_percent}%</b>\n\n"
                )
            return stats_text.rstrip()
        else:
            return "🏆 <b>Top Leagues</b>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении топ-лиг: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_worst_leagues():
    """
    Получает худшие 3 лиги по количеству побед.
    
    Returns:
        str: отформатированный HTML-текст с худшими лигами
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        query = """
        SELECT 
            league,
            COUNT(*) AS total_matches,
            SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'Lost' THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids,
            ROUND(
                SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END)::numeric 
                / NULLIF(COUNT(*), 0) * 100,
                0
            ) AS win_percent
        FROM matches
        GROUP BY league
        ORDER BY 
            wins ASC,
            losses DESC
        LIMIT 3
        """
        
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if results:
            stats_text = "📉 <b>Worst Leagues</b>\n\n"
            for league, total_matches, wins, losses, voids, win_percent in results:
                wins = wins or 0
                losses = losses or 0
                voids = voids or 0
                win_percent = int(win_percent) if win_percent else 0
                
                stats_text += (
                    f"<i>{league}</i>\n"
                    f"<blockquote>{wins}+ {losses}- {voids}=</blockquote>\n"
                    f"Процент побед: <b>{win_percent}%</b>\n\n"
                )
            return stats_text.rstrip()
        else:
            return "📉 <b>Worst Leagues</b>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении худших лиг: {e}")
        return f"❌ Ошибка при получении статистики: {e}"

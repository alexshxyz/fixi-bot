"""
Сервис получения статистики матчей из БД.
Функции для расчёта и форматирования статистики по лигам и в целом.
"""
from database.database import get_db_conn
import matplotlib
matplotlib.use('Agg')  # Используем non-interactive backend для многопоточности
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from datetime import datetime


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


def get_last_5_matches():
    """
    Получает последние 5 матчей из БД в порядке от старого к новому
    (последняя запись в БД - самая нижняя в выводе).
    
    Returns:
        str: отформатированный HTML-текст с последними 5 матчами
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        query = """
        SELECT 
            league,
            home_team,
            away_team,
            prediction,
            final_score,
            result,
            link,
            date
        FROM matches
        ORDER BY id DESC
        LIMIT 5
        """
        
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if results:
            # Не разворачиваем - выводим в порядке DESC, чтобы самый новый матч был первым
            stats_text = "⚡️ <b>Last 5</b>\n\n"
            
            for league, home_team, away_team, prediction, final_score, result, link, match_date in results:
                # Подготавливаем значения, заменяя пустые на "?"
                league = league or "?"
                home_team = home_team or "?"
                away_team = away_team or "?"
                prediction = prediction or "?"
                final_score = final_score or "?"
                link = link or "?"
                
                # Преобразуем дату из формата YYYY-MM-DD в DD-MM-YYYY
                if match_date:
                    try:
                        if isinstance(match_date, str):
                            # Парсим строку в формате YYYY-MM-DD (как сохраняется в БД)
                            date_obj = datetime.strptime(match_date, '%Y-%m-%d')
                            match_date = date_obj.strftime('%d-%m-%Y')
                        else:
                            # Если это объект date/datetime, преобразуем
                            match_date = match_date.strftime('%d-%m-%Y')
                    except Exception as e:
                        print(f"[STATS] Ошибка при преобразовании даты {match_date}: {e}")
                        match_date = "?"
                else:
                    match_date = "?"
                
                # Форматируем результат только смайликом
                if result == 'Won':
                    result_emoji = "✅"
                elif result == 'Lost':
                    result_emoji = "❌"
                elif result == 'Void':
                    result_emoji = "🔁"
                else:
                    result_emoji = "?"
                
                # Собираем сообщение в нужном формате
                stats_text += (
                    f"{league}\n"
                    f"<b>{home_team} - {away_team}</b>\n"
                    f"<b>{prediction}</b>\n"
                    f"{result_emoji} ({final_score})\n"
                    f"<b>{match_date}</b>\n"
                    f"{link}\n\n"
                )
            
            return stats_text.rstrip()
        else:
            return "⚡️ <b>Last 5</b>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении последних матчей: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_this_month_stats():
    """
    Получает статистику матчей за текущий месяц.
    
    Returns:
        str: отформатированный HTML-текст со статистикой за месяц
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Получаем текущий год и месяц
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # Получаем первый день текущего месяца и первый день следующего месяца
        first_day_current = datetime(current_year, current_month, 1).date()
        if current_month == 12:
            first_day_next = datetime(current_year + 1, 1, 1).date()
        else:
            first_day_next = datetime(current_year, current_month + 1, 1).date()
        
        # Названия месяцев в именительном падеже
        month_names = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        current_month_name = month_names.get(current_month, "Неизвестный месяц")
        
        query = """
        SELECT
            COUNT(*) AS total_matches,
            SUM(CASE WHEN result = 'Won' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'Lost' THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids
        FROM matches
        WHERE date IS NOT NULL AND date >= %s AND date < %s
        """
        
        cur.execute(query, (first_day_current, first_day_next))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            total_matches, wins, losses, voids = result
            wins = wins or 0
            losses = losses or 0
            voids = voids or 0
            
            # Вычисляем процент побед (без учета Void)
            matches_to_calc = wins + losses
            if matches_to_calc > 0:
                win_percent = int(wins * 100 / matches_to_calc)
            else:
                win_percent = 0
            
            # Вычисляем прибыль
            profit = wins * 0.8 + losses * (-1) + voids * 0
            profit_str = f"+{profit:.2f}" if profit >= 0 else f"{profit:.2f}"
            
            stats_text = (
                f"<b>📅 {current_month_name}</b>\n\n"
                f"Матчей: <b>{total_matches}</b>\n"
                f"<blockquote>{wins}+ {losses}- {voids}=</blockquote>\n"
                f"Процент побед: <b>{win_percent}%</b>\n\n"
                f"Прибыль: <b>{profit_str} флетов</b>"
            )
            return stats_text
        else:
            return f"<i>{current_month_name}</i>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении статистики за месяц: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_profit_graph():
    """
    Генерирует график прибыли по датам матчей.
    Прибыль считается: Won = +0.8, Lost = -1, Void = 0
    
    Returns:
        BytesIO: изображение графика или None при ошибке
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Получаем все матчи с датой и результатом, отсортированные по дате
        query = """
        SELECT 
            date,
            result
        FROM matches
        WHERE date IS NOT NULL
        ORDER BY date ASC
        """
        
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if not results:
            return None
        
        # Подготавливаем данные для графика
        dates = []
        cumulative_profit = []
        current_profit = 0
        
        for match_date, result in results:
            try:
                # Парсим дату в формате YYYY-MM-DD (как сохраняется в БД)
                if isinstance(match_date, str):
                    date_obj = datetime.strptime(match_date, '%Y-%m-%d')
                else:
                    date_obj = match_date
                
                # Считаем профит для текущего матча
                if result == 'Won':
                    profit = 0.8
                elif result == 'Lost':
                    profit = -1.0
                elif result == 'Void':
                    profit = 0.0
                else:
                    profit = 0.0
                
                current_profit += profit
                dates.append(date_obj)
                cumulative_profit.append(current_profit)
                
            except Exception as e:
                print(f"[GRAPH] Ошибка при обработке матча {match_date}: {e}")
                continue
        
        if not dates:
            return None
        
        # Создаем график
        plt.figure(figsize=(12, 6))
        plt.plot(dates, cumulative_profit, marker='o', linewidth=2, markersize=5, color='#2E86AB')
        
        # Форматирование оси X
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%y'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')
        
        # Добавляем сетку и заголовки
        plt.grid(True, alpha=0.3)
        plt.xlabel('Дата', fontsize=11)
        plt.ylabel('Прибыль (флеты)', fontsize=11)
        plt.title('График доходности', fontsize=13, fontweight='bold')
        
        # Добавляем нулевую линию
        plt.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
        
        # Плотный layout
        plt.tight_layout()
        
        # Сохраняем в BytesIO
        image_bytes = BytesIO()
        plt.savefig(image_bytes, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        
        image_bytes.seek(0)
        return image_bytes
        
    except Exception as e:
        print(f"[DB] Ошибка при генерации графика прибыли: {e}")
        return None

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
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids
        FROM matches;
        """
        
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            total_matches, wins, losses, voids = result
            wins = wins or 0
            losses = losses or 0
            voids = voids or 0
            
            # Рассчитываем WR (Win Rate) - исключаем Void
            matches_without_void = wins + losses
            if matches_without_void > 0:
                win_rate = int(wins * 100 / matches_without_void)
            else:
                win_rate = 0
            
            # Рассчитываем Profit и ROI
            # Won = +0.8, Lost = -1, Void = 0
            profit = wins * 0.8 - losses * 1
            if total_matches > 0:
                roi = int(profit * 100 / total_matches)
            else:
                roi = 0
            
            stats_text = (
                f"📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n"
                f"💰 {roi}% ROI 📈 {win_rate}% WR\n\n"
                f"{total_matches} матчей ({wins}W / {losses}L / {voids}D)"
            )
            return stats_text
        else:
            return "📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n\nДанных в базе нет."
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
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids
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
            for idx, (league, total_matches, wins, losses, voids) in enumerate(results, 1):
                wins = wins or 0
                losses = losses or 0
                voids = voids or 0
                
                # Рассчитываем WR - исключаем Void
                matches_without_void = wins + losses
                if matches_without_void > 0:
                    win_rate = int(wins * 100 / matches_without_void)
                else:
                    win_rate = 0
                
                stats_text += (
                    f"{idx}. <i>{league}</i>\n"
                    f"{wins}W / {losses}L / {voids}D — {win_rate}%\n\n"
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
            SUM(CASE WHEN result = 'Void' THEN 1 ELSE 0 END) AS voids
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
            for idx, (league, total_matches, wins, losses, voids) in enumerate(results, 1):
                wins = wins or 0
                losses = losses or 0
                voids = voids or 0
                
                # Рассчитываем WR - исключаем Void
                matches_without_void = wins + losses
                if matches_without_void > 0:
                    win_rate = int(wins * 100 / matches_without_void)
                else:
                    win_rate = 0
                
                stats_text += (
                    f"{idx}. <i>{league}</i>\n"
                    f"{wins}W / {losses}L / {voids}D — {win_rate}%\n\n"
                )
            return stats_text.rstrip()
        else:
            return "📉 <b>Worst Leagues</b>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении худших лиг: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_last_5_matches():
    """
    Получает последние 5 матчей из БД с компактным форматом.
    
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
            date,
            link
        FROM matches
        ORDER BY id DESC
        LIMIT 5
        """
        
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if results:
            stats_text = "<b>⚡️ LAST 5</b>\n\n"
            
            for league, home_team, away_team, prediction, final_score, result, match_date, link in results:
                # Подготавливаем значения, заменяя пустые на "?"
                league = league or "?"
                home_team = home_team or "?"
                away_team = away_team or "?"
                prediction = prediction or "?"
                final_score = final_score or "?"
                link = link or "#"
                
                # Преобразуем дату из формата YYYY-MM-DD в ДД.МММ.ГГ
                if match_date:
                    try:
                        if isinstance(match_date, str):
                            # Парсим строку в формате YYYY-MM-DD (как сохраняется в БД)
                            date_obj = datetime.strptime(match_date, '%Y-%m-%d')
                            match_date = date_obj.strftime('%d.%m.%y')
                        else:
                            # Если это объект date/datetime, преобразуем
                            match_date = match_date.strftime('%d.%m.%y')
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
                match_text = f"{result_emoji} <b>{home_team} - {away_team} ({final_score})</b>"
                
                stats_text += (
                    f"<a href=\"{link}\">{match_text}</a>\n"
                    f"{league} | {prediction} | <b>{match_date}</b>\n\n"
                )
            
            return stats_text.rstrip()
        else:
            return "⚡️ LAST 5\n\nДанных в базе нет."
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
            1: "ЯНВАРЬ", 2: "ФЕВРАЛЬ", 3: "МАРТ", 4: "АПРЕЛЬ",
            5: "МАЙ", 6: "ИЮНЬ", 7: "ИЮЛЬ", 8: "АВГУСТ",
            9: "СЕНТЯБРЬ", 10: "ОКТЯБРЬ", 11: "НОЯБРЬ", 12: "ДЕКАБРЬ"
        }
        current_month_name = month_names.get(current_month, "НЕИЗВЕСТНЫЙ МЕСЯЦ")
        
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
            
            # Вычисляем WR (Win Rate) - исключаем Void
            matches_without_void = wins + losses
            if matches_without_void > 0:
                win_rate = int(wins * 100 / matches_without_void)
            else:
                win_rate = 0
            
            # Вычисляем прибыль (Won = +0.8, Lost = -1, Void = 0)
            profit = wins * 0.8 - losses * 1
            profit_str = f"+{profit:.2f}" if profit >= 0 else f"{profit:.2f}"
            
            stats_text = (
                f"📅 <b>{current_month_name}</b>\n\n"
                f"💰 {profit_str} флэтов 📈 {win_rate}% WR\n\n"
                f"🎯 {total_matches} матчей\n"
                f"{wins}W / {losses}L / {voids}D"
            )
            return stats_text
        else:
            return f"📅 <b>{current_month_name}</b>\n\nДанных в базе нет."
    except Exception as e:
        print(f"[DB] Ошибка при получении статистики за месяц: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_profit_graph():
    """
    Генерирует график прибыли по датам матчей.
    Прибыль считается: Won = +0.8, Lost = -1, Void = 0
    Группирует данные по дням (точка - это конечный профит за день).
    
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
        
        # Подготавливаем данные для графика, группируя по дням
        daily_profit = {}  # date -> profit_sum
        current_profit = 0
        
        for match_date, result in results:
            try:
                # Парсим дату в формате YYYY-MM-DD (как сохраняется в БД)
                if isinstance(match_date, str):
                    date_obj = datetime.strptime(match_date, '%Y-%m-%d').date()
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
                daily_profit[date_obj] = current_profit
                
            except Exception as e:
                print(f"[GRAPH] Ошибка при обработке матча {match_date}: {e}")
                continue
        
        if not daily_profit:
            return None
        
        # Сортируем по датам и создаем списки для графика
        sorted_dates = sorted(daily_profit.keys())
        dates = [datetime.combine(d, datetime.min.time()) for d in sorted_dates]
        cumulative_profit = [daily_profit[d] for d in sorted_dates]
        
        # Создаем график с зеленым фоном
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#2b7f63')
        ax.set_facecolor('#2b7f63')
        
        # Рисуем линию графика (белая, толстая, без точек)
        ax.plot(dates, cumulative_profit, linewidth=3, color='white')
        
        # Форматирование оси X (ММ.ГГ)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45, ha='right', color='white', fontsize=13, fontweight='bold')
        for label in ax.get_xticklabels():
            label.set_fontweight('bold')
        
        # Форматирование оси Y
        ax.tick_params(axis='y', labelcolor='white', labelsize=13, width=2)
        for label in ax.get_yticklabels():
            label.set_fontweight('bold')
        
        # Добавляем сетку
        ax.grid(True, alpha=0.2, color='white')
        # Убирем подписи осей и заголовок
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_title('')
        
        # Добавляем нулевую линию (еле видная)
        ax.axhline(y=0, color='white', linestyle='--', linewidth=1, alpha=0.3)
        
        # Изменяем цвет и толщину границ графика
        ax.spines['bottom'].set_color('white')
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_color('white')
        ax.spines['left'].set_linewidth(2)
        ax.spines['top'].set_color('#2b7f63')
        ax.spines['right'].set_color('#2b7f63')
        
        # Плотный layout
        plt.tight_layout()
        
        # Сохраняем в BytesIO
        image_bytes = BytesIO()
        plt.savefig(image_bytes, format='png', dpi=100, bbox_inches='tight', facecolor='#2b7f63')
        plt.close()
        
        image_bytes.seek(0)
        return image_bytes
        
    except Exception as e:
        print(f"[DB] Ошибка при генерации графика прибыли: {e}")
        return None


def get_total_profit():
    """
    Рассчитывает итоговую прибыль по всем матчам в базе данных.
    Прибыль считается: Won = +0.8, Lost = -1, Void = 0
    
    Returns:
        str: отформатированный текст с итоговой прибылью
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        query = """
        SELECT
            SUM(CASE WHEN result = 'Won' THEN 0.8 
                     WHEN result = 'Lost' THEN -1 
                     WHEN result = 'Void' THEN 0 
                     ELSE 0 END) AS total_profit
        FROM matches
        """
        
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            total_profit = result[0] or 0
            # Округляем до сотых и форматируем
            total_profit = round(total_profit, 2)
            profit_str = f"+{total_profit}" if total_profit >= 0 else f"{total_profit}"
            
            return f"🔥 {profit_str} флетов"
        else:
            return "❓ 0.00 флетов"
    except Exception as e:
        print(f"[DB] Ошибка при расчете итоговой прибыли: {e}")
        return f"❌ Ошибка при расчете прибыли: {e}"

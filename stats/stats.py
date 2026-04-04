"""
Сервис получения статистики матчей из БД.
Функции для расчёта и форматирования статистики по лигам и в целом.
"""
from database.database import get_db_conn
import matplotlib
matplotlib.use('Agg')  # Использовать неинтерактивный backend для избежания Tkinter ошибок
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime, timedelta


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
                f"📚 <b>SUMMARY</b>\n\n"
                f"💰 {roi}% ROI 📈 {win_rate}% WR\n\n"
                f"<b>{total_matches} matches</b> ({wins}W / {losses}L / {voids}D)"
            )
            return stats_text
        else:
            return "📚 <b>SUMMARY</b>\n\nNo data available."
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
            stats_text = "🏆 <b>TOP LEAGUES</b>\n\n"
            emojis = ['1️⃣', '2️⃣', '3️⃣']
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
                
                emoji = emojis[idx - 1] if idx - 1 < len(emojis) else str(idx)
                stats_text += (
                    f"{emoji} <b>{league}</b>\n"
                    f"{wins}W / {losses}L / {voids}D — {win_rate}%\n\n"
                )
            return stats_text.rstrip()
        else:
            return "🏆 <b>TOP LEAGUES</b>\n\nNo data available."
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
            stats_text = "⛔️ <b>WORST LEAGUES</b>\n\n"
            emojis = ['1️⃣', '2️⃣', '3️⃣']
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
                
                emoji = emojis[idx - 1] if idx - 1 < len(emojis) else str(idx)
                stats_text += (
                    f"{emoji} <b>{league}</b>\n"
                    f"{wins}W / {losses}L / {voids}D — {win_rate}%\n\n"
                )
            return stats_text.rstrip()
        else:
            return "📉 <b>Worst Leagues</b>\n\nNo data available."
    except Exception as e:
        print(f"[DB] Ошибка при получении худших лиг: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_last_5_matches():
    """
    Получает последние 5 матчей из БД для вывода в Telegram с inline-кнопками.
    
    Returns:
        tuple: (текст для вывода, список данных матчей)
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        query = """
        SELECT 
            id,
            league,
            home_team,
            away_team,
            prediction,
            final_score,
            result,
            date,
            link,
            odds
        FROM matches
        ORDER BY id DESC
        LIMIT 5
        """
        
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if results:
            matches_data = []
            stats_text = ""  # Пустой текст - только кнопки
            
            for match_id, league, home_team, away_team, prediction, final_score, result, match_date, link, odds in results:
                # Подготавливаем значения, заменяя пустые на "?"
                home_team = home_team or "?"
                away_team = away_team or "?"
                
                # Форматируем результат только смайликом
                if result == 'Won':
                    result_emoji = "✅"
                elif result == 'Lost':
                    result_emoji = "❌"
                elif result == 'Void':
                    result_emoji = "🔁"
                else:
                    result_emoji = "?"
                
                # Сохраняем полные данные для inline-кнопок
                matches_data.append({
                    'id': match_id,
                    'league': league or "?",
                    'home_team': home_team,
                    'away_team': away_team,
                    'prediction': prediction or "?",
                    'final_score': final_score or "?",
                    'result': result or "?",
                    'result_emoji': result_emoji,
                    'date': match_date,
                    'link': link or "#",
                    'odds': odds
                })
            
            return stats_text, matches_data
        else:
            return "", []
    except Exception as e:
        print(f"[DB] Ошибка при получении последних матчей: {e}")
        return "", []


def get_match_details_by_id(match_id):
    """
    Получает подробную информацию о конкретном матче по ID.
    
    Args:
        match_id: ID матча в БД
        
    Returns:
        dict: информация о матче или None если не найден
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
            link,
            odds
        FROM matches
        WHERE id = %s
        """
        
        cur.execute(query, (match_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            league, home_team, away_team, prediction, final_score, result_status, match_date, link, odds = result
            
            # Преобразуем дату
            if match_date:
                try:
                    if isinstance(match_date, str):
                        date_obj = datetime.strptime(match_date, '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%d.%m.%y')
                    else:
                        formatted_date = match_date.strftime('%d.%m.%y')
                except Exception as e:
                    print(f"[STATS] Ошибка при преобразовании даты {match_date}: {e}")
                    formatted_date = "?"
            else:
                formatted_date = "?"
            
            # Форматируем результат смайликом
            if result_status == 'Won':
                result_emoji = "✅"
            elif result_status == 'Lost':
                result_emoji = "❌"
            elif result_status == 'Void':
                result_emoji = "🔁"
            else:
                result_emoji = "?"
            
            return {
                'emoji': result_emoji,
                'league': league or "?",
                'home_team': home_team or "?",
                'away_team': away_team or "?",
                'prediction': prediction or "?",
                'final_score': final_score or "?",
                'date': formatted_date,
                'link': link or "#",
                'odds': odds
            }
        else:
            return None
    except Exception as e:
        print(f"[DB] Ошибка при получении деталей матча: {e}")
        return None


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
            1: "JANUARY", 2: "FEBRUARY", 3: "MARCH", 4: "APRIL",
            5: "MAY", 6: "JUNE", 7: "JULY", 8: "AUGUST",
            9: "SEPTEMBER", 10: "OCTOBER", 11: "NOVEMBER", 12: "DECEMBER"
        }
        current_month_name = month_names.get(current_month, "UNKNOWN MONTH")
        
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
                f"💰 {profit_str} units 📈 {win_rate}% WR\n\n"
                f"🎯 <b>{total_matches} matches</b>\n"
                f"{wins}W / {losses}L / {voids}D"
            )
            return stats_text
        else:
            return f"📅 <b>{current_month_name}</b>\n\nNo data available."
    except Exception as e:
        print(f"[DB] Ошибка при получении статистики за месяц: {e}")
        return f"❌ Ошибка при получении статистики: {e}"


def get_profit_graph():
    """
    Генерирует график прибыли по датам матчей используя Seaborn + Matplotlib.
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
        dates = sorted_dates
        cumulative_profit = [daily_profit[d] for d in sorted_dates]
        
        # Определяем деления по Y кратные пяти (5, 10, 15, 20, 25) - ровно 5 делений
        max_profit = max(cumulative_profit)
        
        # Фиксированная сетка: всегда 5 делений по 5
        y_ticks_display = [5, 10, 15, 20, 25]
        
        # Вычисляем максимум для отображения - минимум 25, или выше если график больше
        y_max_display = max(25, max_profit + abs(max_profit) * 0.1) if max_profit > 0 else 25 + 2.5
        y_min_display = 0  # Ноль всегда в основании
        
        # Подготавливаем ticktext
        y_ticktext = [f'{int(y)}' for y in y_ticks_display]
        
        # Добавляем отступ для X оси (слева и справа от графика)
        date_range = (dates[-1] - dates[0]).days
        x_padding_days = date_range * 0.10  # 10% отступ
        x_min = dates[0] - timedelta(days=x_padding_days)
        x_max = dates[-1] + timedelta(days=x_padding_days)
        
        # Формируем список всех месяцев, которые есть в данных, по порядку
        month_names_en = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

        x_ticks_dates = []
        seen_months = set()
        for d in dates:
            month_key = (d.year, d.month)
            if month_key not in seen_months:
                seen_months.add(month_key)
                x_ticks_dates.append(d)

        x_ticktext_months = [month_names_en.get(d.month, "") for d in x_ticks_dates]
        
        # Цвета осей
        color_y_axis = '#316650'  # Синий/Индиго для Units (Y)
        color_x_axis = '#AB4E52'  # Лиловый для Date (X)
        
        # Создаем фигуру Matplotlib - уменьшенная площадь для большего места осям
        fig, ax = plt.subplots(figsize=(8.5, 5), dpi=100)
        
        # Устанавливаем стиль Seaborn - darkgrid
        sns.set_style("darkgrid")
        
        # Рисуем линию графика (темно-зеленая, более толстая)
        ax.plot(dates, cumulative_profit, color="#1A4780", linewidth=3, zorder=2)
        
        # Добавляем точки в начале и в конце графика
        ax.plot(dates[0], cumulative_profit[0], 'o', color='#1A4780', markersize=6, zorder=3)
        ax.plot(dates[-1], cumulative_profit[-1], 'o', color='#1A4780', markersize=6, zorder=3)
        
        # Настраиваем сетку - белая, увеличенная для стиля poster
        ax.grid(True, alpha=1.0, color='#FFFFFF', linewidth=1.7)
        ax.set_axisbelow(True)
        
        # Настраиваем фон - светло-серый
        bg_color = "#EAEAF2"
        ax.set_facecolor(bg_color)
        fig.patch.set_facecolor('white')
        
        # Настраиваем X ось - белая (невидимая)
        ax.set_xlim(x_min, x_max)
        ax.set_xticks(x_ticks_dates)
        ax.set_xticklabels(x_ticktext_months, fontsize=12, fontfamily='Segoe UI', color=color_x_axis)
        ax.spines['bottom'].set_color('white')
        ax.spines['bottom'].set_linewidth(0)
        ax.tick_params(axis='x', pad=12, length=0, width=0, color='white', labelcolor=color_x_axis)
        
        # Настраиваем Y ось - белая (невидимая)
        ax.set_ylim(y_min_display, y_max_display)
        ax.set_yticks(y_ticks_display)
        # Цвет чисел на оси Y - синий
        ax.set_yticklabels(y_ticktext, fontsize=12, fontfamily='Arial', color=color_y_axis)
        ax.spines['left'].set_color('white')
        ax.spines['left'].set_linewidth(0)
        ax.tick_params(axis='y', pad=12, length=0, width=0, color='white', labelcolor=color_y_axis)
        
        # Убираем верхнюю и правую границы
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Удаляем заголовок осей
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # Добавляем отступы - увеличены для большего места осям
        fig.subplots_adjust(left=0.14, right=0.92, top=0.95, bottom=0.18)
        
        # Добавляем аннотации для осей ВНУТРИ графика
        # Units - левая верхняя часть
        ax.text(0.02, 0.98, '■ Units', fontsize=16, fontfamily='Arial', weight='bold', 
                color=color_y_axis, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
        
        # Date - правая нижняя часть
        ax.text(0.98, 0.02, '■ Date', fontsize=16, fontfamily='Arial', weight='bold',
                color=color_x_axis, transform=ax.transAxes, verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
        
        # Сохраняем в BytesIO как PNG
        image_bytes = BytesIO()
        fig.savefig(image_bytes, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        image_bytes.seek(0)
        plt.close(fig)
        return image_bytes
    except Exception as e:
        print(f"[DB] Ошибка при генерации графика прибыли: {e}")
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
            
            return f"<b>Total: {profit_str} units</b>"
        else:
            return "❓ 0 units"
    except Exception as e:
        print(f"[DB] Ошибка при расчете итоговой прибыли: {e}")
        return f"❌ Ошибка при расчете прибыли: {e}"

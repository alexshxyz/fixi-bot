"""
Сервис получения статистики матчей из БД.
Функции для расчёта и форматирования статистики по лигам и в целом.
"""
from database.database import get_db_conn
import plotly.graph_objects as go
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
            return "⚡️ LAST 5\n\nNo data available."
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
    Генерирует график прибыли по датам матчей используя Plotly.
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
        
        # Определяем деления по Y кратные трем с учетом нуля (0, 3, 6, 9, 12...)
        min_profit = min(cumulative_profit)
        max_profit = max(cumulative_profit)
        
        # Находим диапазон в делениях по 3
        y_min_ticks = int(min_profit // 3)
        if min_profit % 3 != 0 and min_profit < 0:
            y_min_ticks -= 1
        
        y_max_ticks = int(max_profit // 3)
        if max_profit % 3 != 0 and max_profit > 0:
            y_max_ticks += 1
        
        # Создаем список всех делений кратных 3
        all_y_ticks = [i * 3 for i in range(y_min_ticks, y_max_ticks + 1)]
        
        # Убеждаемся, что ноль в списке
        if 0 not in all_y_ticks:
            all_y_ticks.append(0)
        all_y_ticks = sorted(all_y_ticks)
        
        # Берем деления для отображения (примерно 4-5 делений)
        step = max(1, len(all_y_ticks) // 4)
        y_ticks_display = all_y_ticks[::step]
        if all_y_ticks[-1] not in y_ticks_display:
            y_ticks_display.append(all_y_ticks[-1])
        
        # Добавляем отступ для лучшего отображения (ноль в основании)
        # Находим максимальное значение для расчета отступа сверху
        y_max_tick = max(all_y_ticks) if all_y_ticks else max_profit
        y_max_display = y_max_tick + abs(y_max_tick) * 0.1
        y_min_display = 0  # Ноль всегда в основании
        
        # Подготавливаем ticktext - исключаем ноль полностью из видимых делений
        y_ticks_display_filtered = [y for y in y_ticks_display if y != 0]
        y_ticktext = [f'{int(y)}' for y in y_ticks_display_filtered]
        
        # Добавляем отступ для X оси (слева от графика)
        date_range = (dates[-1] - dates[0]).days
        x_padding_days = date_range * 0.05  # 5% отступ
        x_min = dates[0] - timedelta(days=x_padding_days)
        x_max = dates[-1] + timedelta(days=x_padding_days)
        
        # Вычисляем ровно 4 даты для оси X
        x_ticks_dates = [
            dates[0],
            dates[len(dates) // 3],
            dates[2 * len(dates) // 3],
            dates[-1]
        ]
        # Удаляем дубликаты, если дат очень мало
        x_ticks_dates = list(dict.fromkeys(x_ticks_dates))
        
        # Создаем фигуру plotly
        fig = go.Figure()
        
        # Добавляем линию графика (темно-зеленая, более толстая)
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_profit,
            mode='lines',
            line=dict(color='#1b5a3f', width=5),
            hovertemplate='<b>%{x|%d.%m.%y}</b><br>Прибыль: %{y:.2f}<extra></extra>'
        ))
        
        # Обновляем layout с размерами ближе к скриншоту
        fig.update_layout(
            # Размеры - более компактные
            width=900,
            height=500,
            # Цвета в целом
            plot_bgcolor='white',
            paper_bgcolor='white',
            # Убираем заголовок
            title='',
            # Убираем легенду
            showlegend=False,
            # Шрифты
            font=dict(color='black', size=13),
            # Отступы - увеличиваем справа и слева
            margin=dict(l=80, r=80, t=30, b=80),
            # Оси
            xaxis=dict(
                title='<b>Date</b>',
                title_font=dict(size=15, color='black'),
                showgrid=True,
                gridwidth=1,
                gridcolor='#e0e0e0',
                showline=True,
                linewidth=3,
                linecolor='black',
                mirror=False,
                # Показываем ровно 4 даты на оси X
                tickvals=x_ticks_dates,
                tickformat='%d.%m.%y',
                tickangle=0,
                ticks='outside',
                tickwidth=2,
                ticklen=5,
                tickfont=dict(size=13),
                # Добавляем отступ слева и справа от графика
                range=[x_min, x_max]
            ),
            yaxis=dict(
                title='<b>Units</b>',
                title_font=dict(size=15, color='black'),
                showgrid=True,
                gridwidth=2,
                gridcolor='#d4d4d4',
                showline=True,
                linewidth=3,
                linecolor='black',
                mirror=False,
                # Устанавливаем деления кратные трем (без нуля)
                tickvals=y_ticks_display_filtered,
                ticktext=y_ticktext,
                ticks='outside',
                tickwidth=2,
                ticklen=5,
                tickfont=dict(size=13),
                range=[y_min_display, y_max_display]
            ),
            hovermode='x unified'
        )
        
        # Сохраняем в BytesIO как PNG
        image_bytes = BytesIO()
        image_data = fig.to_image(format='png', width=900, height=500)
        image_bytes.write(image_data)
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
            
            return f"<b>Total: {profit_str} units</b>"
        else:
            return "❓ 0 units"
    except Exception as e:
        print(f"[DB] Ошибка при расчете итоговой прибыли: {e}")
        return f"❌ Ошибка при расчете прибыли: {e}"

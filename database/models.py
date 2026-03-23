"""
Модели данных для парсера матчей.
Классы Match и MetaMatch для представления матчей и управления коллекцией.
"""
from core.config import RATE


class MetaMatch(type):
    """
    Метаклас для Match, предоставляющий доступ к коллекции всех объектов Match.
    """
    @property
    def objects(cls):
        """
        Возвращает список всех созданных объектов Match.
        
        Returns:
            list: список всех инстансов Match
        """
        return cls._objects


class Match(object, metaclass=MetaMatch):
    """
    Представляет матч с коэффициентами и информацией о триггере.
    
    Используется для хранения информации о матчах, обнаруженных парсером,
    и отправки их в Telegram.
    
    Attributes:
        liga: название лиги
        first_team: имя первой команды
        second_team: имя второй команды
        first_team_score: счёт первой команды
        second_team_score: счёт второй команды
        goals: Over/Under значение или handicap текст
        over_half: коэффициент Over для первого тайма (HT)
        over_full: коэффициент Over для полного матча (FT)
        over: выбранный Over (для обратной совместимости)
        tab: табель (HT/FT)
        url: ссылка на матч на NowGoal
        chosen_kind: тип триггера (half, full, ah_half, ah_full)
        chosen_over: коэффициент, который триггернул уведомление
    """
    _objects = []

    def __init__(self, liga, first_team, second_team, first_team_score, second_team_score,
                 goals, over=None, tab=None, url=None, over_half=None, over_full=None,
                 chosen_kind=None, chosen_over=None):
        """
        Инициализация объекта Match.
        
        Args:
            liga: название лиги
            first_team: имя первой команды
            second_team: имя второй команды
            first_team_score: счёт первой команды
            second_team_score: счёт второй команды
            goals: Over/Under значение или handicap текст
            over: одиночный коэффициент Over (для обратной совместимости)
            tab: табель (HT/FT)
            url: ссылка на матч
            over_half: коэффициент Over для HT
            over_full: коэффициент Over для FT
            chosen_kind: тип триггера
            chosen_over: коэффициент, который триггернул
        """
        self.liga = liga
        self.first_team = first_team
        self.second_team = second_team
        self.first_team_score = first_team_score
        self.second_team_score = second_team_score
        self.goals = goals
        
        # backward-compatible single over value: prefer full, then half, then explicit over
        self.over_half = over_half
        self.over_full = over_full
        self.over = over_full if over_full is not None else (over_half if over_half is not None else over)
        
        self.tab = tab
        self.url = url
        self.chosen_kind = chosen_kind
        self.chosen_over = chosen_over
        
        # Логируем созданный объект с ПОЛНОЙ информацией
        print(f"[MATCH_OBJECT] ✓ Created Match:")
        print(f"[MATCH_OBJECT]   liga='{liga}'")
        print(f"[MATCH_OBJECT]   first_team='{first_team}', first_score='{first_team_score}'")
        print(f"[MATCH_OBJECT]   second_team='{second_team}', second_score='{second_team_score}'")
        print(f"[MATCH_OBJECT]   goals='{goals}'")
        print(f"[MATCH_OBJECT]   tab='{tab}'")
        print(f"[MATCH_OBJECT]   url='{url}'")
        print(f"[MATCH_OBJECT]   kind='{chosen_kind}'")
        print(f"[MATCH_OBJECT] Будет отправлено: '{first_team}' {first_team_score} - {second_team_score} '{second_team}'")
        
        # добавляем инстанс в коллекцию
        self.__class__._objects.append(self)

    def __str__(self):
        """
        Форматирует матч в HTML текст для отправки в Telegram.
        
        Returns:
            str: HTML-formatted сообщение о матче
            
        Logic:
            - Если chosen_kind начинается с 'ah_' → показываем Handicap
            - Иначе → показываем Over
            - Коэффициенты показываются как (value + 1.0)
            - Если chosen_over задан → используем его
            - Иначе выбираем из over_half/over_full по RATE
        """
        # Убеждаемся что счет передается (даже если пусто)
        # Обворачиваем названия команд в гиперссылку на matч
        score_line = f"<a href=\"{self.url}\"><b>{self.first_team} {self.first_team_score} - {self.second_team_score} {self.second_team}</b></a>"
        if not self.first_team_score and not self.second_team_score:
            print(f"[MATCH_STR] ⚠ Счет пуст! teams='{self.first_team}' vs '{self.second_team}'")
        
        parts = [f"⭐️ <b>Crown</b>", f"{self.liga}", score_line]

        # If this match was triggered by Asian Handicap (chosen_kind starts with 'ah_'),
        # render Handicap line instead of Over.
        if isinstance(self.chosen_kind, str) and self.chosen_kind.startswith('ah_'):
            # self.goals for AH messages contains the handicap text (e.g. "0/0.5")
            parts.append(f"<b>Handicap {self.goals} {self.tab}</b>")
        else:
            parts.append(f"<b>Over {self.goals} {self.tab}</b>")

        # helper: display numeric odds + 1 for telegram
        def _fmt_add_one(x):
            try:
                v = float(x)
                # Коэффициент всегда положительный, просто добавляем 1
                v2 = v + 1.0
                # remove trailing zeros
                if float(int(v2)) == v2:
                    return str(int(v2))
                return str(round(v2, 4))
            except Exception:
                return str(x)

        # если явно указано, что именно триггернуло — показываем это значение
        if self.chosen_over is not None:
            parts.append(f"Odds {_fmt_add_one(self.chosen_over)}")
        else:
            # попытка выбрать одно значение, которое прошло по порогу RATE
            chosen = None
            try:
                rate_val = float(RATE)
            except Exception:
                rate_val = RATE

            if self.over_full is not None and isinstance(self.over_full, (int, float)):
                if self.over_full <= rate_val:
                    chosen = self.over_full
            if chosen is None and self.over_half is not None and isinstance(self.over_half, (int, float)):
                if self.over_half <= rate_val:
                    chosen = self.over_half

            if chosen is not None:
                parts.append(f"Odds {_fmt_add_one(chosen)}")
            else:
                if self.over_half is not None or self.over_full is not None:
                    parts.append(f"Odds half={self.over_half} full={self.over_full}")
                else:
                    parts.append(f"Odds {round(1 + (self.over or 0), 4)}")
        
        # Логируем финальное сообщение с URL
        msg = "\n".join(parts)
        print(f"[MATCH_MESSAGE] Message:\n{msg}\nURL: {self.url}")
        return msg

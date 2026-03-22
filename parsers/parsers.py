"""
Парсер матчей и коэффициентов с сайта nowgoal.com

Главный модуль, экспортирует основные функции:
- parse_match(page, match_id): парсит один матч
- parse_all_matches(): собирает и парсит все матчи
"""

# Экспортируем основные функции из подмодулей
from .match_parser import parse_match
from .crawler import parse_all_matches

__all__ = ['parse_match', 'parse_all_matches']

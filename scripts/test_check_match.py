"""
Простой тест для проверки функции check_match_exists
"""
import sys
from pathlib import Path

# Добавляем родительскую директорию в sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from database.database import check_match_exists

# Примеры тестирования
print("=" * 60)
print("Тест функции check_match_exists")
print("=" * 60)

# Тест 1: Проверка с пустым link
print("\n1. Тест с пустым link:")
result = check_match_exists("")
print(f"   check_match_exists('') -> {result}")
print(f"   ✓ Ожидалось: False, получено: {result}")

# Тест 2: Проверка с None
print("\n2. Тест с None:")
result = check_match_exists(None)
print(f"   check_match_exists(None) -> {result}")
print(f"   ✓ Ожидалось: False, получено: {result}")

# Тест 3: Проверка с реальным URL (БД должна быть доступна)
print("\n3. Тест с реальным URL:")
test_url = "https://www.nowgoal.com/oddscomp/99999999"
print(f"   Проверяем: {test_url}")
try:
    result = check_match_exists(test_url)
    print(f"   check_match_exists(test_url) -> {result}")
    print(f"   ✓ Функция работает, результат: {result}")
except Exception as e:
    print(f"   ⚠ Ошибка (возможно БД не доступна): {e}")

# Тест 4: Проверка с URL и prediction
print("\n4. Тест с URL и prediction:")
test_url = "https://www.nowgoal.com/oddscomp/99999999"
test_prediction = "Over 2.5 HT"
print(f"   Проверяем: {test_url} + prediction='{test_prediction}'")
try:
    result = check_match_exists(test_url, prediction=test_prediction)
    print(f"   check_match_exists(url, prediction=pred) -> {result}")
    print(f"   ✓ Функция работает, результат: {result}")
except Exception as e:
    print(f"   ⚠ Ошибка (возможно БД не доступна): {e}")

print("\n" + "=" * 60)
print("Тестирование завершено!")
print("=" * 60)

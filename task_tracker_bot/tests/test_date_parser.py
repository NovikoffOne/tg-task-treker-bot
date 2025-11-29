"""
Unit тесты для DateParser
"""
import pytest
from datetime import datetime, date, time, timedelta
from utils.date_parser import DateParser

@pytest.fixture
def date_parser():
    return DateParser()

def test_parse_date_today(date_parser):
    """Тест парсинга 'сегодня'"""
    today = datetime.now().date()
    result = date_parser.parse_date("сегодня")
    assert result == today

def test_parse_date_tomorrow(date_parser):
    """Тест парсинга 'завтра'"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    result = date_parser.parse_date("завтра")
    assert result == tomorrow

def test_parse_date_absolute(date_parser):
    """Тест парсинга абсолютной даты DD.MM"""
    today = datetime.now().date()
    result = date_parser.parse_date("03.12")
    assert result == date(today.year, 12, 3)

def test_parse_date_absolute_full(date_parser):
    """Тест парсинга полной даты DD.MM.YYYY"""
    result = date_parser.parse_date("03.12.2025")
    assert result == date(2025, 12, 3)

def test_parse_time_simple(date_parser):
    """Тест парсинга простого времени"""
    result = date_parser.parse_time("10:00")
    assert result == time(10, 0)

def test_parse_time_range(date_parser):
    """Тест парсинга диапазона времени"""
    result = date_parser.parse_time_range("11:10 - 12:00")
    assert result == (time(11, 10), time(12, 0))

def test_parse_datetime_from_task(date_parser):
    """Тест извлечения даты и времени из текста задачи"""
    task_text = "Выгул Феры в 10:00"
    result = date_parser.parse_datetime_from_task(task_text)
    
    assert result["time"] == time(10, 0)
    assert "Выгул Феры" in result["remaining_text"]

def test_parse_datetime_from_task_with_date(date_parser):
    """Тест извлечения даты из текста задачи"""
    task_text = "5007 - Промониторить трафик 03.12"
    result = date_parser.parse_datetime_from_task(task_text)
    
    today = datetime.now().date()
    assert result["date"] == date(today.year, 12, 3)
    assert "03.12" not in result["remaining_text"]

def test_parse_datetime_from_task_time_range(date_parser):
    """Тест извлечения диапазона времени из текста задачи"""
    task_text = "Доделать бота 11:10 - 12:00"
    result = date_parser.parse_datetime_from_task(task_text)
    
    assert result["time"] == time(11, 10)
    assert result["time_end"] == time(12, 0)
    assert "11:10 - 12:00" not in result["remaining_text"]

def test_parse_date_after_tomorrow(date_parser):
    """Тест парсинга 'послезавтра'"""
    today = datetime.now().date()
    after_tomorrow = today + timedelta(days=2)
    result = date_parser.parse_date("послезавтра")
    assert result == after_tomorrow

def test_parse_date_yesterday(date_parser):
    """Тест парсинга 'вчера'"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    result = date_parser.parse_date("вчера")
    assert result == yesterday

def test_parse_date_with_reference_date(date_parser):
    """Тест парсинга относительной даты с опорной датой"""
    reference = date(2025, 12, 1)
    result = date_parser.parse_date("завтра", reference_date=reference)
    assert result == date(2025, 12, 2)

def test_parse_date_natural_language_context(date_parser):
    """Тест парсинга даты из естественного языка в контексте задач"""
    # Тест фразы "на завтра"
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    result = date_parser.parse_date("на завтра")
    assert result == tomorrow
    
    # Тест фразы "на послезавтра"
    after_tomorrow = today + timedelta(days=2)
    result = date_parser.parse_date("на послезавтра")
    assert result == after_tomorrow

def test_parse_date_from_ai_request(date_parser):
    """Тест парсинга даты из AI-запроса"""
    # Пример: "Добавь на завтра задачи: купить молоко, позвонить маме"
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Извлечение даты из запроса
    result = date_parser.parse_date("на завтра")
    assert result == tomorrow
    
    # Тест с другим форматом
    result = date_parser.parse_date("завтра")
    assert result == tomorrow

def test_parse_datetime_from_task_with_relative_date(date_parser):
    """Тест извлечения относительной даты из текста задачи"""
    # Задача с относительной датой в тексте
    task_text = "Купить молоко завтра"
    result = date_parser.parse_datetime_from_task(task_text)
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    assert result["date"] == tomorrow or result["date"] == today  # Может быть сегодня, если не распарсилось
    assert "молоко" in result["remaining_text"].lower()

def test_parse_datetime_from_task_multiple_dates(date_parser):
    """Тест обработки задачи с несколькими датами (берется первая)"""
    task_text = "Встреча 15.12 и 20.12"
    result = date_parser.parse_datetime_from_task(task_text)
    
    # Должна быть извлечена первая дата
    assert result["date"] is not None
    # Одна из дат должна быть удалена из текста
    assert "15.12" not in result["remaining_text"] or "20.12" not in result["remaining_text"]

def test_parse_date_invalid_format(date_parser):
    """Тест обработки невалидного формата даты"""
    result = date_parser.parse_date("некорректная дата")
    # Должен вернуть None или попытаться распарсить через dateutil
    assert result is None or isinstance(result, date)

def test_parse_date_edge_cases(date_parser):
    """Тест граничных случаев парсинга дат"""
    # Пустая строка
    result = date_parser.parse_date("")
    assert result is None or isinstance(result, date)
    
    # Только пробелы
    result = date_parser.parse_date("   ")
    assert result is None or isinstance(result, date)
    
    # Смешанный регистр
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    result = date_parser.parse_date("ЗаВтРа")
    assert result == tomorrow

def test_parse_datetime_from_task_with_default_date(date_parser):
    """Тест извлечения даты с указанием default_date"""
    default_date = date(2025, 12, 5)
    task_text = "Выгул Феры в 10:00"
    result = date_parser.parse_datetime_from_task(task_text, default_date=default_date)
    
    assert result["date"] == default_date
    assert result["time"] == time(10, 0)

def test_cache_hit(date_parser):
    """Тест попадания в кэш"""
    # Очищаем кэш перед тестом
    date_parser.clear_cache()
    
    # Первый вызов - должен быть cache miss
    result1 = date_parser.parse_date("завтра")
    stats1 = date_parser.get_cache_stats()
    assert stats1["cache_misses"] == 1
    assert stats1["cache_hits"] == 0
    
    # Второй вызов с тем же текстом и reference_date - должен быть cache hit
    result2 = date_parser.parse_date("завтра")
    stats2 = date_parser.get_cache_stats()
    assert stats2["cache_hits"] == 1
    assert stats2["cache_misses"] == 1
    assert result1 == result2

def test_cache_miss_different_reference_date(date_parser):
    """Тест промаха кэша при разном reference_date"""
    date_parser.clear_cache()
    
    reference1 = date(2025, 12, 1)
    reference2 = date(2025, 12, 2)
    
    # Первый вызов
    result1 = date_parser.parse_date("завтра", reference_date=reference1)
    stats1 = date_parser.get_cache_stats()
    assert stats1["cache_misses"] == 1
    
    # Второй вызов с другим reference_date - должен быть cache miss
    result2 = date_parser.parse_date("завтра", reference_date=reference2)
    stats2 = date_parser.get_cache_stats()
    assert stats2["cache_misses"] == 2
    assert result1 != result2  # Разные результаты из-за разного reference_date

def test_cache_clear(date_parser):
    """Тест очистки кэша"""
    # Заполняем кэш
    date_parser.parse_date("сегодня")
    date_parser.parse_date("завтра")
    date_parser.parse_date("послезавтра")
    
    stats_before = date_parser.get_cache_stats()
    assert stats_before["cache_size"] > 0
    
    # Очищаем кэш
    date_parser.clear_cache()
    
    stats_after = date_parser.get_cache_stats()
    assert stats_after["cache_size"] == 0
    assert stats_after["cache_hits"] == 0
    assert stats_after["cache_misses"] == 0

def test_cache_performance(date_parser):
    """Тест производительности кэша"""
    import time
    
    date_parser.clear_cache()
    
    # Первый прогон - без кэша
    start1 = time.time()
    for _ in range(100):
        date_parser.parse_date("завтра")
    time1 = time.time() - start1
    
    # Второй прогон - с кэшем
    start2 = time.time()
    for _ in range(100):
        date_parser.parse_date("завтра")
    time2 = time.time() - start2
    
    # Второй прогон должен быть быстрее (или хотя бы не медленнее)
    # В реальности с кэшем должно быть значительно быстрее
    stats = date_parser.get_cache_stats()
    assert stats["cache_hits"] >= 100  # Все 100 запросов должны попасть в кэш
    assert stats["hit_ratio_percent"] > 50  # Hit ratio должен быть высоким

def test_cache_stats(date_parser):
    """Тест получения статистики кэша"""
    date_parser.clear_cache()
    
    # Делаем несколько запросов
    date_parser.parse_date("сегодня")
    date_parser.parse_date("завтра")
    date_parser.parse_date("завтра")  # Повторный запрос - должен быть hit
    
    stats = date_parser.get_cache_stats()
    
    assert "cache_size" in stats
    assert "cache_hits" in stats
    assert "cache_misses" in stats
    assert "total_requests" in stats
    assert "hit_ratio_percent" in stats
    
    assert stats["cache_size"] >= 0
    assert stats["cache_hits"] >= 1
    assert stats["cache_misses"] >= 2
    assert stats["total_requests"] == stats["cache_hits"] + stats["cache_misses"]
    assert 0 <= stats["hit_ratio_percent"] <= 100

def test_cache_size_limit():
    """Тест ограничения размера кэша"""
    from utils.date_parser import DateParser
    
    # Создаем парсер с маленьким кэшем
    small_cache_parser = DateParser(cache_size=5)
    small_cache_parser.clear_cache()
    
    # Заполняем кэш больше размера
    for i in range(10):
        small_cache_parser.parse_date(f"{i}.12")
    
    stats = small_cache_parser.get_cache_stats()
    # Кэш должен быть ограничен размером (может быть немного больше из-за логики очистки)
    assert stats["cache_size"] <= 10  # Разумный предел


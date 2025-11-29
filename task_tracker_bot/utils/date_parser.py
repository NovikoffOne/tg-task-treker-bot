"""
Парсер дат и времени для Todo List
"""
import re
import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, Dict, Any
from functools import lru_cache
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

class DateParser:
    """Парсинг дат и времени из естественного языка"""
    
    # Паттерны для времени
    TIME_PATTERN = r'(\d{1,2}):(\d{2})'
    TIME_RANGE_PATTERN = r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})'
    
    def __init__(self, default_timezone='Europe/Moscow', cache_size=128):
        self.default_timezone = default_timezone
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0
        # Кэш для parse_date с учетом reference_date
        self._date_cache = {}
    
    def parse_date(self, text: str, reference_date: Optional[date] = None) -> Optional[date]:
        """
        Парсит дату из текста с кэшированием результатов
        
        Поддерживаемые форматы:
        - "сегодня" → текущая дата
        - "завтра" → текущая дата + 1 день
        - "послезавтра" → текущая дата + 2 дня
        - "вчера" → текущая дата - 1 день
        - "DD.MM" → дата в текущем году
        - "DD.MM.YYYY" → конкретная дата
        
        Args:
            text: Текст с датой
            reference_date: Опорная дата (по умолчанию сегодня)
        
        Returns:
            date объект или None
        """
        if not reference_date:
            reference_date = datetime.now().date()
        
        text_lower = text.lower().strip()
        
        # Удаление предлогов для более естественного парсинга
        # Поддерживаемые предлоги: "на", "в", "к"
        prepositions = ['на', 'в', 'к']
        for prep in prepositions:
            if text_lower.startswith(prep + ' '):
                text_lower = text_lower[len(prep):].strip()
                break
        
        # Проверка кэша (ключ: (text_lower, reference_date))
        cache_key = (text_lower, reference_date)
        if cache_key in self._date_cache:
            self._cache_hits += 1
            cached_result = self._date_cache[cache_key]
            logger.debug(f"Кэш HIT для даты '{text}' с reference_date={reference_date} → {cached_result}")
            return cached_result
        
        self._cache_misses += 1
        logger.debug(f"Кэш MISS для даты '{text}' с reference_date={reference_date}")
        
        result = None
        
        # Проверка относительных дат
        if text_lower == 'сегодня':
            result = reference_date
            logger.debug(f"Парсинг даты '{text}' → {result} (относительная дата)")
        elif text_lower == 'завтра':
            result = reference_date + timedelta(days=1)
            logger.debug(f"Парсинг даты '{text}' → {result} (относительная дата)")
        elif text_lower == 'послезавтра':
            result = reference_date + timedelta(days=2)
            logger.debug(f"Парсинг даты '{text}' → {result} (относительная дата)")
        elif text_lower == 'вчера':
            result = reference_date - timedelta(days=1)
            logger.debug(f"Парсинг даты '{text}' → {result} (относительная дата)")
        
        # Проверка формата DD.MM или DD.MM.YYYY
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', text)
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else reference_date.year
            
            try:
                result = date(year, month, day)
                logger.debug(f"Парсинг даты '{text}' → {result} (абсолютная дата DD.MM или DD.MM.YYYY)")
            except ValueError:
                logger.warning(f"Некорректная дата: {day}.{month}.{year} из текста '{text}'")
                result = None
        
        # Попытка парсинга через dateutil (только если еще не распарсили)
        if result is None:
            try:
                parsed = dateutil_parser.parse(text, default=datetime.combine(reference_date, time()))
                result = parsed.date()
                logger.debug(f"Парсинг даты '{text}' → {result} (через dateutil)")
            except (ValueError, TypeError) as e:
                logger.warning(f"Не удалось распарсить дату: '{text}' (ошибка: {e})")
                result = None
        
        # Сохранение в кэш (только если результат успешный)
        if result is not None:
            # Очистка кэша, если он слишком большой
            if len(self._date_cache) >= self._cache_size:
                # Удаляем 25% самых старых записей
                items_to_remove = len(self._date_cache) // 4
                keys_to_remove = list(self._date_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self._date_cache[key]
                logger.debug(f"Очистка кэша: удалено {items_to_remove} записей")
            
            self._date_cache[cache_key] = result
        
        return result
    
    def parse_time(self, text: str) -> Optional[time]:
        """
        Парсит время из текста
        
        Поддерживаемые форматы:
        - "HH:MM" → одно время
        
        Args:
            text: Текст с временем (формат HH:MM)
        
        Returns:
            time объект или None
        """
        time_match = re.search(self.TIME_PATTERN, text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            if 0 <= hour < 24 and 0 <= minute < 60:
                result = time(hour, minute)
                logger.debug(f"Парсинг времени '{text}' → {result}")
                return result
            else:
                logger.warning(f"Некорректное время: {hour}:{minute} из текста '{text}'")
                return None
        
        logger.debug(f"Не удалось распарсить время из текста '{text}'")
        return None
    
    def parse_time_range(self, text: str) -> Optional[Tuple[time, time]]:
        """
        Парсит диапазон времени
        
        Args:
            text: Текст с диапазоном (формат HH:MM - HH:MM)
        
        Returns:
            Кортеж (start_time, end_time) или None
        """
        range_match = re.search(self.TIME_RANGE_PATTERN, text)
        if range_match:
            start_hour = int(range_match.group(1))
            start_min = int(range_match.group(2))
            end_hour = int(range_match.group(3))
            end_min = int(range_match.group(4))
            
            try:
                start_time = time(start_hour, start_min)
                end_time = time(end_hour, end_min)
                
                if start_time < end_time:
                    result = (start_time, end_time)
                    logger.debug(f"Парсинг диапазона времени '{text}' → {start_time} - {end_time}")
                    return result
                else:
                    logger.warning(f"Некорректный диапазон: {start_time} - {end_time} из текста '{text}'")
                    return None
            except ValueError as e:
                logger.warning(f"Ошибка при парсинге диапазона времени '{text}': {e}")
                return None
        
        logger.debug(f"Не удалось распарсить диапазон времени из текста '{text}'")
        return None
    
    def parse_datetime_from_task(
        self,
        task_text: str,
        default_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Извлекает дату и время из текста задачи
        
        Args:
            task_text: Текст задачи
            default_date: Дата по умолчанию
        
        Returns:
            {
                "date": date,
                "time": time | None,
                "time_end": time | None,
                "remaining_text": str
            }
        """
        if not default_date:
            default_date = datetime.now().date()
        
        logger.debug(f"Извлечение даты и времени из задачи: '{task_text}' (default_date={default_date})")
        
        result = {
            "date": default_date,
            "time": None,
            "time_end": None,
            "remaining_text": task_text
        }
        
        # Извлечение даты
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', task_text)
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else default_date.year
            
            try:
                result["date"] = date(year, month, day)
                logger.debug(f"Извлечена дата из задачи: {result['date']}")
                # Удаляем дату из текста
                result["remaining_text"] = re.sub(
                    r'\d{1,2}\.\d{1,2}(?:\.\d{4})?',
                    '',
                    result["remaining_text"]
                ).strip()
            except ValueError as e:
                logger.warning(f"Ошибка при извлечении даты из задачи '{task_text}': {e}")
        
        # Извлечение диапазона времени
        time_range = self.parse_time_range(task_text)
        if time_range:
            result["time"] = time_range[0]
            result["time_end"] = time_range[1]
            # Удаляем диапазон из текста
            result["remaining_text"] = re.sub(
                self.TIME_RANGE_PATTERN,
                '',
                result["remaining_text"]
            ).strip()
        else:
            # Извлечение одного времени
            single_time = self.parse_time(task_text)
            if single_time:
                result["time"] = single_time
                # Удаляем время из текста
                result["remaining_text"] = re.sub(
                    self.TIME_PATTERN,
                    '',
                    result["remaining_text"]
                ).strip()
        
        # Очистка лишних пробелов и предлогов
        result["remaining_text"] = re.sub(r'\s+', ' ', result["remaining_text"]).strip()
        result["remaining_text"] = re.sub(r'\b(в|на|к)\s+', '', result["remaining_text"]).strip()
        
        logger.debug(
            f"Результат парсинга задачи: date={result['date']}, "
            f"time={result['time']}, time_end={result['time_end']}, "
            f"remaining_text='{result['remaining_text']}'"
        )
        
        return result
    
    def clear_cache(self):
        """Очистить кэш парсинга дат"""
        cache_size_before = len(self._date_cache)
        self._date_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info(f"Кэш очищен: удалено {cache_size_before} записей")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Получить статистику использования кэша"""
        total_requests = self._cache_hits + self._cache_misses
        hit_ratio = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._date_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_ratio_percent": round(hit_ratio, 2)
        }


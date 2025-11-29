# Руководство по парсингу дат и времени

> **Дата создания:** 2025-01-29  
> **Версия:** 1.0

## 📋 Содержание

1. [Обзор](#обзор)
2. [Поддерживаемые форматы дат](#поддерживаемые-форматы-дат)
3. [Поддерживаемые форматы времени](#поддерживаемые-форматы-времени)
4. [Библиотеки и инструменты](#библиотеки-и-инструменты)
5. [Примеры парсинга](#примеры-парсинга)
6. [Обработка ошибок](#обработка-ошибок)
7. [Учет часового пояса](#учет-часового-пояса)
8. [Примеры кода](#примеры-кода)

---

## 🎯 Обзор

Парсер дат и времени (`DateParser`) предназначен для извлечения дат и времени из естественного языка пользователя. Он должен понимать различные форматы и контексты использования.

### Основные задачи парсера:

1. Извлечение даты из текста ("завтра", "03.12", "03.12.2025")
2. Извлечение времени ("10:00", "11:10 - 12:00")
3. Определение относительных дат относительно текущей даты
4. Валидация и нормализация данных

---

## 📅 Поддерживаемые форматы дат

### Относительные даты

| Формат | Пример | Описание |
|--------|--------|----------|
| `сегодня` | "сегодня" | Текущая дата |
| `завтра` | "завтра" | Текущая дата + 1 день |
| `послезавтра` | "послезавтра" | Текущая дата + 2 дня |
| `вчера` | "вчера" | Текущая дата - 1 день |

### Абсолютные даты

| Формат | Пример | Описание |
|--------|--------|----------|
| `DD.MM` | "03.12" | Дата в текущем году |
| `DD.MM.YYYY` | "03.12.2025" | Полная дата |
| `DD/MM` | "03/12" | Альтернативный формат |
| `DD/MM/YYYY` | "03/12/2025" | Альтернативный формат |
| `YYYY-MM-DD` | "2025-12-03" | ISO формат |

### Дни недели

| Формат | Пример | Описание |
|--------|--------|----------|
| `в понедельник` | "в понедельник" | Ближайший понедельник |
| `в пятницу` | "в пятницу" | Ближайшая пятница |
| `понедельник` | "понедельник" | Ближайший понедельник |

**Примечание:** Если день недели уже прошел на этой неделе, берется следующий.

---

## ⏰ Поддерживаемые форматы времени

### Одно время

| Формат | Пример | Описание |
|--------|--------|----------|
| `HH:MM` | "10:00" | Час и минуты |
| `HH:MM:SS` | "10:00:00" | С секундами (игнорируются) |
| `H:MM` | "9:30" | Без ведущего нуля |

### Диапазон времени

| Формат | Пример | Описание |
|--------|--------|----------|
| `HH:MM - HH:MM` | "11:10 - 12:00" | Начало и конец |
| `HH:MM–HH:MM` | "11:10–12:00" | С длинным тире |
| `HH:MM до HH:MM` | "11:10 до 12:00" | Слово "до" |
| `с HH:MM до HH:MM` | "с 11:10 до 12:00" | С предлогом "с" |

### Множественное время

| Формат | Пример | Описание |
|--------|--------|----------|
| `HH:MM и HH:MM` | "10:00 и 19:00" | Два времени через "и" |
| `HH:MM, HH:MM` | "10:00, 19:00" | Два времени через запятую |

**Примечание:** При множественном времени создаются отдельные задачи для каждого времени.

---

## 🛠️ Библиотеки и инструменты

### Рекомендуемые библиотеки

1. **`dateutil`** - мощная библиотека для парсинга дат
   ```python
   from dateutil import parser
   from dateutil.relativedelta import relativedelta
   ```

2. **`datetime`** - стандартная библиотека Python
   ```python
   from datetime import datetime, date, time, timedelta
   ```

3. **`re`** - регулярные выражения для извлечения паттернов
   ```python
   import re
   ```

### Установка зависимостей

```bash
pip install python-dateutil
```

Или добавить в `requirements.txt`:
```
python-dateutil>=2.8.2
```

---

## 💡 Примеры парсинга

### Пример 1: Простая дата

**Вход:** "завтра"

**Обработка:**
```python
from datetime import datetime, timedelta

today = datetime.now().date()
tomorrow = today + timedelta(days=1)
# Результат: date(2025, 11, 30)
```

### Пример 2: Дата с форматом

**Вход:** "03.12"

**Обработка:**
```python
from datetime import datetime

date_str = "03.12"
current_year = datetime.now().year
full_date_str = f"{date_str}.{current_year}"
parsed_date = datetime.strptime(full_date_str, "%d.%m.%Y").date()
# Результат: date(2025, 12, 3)
```

### Пример 3: Время

**Вход:** "10:00"

**Обработка:**
```python
from datetime import time

time_str = "10:00"
parsed_time = datetime.strptime(time_str, "%H:%M").time()
# Результат: time(10, 0)
```

### Пример 4: Диапазон времени

**Вход:** "11:10 - 12:00"

**Обработка:**
```python
import re

time_range_str = "11:10 - 12:00"
pattern = r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})'
match = re.match(pattern, time_range_str)

if match:
    start_hour, start_min = int(match.group(1)), int(match.group(2))
    end_hour, end_min = int(match.group(3)), int(match.group(4))
    start_time = time(start_hour, start_min)
    end_time = time(end_hour, end_min)
    # Результат: (time(11, 10), time(12, 0))
```

### Пример 5: Извлечение из текста задачи

**Вход:** "Выгул Феры в 10:00 и 19:00"

**Обработка:**
```python
import re

task_text = "Выгул Феры в 10:00 и 19:00"
time_pattern = r'(\d{1,2}):(\d{2})'
times = re.findall(time_pattern, task_text)

# Результат: [('10', '00'), ('19', '00')]
# Создаются две задачи: одна на 10:00, другая на 19:00
```

### Пример 6: Дата в тексте задачи

**Вход:** "5007 - Промониторить трафик и аналитику 03.12"

**Обработка:**
```python
import re

task_text = "5007 - Промониторить трафик и аналитику 03.12"
date_pattern = r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?'
match = re.search(date_pattern, task_text)

if match:
    day, month = int(match.group(1)), int(match.group(2))
    year = int(match.group(3)) if match.group(3) else datetime.now().year
    parsed_date = date(year, month, day)
    # Результат: date(2025, 12, 3)
    
    # Удаляем дату из текста задачи
    cleaned_text = re.sub(date_pattern, '', task_text).strip()
    # Результат: "5007 - Промониторить трафик и аналитику"
```

---

## ⚠️ Обработка ошибок

### Валидация дат

```python
def validate_date(day: int, month: int, year: int) -> bool:
    """Проверка корректности даты"""
    try:
        date(year, month, day)
        return True
    except ValueError:
        return False
```

### Валидация времени

```python
def validate_time(hour: int, minute: int) -> bool:
    """Проверка корректности времени"""
    return 0 <= hour < 24 and 0 <= minute < 60
```

### Обработка нераспознанных форматов

```python
def parse_date_safe(text: str, default_date: Optional[date] = None) -> Optional[date]:
    """Безопасный парсинг даты с fallback"""
    try:
        # Попытка парсинга через dateutil
        parsed = parser.parse(text, default=default_date or datetime.now())
        return parsed.date()
    except (ValueError, TypeError):
        # Fallback на ручной парсинг
        return parse_date_manual(text, default_date)
    except Exception as e:
        logger.warning(f"Не удалось распарсить дату '{text}': {e}")
        return default_date
```

### Логирование ошибок

```python
import logging

logger = logging.getLogger(__name__)

def parse_date_with_logging(text: str) -> Optional[date]:
    """Парсинг с логированием"""
    try:
        result = parse_date(text)
        if result:
            logger.debug(f"Успешно распарсена дата: '{text}' -> {result}")
        else:
            logger.warning(f"Не удалось распарсить дату: '{text}'")
        return result
    except Exception as e:
        logger.error(f"Ошибка при парсинге даты '{text}': {e}", exc_info=True)
        return None
```

---

## 🌍 Учет часового пояса

### Получение часового пояса пользователя

```python
from datetime import datetime
import pytz

def get_user_timezone(user_id: int) -> pytz.timezone:
    """Получить часовой пояс пользователя"""
    # Можно хранить в БД или использовать дефолтный
    # Для России: pytz.timezone('Europe/Moscow')
    return pytz.timezone('Europe/Moscow')
```

### Нормализация времени с учетом часового пояса

```python
def normalize_datetime(dt: datetime, user_timezone: pytz.timezone) -> datetime:
    """Нормализовать datetime с учетом часового пояса"""
    if dt.tzinfo is None:
        # Если время без часового пояса, считаем его локальным
        dt = user_timezone.localize(dt)
    return dt.astimezone(pytz.UTC)  # Сохраняем в UTC
```

### Пример использования

```python
from datetime import datetime
import pytz

# Парсинг времени пользователя
user_time_str = "10:00"
user_date = date(2025, 11, 30)
user_time = datetime.strptime(user_time_str, "%H:%M").time()

# Создание datetime с учетом часового пояса
user_tz = pytz.timezone('Europe/Moscow')
user_datetime = user_tz.localize(
    datetime.combine(user_date, user_time)
)

# Конвертация в UTC для хранения
utc_datetime = user_datetime.astimezone(pytz.UTC)
```

---

## 📝 Примеры кода

### Полный пример класса DateParser

```python
"""
Парсер дат и времени для Todo List
"""
import re
import logging
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, Dict, Any
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

class DateParser:
    """Парсинг дат и времени из естественного языка"""
    
    # Паттерны для дат
    DATE_PATTERNS = [
        (r'сегодня', lambda ref: ref),
        (r'завтра', lambda ref: ref + timedelta(days=1)),
        (r'послезавтра', lambda ref: ref + timedelta(days=2)),
        (r'вчера', lambda ref: ref - timedelta(days=1)),
        (r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', None),  # DD.MM или DD.MM.YYYY
    ]
    
    # Паттерны для времени
    TIME_PATTERN = r'(\d{1,2}):(\d{2})'
    TIME_RANGE_PATTERN = r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})'
    
    def __init__(self, default_timezone='Europe/Moscow'):
        self.default_timezone = default_timezone
    
    def parse_date(self, text: str, reference_date: Optional[date] = None) -> Optional[date]:
        """
        Парсит дату из текста
        
        Args:
            text: Текст с датой
            reference_date: Опорная дата (по умолчанию сегодня)
        
        Returns:
            date объект или None
        """
        if not reference_date:
            reference_date = datetime.now().date()
        
        text_lower = text.lower().strip()
        
        # Проверка относительных дат
        if text_lower == 'сегодня':
            return reference_date
        elif text_lower == 'завтра':
            return reference_date + timedelta(days=1)
        elif text_lower == 'послезавтра':
            return reference_date + timedelta(days=2)
        elif text_lower == 'вчера':
            return reference_date - timedelta(days=1)
        
        # Проверка формата DD.MM или DD.MM.YYYY
        date_match = re.search(r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?', text)
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else reference_date.year
            
            try:
                return date(year, month, day)
            except ValueError:
                logger.warning(f"Некорректная дата: {day}.{month}.{year}")
                return None
        
        # Попытка парсинга через dateutil
        try:
            parsed = dateutil_parser.parse(text, default=datetime.combine(reference_date, time()))
            return parsed.date()
        except (ValueError, TypeError):
            logger.warning(f"Не удалось распарсить дату: '{text}'")
            return None
    
    def parse_time(self, text: str) -> Optional[time]:
        """
        Парсит время из текста
        
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
                return time(hour, minute)
            else:
                logger.warning(f"Некорректное время: {hour}:{minute}")
                return None
        
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
                    return (start_time, end_time)
                else:
                    logger.warning(f"Некорректный диапазон: {start_time} - {end_time}")
                    return None
            except ValueError:
                return None
        
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
                # Удаляем дату из текста
                result["remaining_text"] = re.sub(
                    r'\d{1,2}\.\d{1,2}(?:\.\d{4})?',
                    '',
                    result["remaining_text"]
                ).strip()
            except ValueError:
                pass
        
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
        
        return result
```

---

## 🔗 Связанные документы

- [Техническая спецификация](../specifications/todo-list-feature.md)
- [Инструкции для агентов](agent-instructions-todo.md)
- [Тест-план](../testing/todo-list-test-plan.md)

---

**Дата последнего обновления:** 2025-01-29


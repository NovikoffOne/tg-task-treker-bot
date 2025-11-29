"""
Валидация данных
"""
from typing import Tuple, Optional
import re

MIN_TITLE_LENGTH = 2
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 2000
MAX_NAME_LENGTH = 100

def validate_title(title: str) -> Tuple[bool, Optional[str]]:
    """Валидация названия задачи"""
    title = title.strip()
    
    if len(title) < MIN_TITLE_LENGTH:
        return False, f"Название задачи слишком короткое (минимум {MIN_TITLE_LENGTH} символа)"
    
    if len(title) > MAX_TITLE_LENGTH:
        return False, f"Название задачи слишком длинное (максимум {MAX_TITLE_LENGTH} символов)"
    
    return True, None

def validate_description(description: str) -> Tuple[bool, Optional[str]]:
    """Валидация описания задачи"""
    description = description.strip()
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Описание слишком длинное (максимум {MAX_DESCRIPTION_LENGTH} символов)"
    
    return True, None

def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """Валидация названия (пространство, доска, колонка)"""
    name = name.strip()
    
    if len(name) < MIN_TITLE_LENGTH:
        return False, f"Название слишком короткое (минимум {MIN_TITLE_LENGTH} символа)"
    
    if len(name) > MAX_NAME_LENGTH:
        return False, f"Название слишком длинное (максимум {MAX_NAME_LENGTH} символов)"
    
    return True, None

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Валидация URL"""
    url = url.strip()
    
    # Простая проверка URL
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Некорректный формат URL"
    
    return True, None

def validate_task_id(task_id_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Валидация ID задачи"""
    try:
        task_id = int(task_id_str)
        if task_id <= 0:
            return False, None, "ID задачи должен быть положительным числом"
        return True, task_id, None
    except ValueError:
        return False, None, "ID задачи должен быть числом"

def validate_priority(priority: int) -> Tuple[bool, Optional[str]]:
    """Валидация приоритета"""
    if priority < 0 or priority > 3:
        return False, "Приоритет должен быть от 0 до 3 (0=низкий, 1=средний, 2=высокий, 3=критический)"
    return True, None

def parse_quoted_args(args: list) -> list:
    """
    Парсинг аргументов команды с учетом кавычек.
    Объединяет аргументы, которые были разделены пробелами внутри кавычек.
    Также убирает кавычки из аргументов, если они есть.
    
    Примеры:
        ['"Подготовка', 'аккаунта"', 'План', 'на', 'неделю'] 
        -> ['Подготовка аккаунта', 'План на неделю']
        
        ['"Фикс', 'Багов"', 'move_task']
        -> ['Фикс Багов', 'move_task']
        
        ['"Фикс Багов"', 'move_task']  # Telegram может передать как один аргумент
        -> ['Фикс Багов', 'move_task']
    """
    if not args:
        return []
    
    result = []
    current_arg = None
    in_quotes = False
    
    for arg in args:
        arg_stripped = arg.strip()
        
        # Если аргумент полностью в кавычках (Telegram передал как один аргумент)
        if arg_stripped.startswith('"') and arg_stripped.endswith('"') and len(arg_stripped) > 1:
            # Убираем кавычки
            result.append(arg_stripped[1:-1])
            current_arg = None
            in_quotes = False
        # Если аргумент начинается с кавычки (начало многословного аргумента)
        elif arg_stripped.startswith('"'):
            # Начало кавычек
            current_arg = arg_stripped[1:]  # Убираем открывающую кавычку
            in_quotes = True
        # Если аргумент заканчивается кавычкой и мы внутри кавычек
        elif arg_stripped.endswith('"') and in_quotes:
            # Конец кавычек
            if current_arg is not None:
                current_arg += " " + arg_stripped[:-1]  # Убираем закрывающую кавычку
            else:
                current_arg = arg_stripped[:-1]
            result.append(current_arg)
            current_arg = None
            in_quotes = False
        # Если мы внутри кавычек (продолжение многословного аргумента)
        elif in_quotes:
            if current_arg is not None:
                current_arg += " " + arg_stripped
            else:
                current_arg = arg_stripped
        # Обычный аргумент без кавычек
        else:
            result.append(arg_stripped)
    
    # Если остался незакрытый аргумент в кавычках, добавляем его
    if current_arg is not None:
        result.append(current_arg)
    
    return result


"""
Модель Task (Задача)
"""
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Optional

@dataclass
class Task:
    id: int
    project_id: Optional[str]
    column_id: int
    parent_task_id: Optional[int]
    title: str
    description: Optional[str]
    priority: int  # 0=низкий, 1=средний, 2=высокий, 3=критический
    position: int
    created_at: datetime
    updated_at: datetime
    assignee_id: Optional[int] = None  # Основной ответственный
    started_at: Optional[datetime] = None  # Дата начала работы
    completed_at: Optional[datetime] = None  # Дата завершения
    deadline: Optional[datetime] = None  # Дедлайн задачи
    scheduled_date: Optional[date] = None  # Дата выполнения (для Todo List)
    scheduled_time: Optional[time] = None  # Время выполнения (для Todo List)
    scheduled_time_end: Optional[time] = None  # Конец временного диапазона (для Todo List)
    
    @property
    def priority_emoji(self) -> str:
        """Эмодзи приоритета"""
        priority_map = {
            0: '🟢',  # Низкий
            1: '🟡',  # Средний
            2: '🟠',  # Высокий
            3: '🔴',  # Критический
        }
        return priority_map.get(self.priority, '⚪')
    
    @property
    def priority_name(self) -> str:
        """Название приоритета"""
        priority_map = {
            0: 'Низкий',
            1: 'Средний',
            2: 'Высокий',
            3: 'Критический',
        }
        return priority_map.get(self.priority, 'Не указан')
    
    @classmethod
    def from_row(cls, row) -> 'Task':
        """Создать Task из строки БД"""
        def parse_datetime(value):
            """Парсить datetime из строки или вернуть None"""
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value) if value else None
            return value
        
        def parse_date(value):
            """Парсить date из строки или вернуть None"""
            if value is None:
                return None
            if isinstance(value, str):
                if not value:
                    return None
                return datetime.fromisoformat(value).date() if value else None
            if isinstance(value, datetime):
                return value.date()
            return value
        
        def parse_time(value):
            """Парсить time из строки или вернуть None"""
            if value is None:
                return None
            if isinstance(value, str):
                if not value:
                    return None
                # Формат HH:MM или HH:MM:SS
                parts = value.split(':')
                if len(parts) >= 2:
                    return time(int(parts[0]), int(parts[1]))
            return value
        
        def get_value(key, default=None):
            """Получить значение из row с поддержкой отсутствующих ключей"""
            try:
                return row[key] if key in row.keys() else default
            except (KeyError, AttributeError):
                # Если row не поддерживает keys(), пробуем прямой доступ
                try:
                    return row[key]
                except (KeyError, IndexError):
                    return default
        
        return cls(
            id=row['id'],
            project_id=row['project_id'],
            column_id=row['column_id'],
            parent_task_id=row['parent_task_id'],
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            position=row['position'],
            created_at=parse_datetime(row['created_at']),
            updated_at=parse_datetime(row['updated_at']),
            assignee_id=get_value('assignee_id'),
            started_at=parse_datetime(get_value('started_at')),
            completed_at=parse_datetime(get_value('completed_at')),
            deadline=parse_datetime(get_value('deadline')),
            scheduled_date=parse_date(get_value('scheduled_date')),
            scheduled_time=parse_time(get_value('scheduled_time')),
            scheduled_time_end=parse_time(get_value('scheduled_time_end'))
        )


"""
Модель PersonalTask (Личная задача)
"""
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Optional

@dataclass
class PersonalTask:
    id: int
    user_id: int
    title: str
    scheduled_date: date
    description: Optional[str] = None
    scheduled_time: Optional[time] = None
    scheduled_time_end: Optional[time] = None
    deadline: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    @property
    def time_display(self) -> str:
        """Форматированное отображение времени"""
        if self.scheduled_time and self.scheduled_time_end:
            return f"{self.scheduled_time.strftime('%H:%M')} - {self.scheduled_time_end.strftime('%H:%M')}"
        elif self.scheduled_time:
            return self.scheduled_time.strftime('%H:%M')
        return ""
    
    @classmethod
    def from_row(cls, row) -> 'PersonalTask':
        """Создать PersonalTask из строки БД"""
        def parse_datetime(value):
            """Парсить datetime из строки или вернуть None"""
            if value is None:
                return None
            if isinstance(value, str):
                if not value:
                    return None
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
            user_id=row['user_id'],
            title=row['title'],
            scheduled_date=parse_date(row['scheduled_date']),
            description=get_value('description'),
            scheduled_time=parse_time(get_value('scheduled_time')),
            scheduled_time_end=parse_time(get_value('scheduled_time_end')),
            deadline=parse_datetime(get_value('deadline')),
            completed=bool(get_value('completed', False)),
            completed_at=parse_datetime(get_value('completed_at')),
            created_at=parse_datetime(get_value('created_at')) or datetime.now(),
            updated_at=parse_datetime(get_value('updated_at')) or datetime.now()
        )


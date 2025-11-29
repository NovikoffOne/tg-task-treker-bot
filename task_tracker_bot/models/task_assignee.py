"""
Модель TaskAssignee (Назначение задачи)
"""
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TaskAssignee:
    id: int
    task_id: int
    user_id: int
    role: str  # 'assignee', 'reviewer', 'watcher', etc.
    assigned_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'TaskAssignee':
        """Создать TaskAssignee из строки БД"""
        def parse_datetime(value):
            if value is None:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value) if value else None
            return value
        
        def get_value(key, default=None):
            """Получить значение из row с поддержкой отсутствующих ключей"""
            try:
                return row[key] if key in row.keys() else default
            except (KeyError, AttributeError):
                try:
                    return row[key]
                except (KeyError, IndexError):
                    return default
        
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            user_id=row['user_id'],
            role=get_value('role', 'assignee'),
            assigned_at=parse_datetime(get_value('assigned_at'))
        )


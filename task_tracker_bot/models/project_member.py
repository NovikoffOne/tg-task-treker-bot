"""
Модель ProjectMember (Участник проекта)
"""
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProjectMember:
    id: int
    project_id: str
    user_id: int
    role: str  # 'designer', 'developer', 'tester', 'manager', etc.
    joined_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'ProjectMember':
        """Создать ProjectMember из строки БД"""
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
            project_id=row['project_id'],
            user_id=row['user_id'],
            role=row['role'],
            joined_at=parse_datetime(get_value('joined_at'))
        )


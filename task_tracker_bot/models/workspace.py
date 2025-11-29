"""
Модель Workspace (Пространство)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Workspace:
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Workspace':
        """Создать Workspace из строки БД"""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            updated_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at']
        )


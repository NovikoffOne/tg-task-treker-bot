"""
Модель Board (Доска)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Board:
    id: int
    workspace_id: int
    name: str
    position: int
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Board':
        """Создать Board из строки БД"""
        return cls(
            id=row['id'],
            workspace_id=row['workspace_id'],
            name=row['name'],
            position=row['position'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            updated_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at']
        )


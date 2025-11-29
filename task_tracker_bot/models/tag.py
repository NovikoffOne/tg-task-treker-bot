"""
Модель Tag (Метка)
"""
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Tag:
    id: int
    workspace_id: int
    name: str
    color: str  # HEX цвет
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Tag':
        """Создать Tag из строки БД"""
        return cls(
            id=row['id'],
            workspace_id=row['workspace_id'],
            name=row['name'],
            color=row['color'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
        )


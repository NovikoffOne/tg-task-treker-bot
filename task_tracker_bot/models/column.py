"""
Модель Column (Колонка)
"""
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Column:
    id: int
    board_id: int
    name: str
    position: int
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Column':
        """Создать Column из строки БД"""
        return cls(
            id=row['id'],
            board_id=row['board_id'],
            name=row['name'],
            position=row['position'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
        )


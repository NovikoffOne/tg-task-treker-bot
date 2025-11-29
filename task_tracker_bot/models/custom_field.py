"""
Модель CustomField (Динамическое поле)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CustomField:
    id: int
    workspace_id: int
    name: str
    field_type: str  # 'text', 'url', 'number', 'date', 'select'
    default_value: Optional[str]
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'CustomField':
        """Создать CustomField из строки БД"""
        return cls(
            id=row['id'],
            workspace_id=row['workspace_id'],
            name=row['name'],
            field_type=row['field_type'],
            default_value=row['default_value'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
        )


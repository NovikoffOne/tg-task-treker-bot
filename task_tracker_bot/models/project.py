"""
Модель Project (Проект)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Project:
    id: str  # Настраиваемый ID (например, "5010")
    workspace_id: int
    name: str
    dashboard_stage: str  # Текущий этап дашборда
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Project':
        """Создать Project из строки БД"""
        return cls(
            id=row['id'],
            workspace_id=row['workspace_id'],
            name=row['name'],
            dashboard_stage=row['dashboard_stage'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            updated_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at']
        )


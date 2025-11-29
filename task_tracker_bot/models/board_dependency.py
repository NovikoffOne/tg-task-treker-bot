"""
Модель BoardDependency (Зависимость досок)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BoardDependency:
    id: int
    workspace_id: int
    name: str
    source_board_id: int
    source_column_id: int
    trigger_type: str  # 'enter' или 'leave'
    target_board_id: int
    target_column_id: int
    action_type: str  # 'create_task' или 'move_task'
    task_title_template: Optional[str] = None
    enabled: bool = True
    created_at: datetime = None
    
    @classmethod
    def from_row(cls, row) -> 'BoardDependency':
        """Создать BoardDependency из строки БД"""
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
            workspace_id=row['workspace_id'],
            name=row['name'],
            source_board_id=row['source_board_id'],
            source_column_id=row['source_column_id'],
            trigger_type=get_value('trigger_type', 'enter'),
            target_board_id=row['target_board_id'],
            target_column_id=row['target_column_id'],
            action_type=row['action_type'],
            task_title_template=get_value('task_title_template'),
            enabled=bool(get_value('enabled', True)),
            created_at=parse_datetime(get_value('created_at'))
        )


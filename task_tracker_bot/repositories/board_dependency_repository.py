"""
Репозиторий для работы с BoardDependency
"""
from typing import List, Optional
from database import Database
from models.board_dependency import BoardDependency

class BoardDependencyRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, workspace_id: int, name: str, source_board_id: int,
               source_column_id: int, trigger_type: str, target_board_id: int,
               target_column_id: int, action_type: str,
               task_title_template: Optional[str] = None, enabled: bool = True) -> int:
        """Создать зависимость досок"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO board_dependencies 
                (workspace_id, name, source_board_id, source_column_id, trigger_type,
                 target_board_id, target_column_id, action_type, task_title_template, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (workspace_id, name, source_board_id, source_column_id, trigger_type,
                  target_board_id, target_column_id, action_type, task_title_template, enabled))
            return cursor.lastrowid
    
    def get_by_id(self, dependency_id: int) -> Optional[BoardDependency]:
        """Получить зависимость по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM board_dependencies
                WHERE id = ?
            """, (dependency_id,))
            row = cursor.fetchone()
            if row:
                return BoardDependency.from_row(row)
            return None
    
    def get_all_by_workspace(self, workspace_id: int) -> List[BoardDependency]:
        """Получить все зависимости пространства"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM board_dependencies
                WHERE workspace_id = ?
                ORDER BY created_at DESC
            """, (workspace_id,))
            rows = cursor.fetchall()
            return [BoardDependency.from_row(row) for row in rows]
    
    def get_by_source(self, source_board_id: int, source_column_id: int,
                      trigger_type: str = 'enter') -> List[BoardDependency]:
        """Получить зависимости по источнику"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM board_dependencies
                WHERE source_board_id = ? 
                AND source_column_id = ?
                AND trigger_type = ?
                AND enabled = 1
                ORDER BY created_at ASC
            """, (source_board_id, source_column_id, trigger_type))
            rows = cursor.fetchall()
            return [BoardDependency.from_row(row) for row in rows]
    
    def update(self, dependency_id: int, name: Optional[str] = None,
               enabled: Optional[bool] = None, task_title_template: Optional[str] = None) -> bool:
        """Обновить зависимость"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(enabled)
        if task_title_template is not None:
            updates.append("task_title_template = ?")
            params.append(task_title_template)
        
        if not updates:
            return False
        
        params.append(dependency_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE board_dependencies
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete(self, dependency_id: int) -> bool:
        """Удалить зависимость"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM board_dependencies
                WHERE id = ?
            """, (dependency_id,))
            return cursor.rowcount > 0


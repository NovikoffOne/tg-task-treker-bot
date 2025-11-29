"""
Репозиторий для работы с Workspace
"""
from typing import List, Optional
from database import Database
from models.workspace import Workspace

class WorkspaceRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, user_id: int, name: str) -> int:
        """Создать пространство"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workspaces (user_id, name)
                VALUES (?, ?)
            """, (user_id, name))
            return cursor.lastrowid
    
    def get_by_id(self, workspace_id: int, user_id: int) -> Optional[Workspace]:
        """Получить пространство по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workspaces
                WHERE id = ? AND user_id = ?
            """, (workspace_id, user_id))
            row = cursor.fetchone()
            if row:
                return Workspace.from_row(row)
            return None
    
    def get_by_name(self, user_id: int, name: str) -> Optional[Workspace]:
        """Получить пространство по имени"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workspaces
                WHERE user_id = ? AND name = ?
            """, (user_id, name))
            row = cursor.fetchone()
            if row:
                return Workspace.from_row(row)
            return None
    
    def get_all_by_user(self, user_id: int) -> List[Workspace]:
        """Получить все пространства пользователя"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workspaces
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [Workspace.from_row(row) for row in rows]
    
    def update(self, workspace_id: int, user_id: int, name: str) -> bool:
        """Обновить пространство"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workspaces
                SET name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (name, workspace_id, user_id))
            return cursor.rowcount > 0
    
    def delete(self, workspace_id: int, user_id: int) -> bool:
        """Удалить пространство"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM workspaces
                WHERE id = ? AND user_id = ?
            """, (workspace_id, user_id))
            return cursor.rowcount > 0


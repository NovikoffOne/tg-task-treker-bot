"""
Репозиторий для работы с Board
"""
from typing import List, Optional
from database import Database
from models.board import Board

class BoardRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, workspace_id: int, name: str, position: int = 0) -> int:
        """Создать доску"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO boards (workspace_id, name, position)
                VALUES (?, ?, ?)
            """, (workspace_id, name, position))
            return cursor.lastrowid
    
    def get_by_id(self, board_id: int) -> Optional[Board]:
        """Получить доску по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM boards
                WHERE id = ?
            """, (board_id,))
            row = cursor.fetchone()
            if row:
                return Board.from_row(row)
            return None
    
    def get_by_name(self, workspace_id: int, name: str) -> Optional[Board]:
        """Получить доску по имени"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM boards
                WHERE workspace_id = ? AND name = ?
            """, (workspace_id, name))
            row = cursor.fetchone()
            if row:
                return Board.from_row(row)
            return None
    
    def get_all_by_workspace(self, workspace_id: int) -> List[Board]:
        """Получить все доски пространства"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM boards
                WHERE workspace_id = ?
                ORDER BY position ASC, created_at ASC
            """, (workspace_id,))
            rows = cursor.fetchall()
            return [Board.from_row(row) for row in rows]
    
    def update(self, board_id: int, name: Optional[str] = None, position: Optional[int] = None) -> bool:
        """Обновить доску"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if position is not None:
            updates.append("position = ?")
            params.append(position)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(board_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE boards
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete(self, board_id: int) -> bool:
        """Удалить доску"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM boards
                WHERE id = ?
            """, (board_id,))
            return cursor.rowcount > 0


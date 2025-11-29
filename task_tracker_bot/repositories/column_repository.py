"""
Репозиторий для работы с Column
"""
from typing import List, Optional
from database import Database
from models.column import Column

class ColumnRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, board_id: int, name: str, position: int = 0) -> int:
        """Создать колонку"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO columns (board_id, name, position)
                VALUES (?, ?, ?)
            """, (board_id, name, position))
            return cursor.lastrowid
    
    def get_by_id(self, column_id: int) -> Optional[Column]:
        """Получить колонку по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM columns
                WHERE id = ?
            """, (column_id,))
            row = cursor.fetchone()
            if row:
                return Column.from_row(row)
            return None
    
    def get_by_name(self, board_id: int, name: str) -> Optional[Column]:
        """Получить колонку по имени"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM columns
                WHERE board_id = ? AND name = ?
            """, (board_id, name))
            row = cursor.fetchone()
            if row:
                return Column.from_row(row)
            return None
    
    def get_all_by_board(self, board_id: int) -> List[Column]:
        """Получить все колонки доски"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM columns
                WHERE board_id = ?
                ORDER BY position ASC, created_at ASC
            """, (board_id,))
            rows = cursor.fetchall()
            return [Column.from_row(row) for row in rows]
    
    def get_first_by_board(self, board_id: int) -> Optional[Column]:
        """Получить первую колонку доски"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM columns
                WHERE board_id = ?
                ORDER BY position ASC, created_at ASC
                LIMIT 1
            """, (board_id,))
            row = cursor.fetchone()
            if row:
                return Column.from_row(row)
            return None
    
    def update(self, column_id: int, name: Optional[str] = None, position: Optional[int] = None) -> bool:
        """Обновить колонку"""
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
        
        params.append(column_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE columns
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete(self, column_id: int) -> bool:
        """Удалить колонку"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM columns
                WHERE id = ?
            """, (column_id,))
            return cursor.rowcount > 0


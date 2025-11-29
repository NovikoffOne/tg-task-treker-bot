"""
Репозиторий для работы с Tag
"""
import sqlite3
from typing import List, Optional
from database import Database
from models.tag import Tag

class TagRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, workspace_id: int, name: str, color: str = '#3498db') -> int:
        """Создать метку"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_tags (workspace_id, name, color)
                VALUES (?, ?, ?)
            """, (workspace_id, name, color))
            return cursor.lastrowid
    
    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        """Получить метку по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_tags
                WHERE id = ?
            """, (tag_id,))
            row = cursor.fetchone()
            if row:
                return Tag.from_row(row)
            return None
    
    def get_by_name(self, workspace_id: int, name: str) -> Optional[Tag]:
        """Получить метку по имени"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_tags
                WHERE workspace_id = ? AND name = ?
            """, (workspace_id, name))
            row = cursor.fetchone()
            if row:
                return Tag.from_row(row)
            return None
    
    def get_all_by_workspace(self, workspace_id: int) -> List[Tag]:
        """Получить все метки пространства"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_tags
                WHERE workspace_id = ?
                ORDER BY created_at ASC
            """, (workspace_id,))
            rows = cursor.fetchall()
            return [Tag.from_row(row) for row in rows]
    
    def add_to_task(self, task_id: int, tag_id: int) -> bool:
        """Добавить метку к задаче"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO task_tag_relations (task_id, tag_id)
                    VALUES (?, ?)
                """, (task_id, tag_id))
                return True
            except sqlite3.IntegrityError:
                return False  # Уже существует
    
    def remove_from_task(self, task_id: int, tag_id: int) -> bool:
        """Удалить метку с задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM task_tag_relations
                WHERE task_id = ? AND tag_id = ?
            """, (task_id, tag_id))
            return cursor.rowcount > 0
    
    def get_task_tags(self, task_id: int) -> List[Tag]:
        """Получить все метки задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.* FROM task_tags t
                INNER JOIN task_tag_relations ttr ON t.id = ttr.tag_id
                WHERE ttr.task_id = ?
                ORDER BY t.name ASC
            """, (task_id,))
            rows = cursor.fetchall()
            return [Tag.from_row(row) for row in rows]
    
    def delete(self, tag_id: int) -> bool:
        """Удалить метку"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM task_tags
                WHERE id = ?
            """, (tag_id,))
            return cursor.rowcount > 0


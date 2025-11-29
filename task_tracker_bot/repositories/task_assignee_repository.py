"""
Репозиторий для работы с TaskAssignee
"""
from typing import List, Optional
from database import Database
from models.task_assignee import TaskAssignee

class TaskAssigneeRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, task_id: int, user_id: int, role: str = 'assignee') -> int:
        """Создать назначение задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Используем INSERT OR IGNORE для избежания дубликатов
            cursor.execute("""
                INSERT OR IGNORE INTO task_assignees (task_id, user_id, role)
                VALUES (?, ?, ?)
            """, (task_id, user_id, role))
            if cursor.rowcount > 0:
                return cursor.lastrowid
            # Если запись уже существует, получаем её ID
            cursor.execute("""
                SELECT id FROM task_assignees
                WHERE task_id = ? AND user_id = ? AND role = ?
            """, (task_id, user_id, role))
            row = cursor.fetchone()
            return row['id'] if row else None
    
    def get_by_id(self, assignee_id: int) -> Optional[TaskAssignee]:
        """Получить назначение по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_assignees
                WHERE id = ?
            """, (assignee_id,))
            row = cursor.fetchone()
            if row:
                return TaskAssignee.from_row(row)
            return None
    
    def get_by_task(self, task_id: int) -> List[TaskAssignee]:
        """Получить все назначения задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM task_assignees
                WHERE task_id = ?
                ORDER BY assigned_at ASC
            """, (task_id,))
            rows = cursor.fetchall()
            return [TaskAssignee.from_row(row) for row in rows]
    
    def get_by_user(self, user_id: int, role: Optional[str] = None) -> List[TaskAssignee]:
        """Получить все назначения пользователя"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if role:
                cursor.execute("""
                    SELECT * FROM task_assignees
                    WHERE user_id = ? AND role = ?
                    ORDER BY assigned_at DESC
                """, (user_id, role))
            else:
                cursor.execute("""
                    SELECT * FROM task_assignees
                    WHERE user_id = ?
                    ORDER BY assigned_at DESC
                """, (user_id,))
            rows = cursor.fetchall()
            return [TaskAssignee.from_row(row) for row in rows]
    
    def delete(self, task_id: int, user_id: int, role: Optional[str] = None) -> bool:
        """Удалить назначение"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if role:
                cursor.execute("""
                    DELETE FROM task_assignees
                    WHERE task_id = ? AND user_id = ? AND role = ?
                """, (task_id, user_id, role))
            else:
                cursor.execute("""
                    DELETE FROM task_assignees
                    WHERE task_id = ? AND user_id = ?
                """, (task_id, user_id))
            return cursor.rowcount > 0
    
    def delete_by_task(self, task_id: int) -> bool:
        """Удалить все назначения задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM task_assignees
                WHERE task_id = ?
            """, (task_id,))
            return cursor.rowcount > 0


"""
Репозиторий для работы с PersonalTask
"""
from typing import List, Optional
from datetime import date, time, datetime
from database import Database
from models.personal_task import PersonalTask

class PersonalTaskRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(
        self,
        user_id: int,
        title: str,
        scheduled_date: date,
        scheduled_time: Optional[time] = None,
        scheduled_time_end: Optional[time] = None,
        deadline: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> int:
        """Создать личную задачу"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO personal_tasks (
                    user_id, title, description, scheduled_date, 
                    scheduled_time, scheduled_time_end, deadline
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, title, description, scheduled_date.isoformat(),
                scheduled_time.isoformat() if scheduled_time else None,
                scheduled_time_end.isoformat() if scheduled_time_end else None,
                deadline.isoformat() if deadline else None
            ))
            return cursor.lastrowid
    
    def get_by_id(self, task_id: int) -> Optional[PersonalTask]:
        """Получить задачу по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM personal_tasks
                WHERE id = ?
            """, (task_id,))
            row = cursor.fetchone()
            if row:
                return PersonalTask.from_row(row)
            return None
    
    def get_by_date(self, user_id: int, target_date: date) -> List[PersonalTask]:
        """Получить задачи на указанную дату"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM personal_tasks
                WHERE user_id = ? AND scheduled_date = ?
                ORDER BY scheduled_time ASC, created_at ASC
            """, (user_id, target_date.isoformat()))
            rows = cursor.fetchall()
            return [PersonalTask.from_row(row) for row in rows]
    
    def get_by_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[PersonalTask]:
        """Получить задачи в диапазоне дат"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM personal_tasks
                WHERE user_id = ? 
                AND scheduled_date >= ? 
                AND scheduled_date <= ?
                ORDER BY scheduled_date ASC, scheduled_time ASC, created_at ASC
            """, (user_id, start_date.isoformat(), end_date.isoformat()))
            rows = cursor.fetchall()
            return [PersonalTask.from_row(row) for row in rows]
    
    def mark_completed(self, task_id: int, user_id: int) -> bool:
        """Отметить задачу как выполненную"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE personal_tasks
                SET completed = 1, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (task_id, user_id))
            return cursor.rowcount > 0
    
    def update(
        self,
        task_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_date: Optional[date] = None,
        scheduled_time: Optional[time] = None,
        scheduled_time_end: Optional[time] = None,
        deadline: Optional[datetime] = None
    ) -> bool:
        """Обновить задачу"""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if scheduled_date is not None:
            updates.append("scheduled_date = ?")
            params.append(scheduled_date.isoformat())
        if scheduled_time is not None:
            updates.append("scheduled_time = ?")
            params.append(scheduled_time.isoformat())
        if scheduled_time_end is not None:
            updates.append("scheduled_time_end = ?")
            params.append(scheduled_time_end.isoformat())
        if deadline is not None:
            updates.append("deadline = ?")
            params.append(deadline.isoformat())
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([task_id, user_id])
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE personal_tasks
                SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete(self, task_id: int, user_id: int) -> bool:
        """Удалить задачу"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM personal_tasks
                WHERE id = ? AND user_id = ?
            """, (task_id, user_id))
            return cursor.rowcount > 0


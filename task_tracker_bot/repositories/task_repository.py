"""
Репозиторий для работы с Task
"""
from typing import List, Optional
from datetime import date, time
from database import Database
from models.task import Task

class TaskRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, column_id: int, title: str, description: Optional[str] = None,
               project_id: Optional[str] = None, parent_task_id: Optional[int] = None,
               priority: int = 0, position: int = 0,
               scheduled_date: Optional[date] = None,
               scheduled_time: Optional[time] = None,
               scheduled_time_end: Optional[time] = None) -> int:
        """Создать задачу"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (
                    column_id, title, description, project_id, parent_task_id, 
                    priority, position, scheduled_date, scheduled_time, scheduled_time_end
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                column_id, title, description, project_id, parent_task_id, 
                priority, position,
                scheduled_date.isoformat() if scheduled_date else None,
                scheduled_time.isoformat() if scheduled_time else None,
                scheduled_time_end.isoformat() if scheduled_time_end else None
            ))
            return cursor.lastrowid
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE id = ?
            """, (task_id,))
            row = cursor.fetchone()
            if row:
                return Task.from_row(row)
            return None
    
    def get_all_by_column(self, column_id: int) -> List[Task]:
        """Получить все задачи колонки"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE column_id = ?
                ORDER BY position ASC, created_at ASC
            """, (column_id,))
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]
    
    def get_all_by_project(self, project_id: str) -> List[Task]:
        """Получить все задачи проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE project_id = ?
                ORDER BY created_at ASC
            """, (project_id,))
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]
    
    def get_subtasks(self, parent_task_id: int) -> List[Task]:
        """Получить все подзадачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE parent_task_id = ?
                ORDER BY position ASC, created_at ASC
            """, (parent_task_id,))
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]
    
    def update(self, task_id: int, column_id: Optional[int] = None, title: Optional[str] = None,
               description: Optional[str] = None, priority: Optional[int] = None,
               position: Optional[int] = None, assignee_id: Optional[int] = None,
               started_at: Optional = None, completed_at: Optional = None,
               deadline: Optional = None,
               scheduled_date: Optional[date] = None,
               scheduled_time: Optional[time] = None,
               scheduled_time_end: Optional[time] = None) -> bool:
        """Обновить задачу
        
        Args:
            started_at: datetime объект или строка ISO формата
            completed_at: datetime объект или строка ISO формата
            deadline: datetime объект или строка ISO формата
            scheduled_date: date объект
            scheduled_time: time объект
            scheduled_time_end: time объект
        """
        from datetime import datetime
        
        updates = []
        params = []
        
        if column_id is not None:
            updates.append("column_id = ?")
            params.append(column_id)
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if position is not None:
            updates.append("position = ?")
            params.append(position)
        if assignee_id is not None:
            updates.append("assignee_id = ?")
            params.append(assignee_id)
        if started_at is not None:
            updates.append("started_at = ?")
            params.append(started_at.isoformat() if isinstance(started_at, datetime) else started_at)
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat() if isinstance(completed_at, datetime) else completed_at)
        if deadline is not None:
            updates.append("deadline = ?")
            params.append(deadline.isoformat() if isinstance(deadline, datetime) else deadline)
        if scheduled_date is not None:
            updates.append("scheduled_date = ?")
            params.append(scheduled_date.isoformat())
        if scheduled_time is not None:
            updates.append("scheduled_time = ?")
            params.append(scheduled_time.isoformat())
        if scheduled_time_end is not None:
            updates.append("scheduled_time_end = ?")
            params.append(scheduled_time_end.isoformat())
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE tasks
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete(self, task_id: int) -> bool:
        """Удалить задачу"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tasks
                WHERE id = ?
            """, (task_id,))
            return cursor.rowcount > 0
    
    def get_max_position(self, column_id: int) -> int:
        """Получить максимальную позицию в колонке"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(MAX(position), -1) FROM tasks
                WHERE column_id = ?
            """, (column_id,))
            result = cursor.fetchone()
            return result[0] + 1 if result else 0
    
    def get_by_assignee(self, user_id: int) -> List[Task]:
        """Получить все задачи пользователя (по assignee_id)"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE assignee_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]
    
    def get_by_deadline(self, deadline_date: str) -> List[Task]:
        """Получить все задачи с дедлайном на указанную дату"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE DATE(deadline) = DATE(?)
                ORDER BY deadline ASC
            """, (deadline_date,))
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Получить все просроченные задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks
                WHERE deadline IS NOT NULL
                AND deadline < datetime('now')
                AND completed_at IS NULL
                ORDER BY deadline ASC
            """)
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]
    
    def get_by_scheduled_date(self, scheduled_date: date, project_id: Optional[str] = None) -> List[Task]:
        """Получить задачи на указанную дату
        
        Args:
            scheduled_date: Дата выполнения
            project_id: Если указан, фильтровать по project_id
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute("""
                    SELECT * FROM tasks
                    WHERE scheduled_date = ? AND project_id = ?
                    ORDER BY scheduled_time ASC, created_at ASC
                """, (scheduled_date.isoformat(), project_id))
            else:
                cursor.execute("""
                    SELECT * FROM tasks
                    WHERE scheduled_date = ? AND project_id IS NOT NULL
                    ORDER BY scheduled_time ASC, created_at ASC
                """, (scheduled_date.isoformat(),))
            rows = cursor.fetchall()
            return [Task.from_row(row) for row in rows]


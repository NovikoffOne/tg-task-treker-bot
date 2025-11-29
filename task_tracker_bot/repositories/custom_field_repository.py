"""
Репозиторий для работы с CustomField
"""
from typing import List, Optional, Dict
from database import Database
from models.custom_field import CustomField

class CustomFieldRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, workspace_id: int, name: str, field_type: str, default_value: Optional[str] = None) -> int:
        """Создать поле"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO custom_fields (workspace_id, name, field_type, default_value)
                VALUES (?, ?, ?, ?)
            """, (workspace_id, name, field_type, default_value))
            return cursor.lastrowid
    
    def get_by_id(self, field_id: int) -> Optional[CustomField]:
        """Получить поле по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM custom_fields
                WHERE id = ?
            """, (field_id,))
            row = cursor.fetchone()
            if row:
                return CustomField.from_row(row)
            return None
    
    def get_by_name(self, workspace_id: int, name: str) -> Optional[CustomField]:
        """Получить поле по имени"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM custom_fields
                WHERE workspace_id = ? AND name = ?
            """, (workspace_id, name))
            row = cursor.fetchone()
            if row:
                return CustomField.from_row(row)
            return None
    
    def get_all_by_workspace(self, workspace_id: int) -> List[CustomField]:
        """Получить все поля пространства"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM custom_fields
                WHERE workspace_id = ?
                ORDER BY created_at ASC
            """, (workspace_id,))
            rows = cursor.fetchall()
            return [CustomField.from_row(row) for row in rows]
    
    def set_task_field(self, task_id: int, field_id: int, value: str) -> bool:
        """Установить значение поля для задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_custom_fields (task_id, field_id, value)
                VALUES (?, ?, ?)
                ON CONFLICT(task_id, field_id) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
            """, (task_id, field_id, value, value))
            return cursor.rowcount > 0
    
    def get_task_field(self, task_id: int, field_id: int) -> Optional[str]:
        """Получить значение поля задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM task_custom_fields
                WHERE task_id = ? AND field_id = ?
            """, (task_id, field_id))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def get_task_fields(self, task_id: int) -> Dict[int, str]:
        """Получить все поля задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT field_id, value FROM task_custom_fields
                WHERE task_id = ?
            """, (task_id,))
            rows = cursor.fetchall()
            return {row['field_id']: row['value'] for row in rows}
    
    def delete_task_field(self, task_id: int, field_id: int) -> bool:
        """Удалить поле задачи"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM task_custom_fields
                WHERE task_id = ? AND field_id = ?
            """, (task_id, field_id))
            return cursor.rowcount > 0
    
    def enable_project_sync(self, project_id: str, field_id: int) -> bool:
        """Включить синхронизацию поля для проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_field_sync (project_id, field_id, sync_enabled)
                VALUES (?, ?, 1)
                ON CONFLICT(project_id, field_id) DO UPDATE SET sync_enabled = 1
            """, (project_id, field_id))
            return cursor.rowcount > 0
    
    def disable_project_sync(self, project_id: str, field_id: int) -> bool:
        """Отключить синхронизацию поля для проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE project_field_sync
                SET sync_enabled = 0
                WHERE project_id = ? AND field_id = ?
            """, (project_id, field_id))
            return cursor.rowcount > 0
    
    def is_sync_enabled(self, project_id: str, field_id: int) -> bool:
        """Проверить, включена ли синхронизация"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sync_enabled FROM project_field_sync
                WHERE project_id = ? AND field_id = ?
            """, (project_id, field_id))
            row = cursor.fetchone()
            return row['sync_enabled'] == 1 if row else False
    
    def get_synced_fields(self, project_id: str) -> List[int]:
        """Получить список синхронизированных полей проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT field_id FROM project_field_sync
                WHERE project_id = ? AND sync_enabled = 1
            """, (project_id,))
            rows = cursor.fetchall()
            return [row['field_id'] for row in rows]
    
    def delete(self, field_id: int) -> bool:
        """Удалить поле"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM custom_fields
                WHERE id = ?
            """, (field_id,))
            return cursor.rowcount > 0


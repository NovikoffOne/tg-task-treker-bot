"""
Репозиторий для работы с ProjectMember
"""
from typing import List, Optional
from database import Database
from models.project_member import ProjectMember

class ProjectMemberRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, project_id: str, user_id: int, role: str) -> int:
        """Создать участника проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Используем INSERT OR IGNORE для избежания дубликатов
            cursor.execute("""
                INSERT OR IGNORE INTO project_members (project_id, user_id, role)
                VALUES (?, ?, ?)
            """, (project_id, user_id, role))
            if cursor.rowcount > 0:
                return cursor.lastrowid
            # Если запись уже существует, получаем её ID
            cursor.execute("""
                SELECT id FROM project_members
                WHERE project_id = ? AND user_id = ? AND role = ?
            """, (project_id, user_id, role))
            row = cursor.fetchone()
            return row['id'] if row else None
    
    def get_by_id(self, member_id: int) -> Optional[ProjectMember]:
        """Получить участника по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM project_members
                WHERE id = ?
            """, (member_id,))
            row = cursor.fetchone()
            if row:
                return ProjectMember.from_row(row)
            return None
    
    def get_by_project(self, project_id: str) -> List[ProjectMember]:
        """Получить всех участников проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM project_members
                WHERE project_id = ?
                ORDER BY joined_at ASC
            """, (project_id,))
            rows = cursor.fetchall()
            return [ProjectMember.from_row(row) for row in rows]
    
    def get_by_user(self, user_id: int) -> List[ProjectMember]:
        """Получить все проекты пользователя"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM project_members
                WHERE user_id = ?
                ORDER BY joined_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [ProjectMember.from_row(row) for row in rows]
    
    def get_by_project_and_user(self, project_id: str, user_id: int) -> Optional[ProjectMember]:
        """Получить участника проекта по проекту и пользователю"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM project_members
                WHERE project_id = ? AND user_id = ?
                LIMIT 1
            """, (project_id, user_id))
            row = cursor.fetchone()
            if row:
                return ProjectMember.from_row(row)
            return None
    
    def delete(self, project_id: str, user_id: int, role: Optional[str] = None) -> bool:
        """Удалить участника проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if role:
                cursor.execute("""
                    DELETE FROM project_members
                    WHERE project_id = ? AND user_id = ? AND role = ?
                """, (project_id, user_id, role))
            else:
                cursor.execute("""
                    DELETE FROM project_members
                    WHERE project_id = ? AND user_id = ?
                """, (project_id, user_id))
            return cursor.rowcount > 0
    
    def delete_by_project(self, project_id: str) -> bool:
        """Удалить всех участников проекта"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM project_members
                WHERE project_id = ?
            """, (project_id,))
            return cursor.rowcount > 0


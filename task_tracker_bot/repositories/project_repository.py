"""
Репозиторий для работы с Project
"""
from typing import List, Optional
from database import Database
from models.project import Project

class ProjectRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, project_id: str, workspace_id: int, name: str, dashboard_stage: str = 'preparation') -> str:
        """Создать проект"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (id, workspace_id, name, dashboard_stage)
                VALUES (?, ?, ?, ?)
            """, (project_id, workspace_id, name, dashboard_stage))
            return project_id
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Получить проект по ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects
                WHERE id = ?
            """, (project_id,))
            row = cursor.fetchone()
            if row:
                return Project.from_row(row)
            return None
    
    def get_all_by_workspace(self, workspace_id: int) -> List[Project]:
        """Получить все проекты пространства"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM projects
                WHERE workspace_id = ?
                ORDER BY created_at DESC
            """, (workspace_id,))
            rows = cursor.fetchall()
            return [Project.from_row(row) for row in rows]
    
    def update(self, project_id: str, name: Optional[str] = None, dashboard_stage: Optional[str] = None) -> bool:
        """Обновить проект"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if dashboard_stage is not None:
            updates.append("dashboard_stage = ?")
            params.append(dashboard_stage)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(project_id)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE projects
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete(self, project_id: str) -> bool:
        """Удалить проект"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM projects
                WHERE id = ?
            """, (project_id,))
            return cursor.rowcount > 0


"""
Сервис для работы с Project
Включает автоматическое создание задач проекта на досках
"""
from typing import List, Optional, Tuple
from repositories.project_repository import ProjectRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.task_repository import TaskRepository
from models.project import Project

class ProjectService:
    def __init__(self, project_repo: ProjectRepository, board_repo: BoardRepository,
                 column_repo: ColumnRepository, task_repo: TaskRepository):
        self.project_repo = project_repo
        self.board_repo = board_repo
        self.column_repo = column_repo
        self.task_repo = task_repo
    
    def create_project(self, project_id: str, workspace_id: int, name: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Создать проект с автоматическим созданием задач на досках"""
        # Валидация
        project_id = project_id.strip()
        name = name.strip()
        
        if len(project_id) < 1:
            return False, None, "ID проекта не может быть пустым"
        if len(project_id) > 50:
            return False, None, "ID проекта слишком длинный (максимум 50 символов)"
        if len(name) < 2:
            return False, None, "Название проекта должно быть минимум 2 символа"
        if len(name) > 200:
            return False, None, "Название проекта слишком длинное (максимум 200 символов)"
        
        # Проверка уникальности ID
        existing = self.project_repo.get_by_id(project_id)
        if existing:
            return False, None, "Проект с таким ID уже существует"
        
        try:
            # Создать проект
            self.project_repo.create(project_id, workspace_id, name)
            
            # Найти доску "Подготовка" в пространстве
            preparation_board = self.board_repo.get_by_name(workspace_id, "Подготовка")
            
            # Если доска "Подготовка" не найдена, использовать первую доску как fallback
            if not preparation_board:
                boards = self.board_repo.get_all_by_workspace(workspace_id)
                if not boards:
                    return False, None, "В пространстве нет досок. Создайте хотя бы одну доску."
                preparation_board = boards[0]
            
            # Создать задачу только на доске "Подготовка"
            # Задачи на других досках будут создаваться автоматически через зависимости досок
            first_column = self.column_repo.get_first_by_board(preparation_board.id)
            if not first_column:
                return False, None, f"На доске '{preparation_board.name}' нет колонок"
            
            # Создать задачу: "{project_id} {name} {board_name}"
            task_title = f"{project_id} {name} {preparation_board.name}"
            position = self.task_repo.get_max_position(first_column.id)
            task_id = self.task_repo.create(
                column_id=first_column.id,
                title=task_title,
                project_id=project_id,
                priority=0,
                position=position
            )
            
            return True, project_id, None
        except Exception as e:
            return False, None, f"Ошибка при создании проекта: {str(e)}"
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Получить проект"""
        return self.project_repo.get_by_id(project_id)
    
    def list_projects(self, workspace_id: int) -> List[Project]:
        """Получить все проекты пространства"""
        return self.project_repo.get_all_by_workspace(workspace_id)
    
    def update_dashboard_stage(self, project_id: str, stage: str) -> tuple[bool, Optional[str]]:
        """Обновить этап дашборда проекта"""
        valid_stages = ['preparation', 'design', 'development', 'testing', 
                       'submission', 'moderation', 'rejected', 'published']
        if stage not in valid_stages:
            return False, f"Некорректный этап. Допустимые: {', '.join(valid_stages)}"
        
        try:
            success = self.project_repo.update(project_id, dashboard_stage=stage)
            if success:
                return True, None
            return False, "Проект не найден"
        except Exception as e:
            return False, f"Ошибка при обновлении: {str(e)}"
    
    def delete_project(self, project_id: str) -> tuple[bool, Optional[str]]:
        """Удалить проект (задачи остаются, но теряют связь)"""
        project = self.project_repo.get_by_id(project_id)
        if not project:
            return False, "Проект не найден"
        
        try:
            success = self.project_repo.delete(project_id)
            if success:
                return True, None
            return False, "Ошибка при удалении проекта"
        except Exception as e:
            return False, f"Ошибка при удалении: {str(e)}"


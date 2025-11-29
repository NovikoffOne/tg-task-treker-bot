"""
Сервис для работы с назначениями задач и участниками проектов
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from repositories.task_assignee_repository import TaskAssigneeRepository
from repositories.project_member_repository import ProjectMemberRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from models.task_assignee import TaskAssignee
from models.project_member import ProjectMember

logger = logging.getLogger(__name__)

class AssignmentService:
    def __init__(self, assignee_repo: TaskAssigneeRepository,
                 member_repo: ProjectMemberRepository,
                 task_repo: TaskRepository, project_repo: ProjectRepository,
                 column_repo: ColumnRepository, board_repo: BoardRepository):
        self.assignee_repo = assignee_repo
        self.member_repo = member_repo
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.column_repo = column_repo
        self.board_repo = board_repo
    
    def assign_task(self, task_id: int, user_id: int, role: str = 'assignee') -> Tuple[bool, Optional[str]]:
        """Назначить пользователя на задачу"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return (False, "Задача не найдена")
        
        try:
            assignee_id = self.assignee_repo.create(task_id, user_id, role)
            if assignee_id:
                # Обновляем assignee_id в задаче (основной ответственный)
                if role == 'assignee':
                    self.task_repo.update(task_id, assignee_id=user_id)
                logger.info(f"Назначен пользователь {user_id} на задачу {task_id} с ролью {role}")
                return (True, None)
            return (False, "Не удалось назначить пользователя")
        except Exception as e:
            logger.error(f"Ошибка при назначении задачи: {e}")
            return (False, f"Ошибка: {str(e)}")
    
    def unassign_task(self, task_id: int, user_id: int, role: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Снять назначение пользователя с задачи"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return (False, "Задача не найдена")
        
        try:
            success = self.assignee_repo.delete(task_id, user_id, role)
            if success:
                # Если это был основной ответственный, сбрасываем assignee_id
                if role == 'assignee' or role is None:
                    if task.assignee_id == user_id:
                        self.task_repo.update(task_id, assignee_id=None)
                logger.info(f"Снято назначение пользователя {user_id} с задачи {task_id}")
                return (True, None)
            return (False, "Назначение не найдено")
        except Exception as e:
            logger.error(f"Ошибка при снятии назначения: {e}")
            return (False, f"Ошибка: {str(e)}")
    
    def get_user_tasks(self, user_id: int) -> List:
        """Получить все задачи пользователя (по assignee_id)"""
        return self.task_repo.get_by_assignee(user_id)
    
    def add_project_member(self, project_id: str, user_id: int, role: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Добавить участника проекта"""
        project = self.project_repo.get_by_id(project_id)
        if not project:
            return (False, None, "Проект не найден")
        
        try:
            member_id = self.member_repo.create(project_id, user_id, role)
            if member_id:
                logger.info(f"Добавлен участник {user_id} в проект {project_id} с ролью {role}")
                return (True, member_id, None)
            return (False, None, "Участник уже существует")
        except Exception as e:
            logger.error(f"Ошибка при добавлении участника проекта: {e}")
            return (False, None, f"Ошибка: {str(e)}")
    
    def get_project_members(self, project_id: str) -> List[ProjectMember]:
        """Получить всех участников проекта"""
        return self.member_repo.get_by_project(project_id)
    
    def get_user_projects(self, user_id: int) -> List[ProjectMember]:
        """Получить все проекты пользователя"""
        return self.member_repo.get_by_user(user_id)
    
    def determine_role_from_board(self, board_name: str) -> str:
        """Определить роль участника проекта на основе названия доски"""
        board_name_lower = board_name.lower()
        
        # Маппинг названий досок на роли
        role_mapping = {
            'дизайн': 'designer',
            'design': 'designer',
            'разработка': 'developer',
            'development': 'developer',
            'тестирование': 'tester',
            'testing': 'tester',
            'qa': 'tester',
            'подготовка': 'preparator',
            'preparation': 'preparator',
            'aso': 'aso_specialist',
            'store': 'store_manager',
            'подготовка аккаунта': 'account_manager',
        }
        
        for key, role in role_mapping.items():
            if key in board_name_lower:
                return role
        
        # По умолчанию
        return 'member'
    
    def auto_assign_on_move_to_work(self, task_id: int, user_id: int, column_id: int) -> Tuple[bool, Optional[str]]:
        """
        Автоматически назначить пользователя при перемещении задачи в "В работе"
        Также добавляет пользователя как участника проекта, если задача связана с проектом
        """
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return (False, "Задача не найдена")
        
        column = self.column_repo.get_by_id(column_id)
        if not column:
            return (False, "Колонка не найдена")
        
        board = self.board_repo.get_by_id(column.board_id)
        if not board:
            return (False, "Доска не найдена")
        
        # Проверяем, что колонка является "В работе" или похожей
        column_name_lower = column.name.lower()
        work_columns = ['в работе', 'in progress', 'doing', 'работа', 'work']
        is_work_column = any(work_col in column_name_lower for work_col in work_columns)
        
        if not is_work_column:
            return (True, None)  # Не требуется назначение
        
        # Назначаем пользователя на задачу
        assign_result = self.assign_task(task_id, user_id, 'assignee')
        if not assign_result[0]:
            return assign_result
        
        # Если задача связана с проектом, добавляем пользователя как участника проекта
        if task.project_id:
            role = self.determine_role_from_board(board.name)
            member_result = self.add_project_member(task.project_id, user_id, role)
            if not member_result[0] and member_result[2] != "Участник уже существует":
                logger.warning(f"Не удалось добавить участника проекта: {member_result[2]}")
        
        return (True, None)


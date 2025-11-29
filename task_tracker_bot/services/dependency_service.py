"""
Сервис для работы с зависимостями досок
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from repositories.board_dependency_repository import BoardDependencyRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from models.task import Task
from models.board_dependency import BoardDependency

logger = logging.getLogger(__name__)

class DependencyService:
    def __init__(self, dependency_repo: BoardDependencyRepository,
                 task_repo: TaskRepository, project_repo: ProjectRepository,
                 column_repo: ColumnRepository, board_repo: BoardRepository):
        self.dependency_repo = dependency_repo
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.column_repo = column_repo
        self.board_repo = board_repo
    
    def check_and_execute_dependencies(self, task_id: int, new_column_id: int) -> List[Tuple[bool, str]]:
        """
        Проверить и выполнить зависимости при перемещении задачи
        
        Returns:
            List of tuples (success, message)
        """
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return [(False, "Задача не найдена")]
        
        # Получить колонку назначения
        target_column = self.column_repo.get_by_id(new_column_id)
        if not target_column:
            return [(False, "Колонка не найдена")]
        
        # Получить доску колонки
        board = self.board_repo.get_by_id(target_column.board_id)
        if not board:
            return [(False, "Доска не найдена")]
        
        # Найти все зависимости для этой колонки
        dependencies = self.dependency_repo.get_by_source(
            source_board_id=board.id,
            source_column_id=new_column_id,
            trigger_type='enter'
        )
        
        if not dependencies:
            return []
        
        results = []
        
        for dependency in dependencies:
            try:
                if dependency.action_type == 'create_task':
                    result = self._execute_create_task_dependency(task, dependency)
                    results.append(result)
                elif dependency.action_type == 'move_task':
                    result = self._execute_move_task_dependency(task, dependency)
                    results.append(result)
                else:
                    logger.warning(f"Неизвестный тип действия зависимости: {dependency.action_type}")
                    results.append((False, f"Неизвестный тип действия: {dependency.action_type}"))
            except Exception as e:
                logger.error(f"Ошибка при выполнении зависимости {dependency.id}: {e}")
                results.append((False, f"Ошибка: {str(e)}"))
        
        return results
    
    def _execute_create_task_dependency(self, source_task: Task, dependency: BoardDependency) -> Tuple[bool, str]:
        """Выполнить зависимость создания задачи"""
        # Проверяем, что исходная задача связана с проектом
        if not source_task.project_id:
            return (False, "Исходная задача не связана с проектом")
        
        project = self.project_repo.get_by_id(source_task.project_id)
        if not project:
            return (False, f"Проект {source_task.project_id} не найден")
        
        # Формируем название задачи из шаблона
        task_title = self._format_task_title(dependency.task_title_template, project)
        if not task_title:
            task_title = f"{project.id} {project.name}"
        
        # Создаем задачу на целевой доске
        try:
            position = self.task_repo.get_max_position(dependency.target_column_id)
            new_task_id = self.task_repo.create(
                column_id=dependency.target_column_id,
                title=task_title,
                description=None,
                project_id=project.id,
                parent_task_id=None,
                priority=source_task.priority,
                position=position
            )
            logger.info(f"Создана задача {new_task_id} по зависимости {dependency.id}")
            return (True, f"Создана задача #{new_task_id}: {task_title}")
        except Exception as e:
            logger.error(f"Ошибка при создании задачи по зависимости: {e}")
            return (False, f"Ошибка создания задачи: {str(e)}")
    
    def _execute_move_task_dependency(self, source_task: Task, dependency: BoardDependency) -> Tuple[bool, str]:
        """Выполнить зависимость перемещения задачи"""
        # Находим задачу проекта на целевой доске
        if not source_task.project_id:
            return (False, "Исходная задача не связана с проектом")
        
        # Получаем все задачи проекта
        project_tasks = self.task_repo.get_all_by_project(source_task.project_id)
        
        # Находим задачу на целевой доске (по колонкам целевой доски)
        target_board = self.board_repo.get_by_id(dependency.target_board_id)
        if not target_board:
            return (False, "Целевая доска не найдена")
        
        # Получаем все колонки целевой доски
        from repositories.column_repository import ColumnRepository
        from database import Database
        db = Database()
        column_repo = ColumnRepository(db)
        target_columns = column_repo.get_all_by_board(dependency.target_board_id)
        target_column_ids = [col.id for col in target_columns]
        
        # Ищем задачу проекта на целевой доске
        target_task = None
        for task in project_tasks:
            if task.column_id in target_column_ids:
                target_task = task
                break
        
        if not target_task:
            return (False, f"Задача проекта {source_task.project_id} не найдена на целевой доске")
        
        # Перемещаем задачу в целевую колонку
        try:
            position = self.task_repo.get_max_position(dependency.target_column_id)
            success = self.task_repo.update(
                target_task.id,
                column_id=dependency.target_column_id,
                position=position
            )
            if success:
                logger.info(f"Перемещена задача {target_task.id} по зависимости {dependency.id}")
                return (True, f"Перемещена задача #{target_task.id} в колонку")
            return (False, "Ошибка при перемещении задачи")
        except Exception as e:
            logger.error(f"Ошибка при перемещении задачи по зависимости: {e}")
            return (False, f"Ошибка перемещения: {str(e)}")
    
    def _format_task_title(self, template: Optional[str], project) -> Optional[str]:
        """Форматировать название задачи из шаблона"""
        if not template:
            return None
        
        # Убираем кавычки из шаблона, если они есть
        template = template.strip()
        if template.startswith('"') and template.endswith('"'):
            template = template[1:-1]
        elif template.startswith("'") and template.endswith("'"):
            template = template[1:-1]
        
        try:
            formatted_title = template.format(
                project_id=project.id,
                project_name=project.name
            )
            # Обрезаем название до максимальной длины (500 символов)
            if len(formatted_title) > 500:
                formatted_title = formatted_title[:497] + "..."
            return formatted_title
        except Exception as e:
            logger.warning(f"Ошибка форматирования шаблона '{template}': {e}")
            return None
    
    def create_dependency(self, workspace_id: int, name: str, source_board_id: int,
                         source_column_id: int, trigger_type: str, target_board_id: int,
                         target_column_id: int, action_type: str,
                         task_title_template: Optional[str] = None) -> Tuple[bool, Optional[int], Optional[str]]:
        """Создать зависимость"""
        try:
            dependency_id = self.dependency_repo.create(
                workspace_id=workspace_id,
                name=name,
                source_board_id=source_board_id,
                source_column_id=source_column_id,
                trigger_type=trigger_type,
                target_board_id=target_board_id,
                target_column_id=target_column_id,
                action_type=action_type,
                task_title_template=task_title_template
            )
            return (True, dependency_id, None)
        except Exception as e:
            logger.error(f"Ошибка при создании зависимости: {e}")
            return (False, None, f"Ошибка: {str(e)}")
    
    def list_dependencies(self, workspace_id: int) -> List[BoardDependency]:
        """Получить все зависимости пространства"""
        return self.dependency_repo.get_all_by_workspace(workspace_id)
    
    def delete_dependency(self, dependency_id: int) -> Tuple[bool, Optional[str]]:
        """Удалить зависимость"""
        dependency = self.dependency_repo.get_by_id(dependency_id)
        if not dependency:
            return (False, "Зависимость не найдена")
        
        try:
            success = self.dependency_repo.delete(dependency_id)
            if success:
                return (True, None)
            return (False, "Ошибка при удалении зависимости")
        except Exception as e:
            logger.error(f"Ошибка при удалении зависимости: {e}")
            return (False, f"Ошибка: {str(e)}")


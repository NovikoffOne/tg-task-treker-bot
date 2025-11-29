"""
Сервис для работы с Task
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from repositories.task_repository import TaskRepository
from repositories.column_repository import ColumnRepository
from models.task import Task

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self, task_repo: TaskRepository, column_repo: ColumnRepository,
                 dependency_service=None, assignment_service=None):
        self.task_repo = task_repo
        self.column_repo = column_repo
        self.dependency_service = dependency_service
        self.assignment_service = assignment_service
    
    def create_task(self, column_id: int, title: str, description: Optional[str] = None,
                   project_id: Optional[str] = None, parent_task_id: Optional[int] = None,
                   priority: int = 0,
                   scheduled_date=None,
                   scheduled_time=None,
                   scheduled_time_end=None) -> tuple[bool, Optional[int], Optional[str]]:
        """Создать задачу"""
        from datetime import date, time
        
        # Валидация
        title = title.strip()
        if len(title) < 2:
            return False, None, "Название задачи должно быть минимум 2 символа"
        if len(title) > 500:
            return False, None, "Название задачи слишком длинное (максимум 500 символов)"
        if description and len(description) > 2000:
            return False, None, "Описание слишком длинное (максимум 2000 символов)"
        if priority < 0 or priority > 3:
            return False, None, "Приоритет должен быть от 0 до 3"
        
        # Проверка существования колонки
        column = self.column_repo.get_by_id(column_id)
        if not column:
            return False, None, "Колонка не найдена"
        
        try:
            position = self.task_repo.get_max_position(column_id)
            task_id = self.task_repo.create(
                column_id=column_id,
                title=title,
                description=description,
                project_id=project_id,
                parent_task_id=parent_task_id,
                priority=priority,
                position=position,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                scheduled_time_end=scheduled_time_end
            )
            return True, task_id, None
        except Exception as e:
            return False, None, f"Ошибка при создании задачи: {str(e)}"
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Получить задачу"""
        return self.task_repo.get_by_id(task_id)
    
    def list_tasks_by_column(self, column_id: int) -> List[Task]:
        """Получить все задачи колонки"""
        return self.task_repo.get_all_by_column(column_id)
    
    def list_tasks_by_project(self, project_id: str) -> List[Task]:
        """Получить все задачи проекта"""
        return self.task_repo.get_all_by_project(project_id)
    
    def get_subtasks(self, parent_task_id: int) -> List[Task]:
        """Получить подзадачи"""
        return self.task_repo.get_subtasks(parent_task_id)
    
    def update_task(self, task_id: int, title: Optional[str] = None,
                   description: Optional[str] = None, priority: Optional[int] = None) -> tuple[bool, Optional[str]]:
        """Обновить задачу"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False, "Задача не найдена"
        
        # Валидация
        if title is not None:
            title = title.strip()
            if len(title) < 2:
                return False, "Название задачи должно быть минимум 2 символа"
            if len(title) > 500:
                return False, "Название задачи слишком длинное (максимум 500 символов)"
        if description is not None and len(description) > 2000:
            return False, "Описание слишком длинное (максимум 2000 символов)"
        if priority is not None and (priority < 0 or priority > 3):
            return False, "Приоритет должен быть от 0 до 3"
        
        try:
            success = self.task_repo.update(task_id, title=title, description=description, priority=priority)
            if success:
                return True, None
            return False, "Ошибка при обновлении задачи"
        except Exception as e:
            return False, f"Ошибка при обновлении: {str(e)}"
    
    def move_task(self, task_id: int, column_id: int, user_id: Optional[int] = None) -> tuple[bool, Optional[str]]:
        """
        Переместить задачу в другую колонку
        С автоматическим трекингом дат и выполнением зависимостей
        """
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False, "Задача не найдена"
        
        column = self.column_repo.get_by_id(column_id)
        if not column:
            return False, "Колонка не найдена"
        
        old_column_id = task.column_id
        
        try:
            # Определяем, нужно ли трекать даты
            column_name_lower = column.name.lower()
            work_columns = ['в работе', 'in progress', 'doing', 'работа', 'work']
            done_columns = ['готово', 'done', 'completed', 'завершено', 'готов']
            
            is_work_column = any(work_col in column_name_lower for work_col in work_columns)
            is_done_column = any(done_col in column_name_lower for done_col in done_columns)
            
            # Автоматическое треканье дат
            started_at = None
            completed_at = None
            
            if is_work_column and not task.started_at:
                started_at = datetime.now()
                logger.info(f"Автоматически установлена дата начала для задачи {task_id}")
            
            if is_done_column and not task.completed_at:
                completed_at = datetime.now()
                logger.info(f"Автоматически установлена дата завершения для задачи {task_id}")
            
            position = self.task_repo.get_max_position(column_id)
            success = self.task_repo.update(
                task_id,
                column_id=column_id,
                position=position,
                started_at=started_at,
                completed_at=completed_at
            )
            
            if not success:
                return False, "Ошибка при перемещении задачи"
            
            # Автоматическое назначение при перемещении в "В работе"
            if is_work_column and user_id and self.assignment_service:
                assign_result = self.assignment_service.auto_assign_on_move_to_work(
                    task_id, user_id, column_id
                )
                if not assign_result[0]:
                    logger.warning(f"Не удалось автоматически назначить задачу: {assign_result[1]}")
            
            # Выполнение зависимостей досок
            if self.dependency_service:
                dependency_results = self.dependency_service.check_and_execute_dependencies(
                    task_id, column_id
                )
                for success, message in dependency_results:
                    if not success:
                        logger.warning(f"Ошибка выполнения зависимости: {message}")
            
            return True, None
        except Exception as e:
            logger.error(f"Ошибка при перемещении задачи: {e}")
            return False, f"Ошибка при перемещении: {str(e)}"
    
    def delete_task(self, task_id: int) -> tuple[bool, Optional[str]]:
        """Удалить задачу"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False, "Задача не найдена"
        
        try:
            success = self.task_repo.delete(task_id)
            if success:
                return True, None
            return False, "Ошибка при удалении задачи"
        except Exception as e:
            return False, f"Ошибка при удалении: {str(e)}"
    
    def create_subtask(self, parent_task_id: int, title: str, description: Optional[str] = None) -> tuple[bool, Optional[int], Optional[str]]:
        """Создать подзадачу"""
        parent_task = self.task_repo.get_by_id(parent_task_id)
        if not parent_task:
            return False, None, "Родительская задача не найдена"
        
        return self.create_task(
            column_id=parent_task.column_id,
            title=title,
            description=description,
            project_id=parent_task.project_id,
            parent_task_id=parent_task_id
        )
    
    def set_deadline(self, task_id: int, deadline: datetime) -> tuple[bool, Optional[str]]:
        """Установить дедлайн задачи"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False, "Задача не найдена"
        
        try:
            success = self.task_repo.update(task_id, deadline=deadline)
            if success:
                logger.info(f"Установлен дедлайн для задачи {task_id}: {deadline}")
                return True, None
            return False, "Ошибка при установке дедлайна"
        except Exception as e:
            logger.error(f"Ошибка при установке дедлайна: {e}")
            return False, f"Ошибка: {str(e)}"
    
    def get_overdue_tasks(self) -> List[Task]:
        """Получить все просроченные задачи"""
        return self.task_repo.get_overdue_tasks()
    
    def get_tasks_by_deadline(self, deadline_date: str) -> List[Task]:
        """Получить задачи с дедлайном на указанную дату"""
        return self.task_repo.get_by_deadline(deadline_date)


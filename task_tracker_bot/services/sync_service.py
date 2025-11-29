"""
Сервис синхронизации полей проекта
При добавлении поля к задаче проекта → синхронизирует со всеми задачами проекта
"""
from typing import Optional, Tuple
from repositories.task_repository import TaskRepository
from repositories.custom_field_repository import CustomFieldRepository

class SyncService:
    def __init__(self, task_repo: TaskRepository, field_repo: CustomFieldRepository):
        self.task_repo = task_repo
        self.field_repo = field_repo
    
    def sync_field_to_project(self, task_id: int, field_id: int, value: str) -> tuple[bool, Optional[str]]:
        """Синхронизировать поле задачи проекта со всеми задачами проекта"""
        # Получить задачу
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False, "Задача не найдена"
        
        # Проверить, что задача принадлежит проекту
        if not task.project_id:
            # Просто добавить поле к задаче без синхронизации
            try:
                self.field_repo.set_task_field(task_id, field_id, value)
                return True, None
            except Exception as e:
                return False, f"Ошибка при добавлении поля: {str(e)}"
        
        # Проверить, включена ли синхронизация для этого поля
        sync_enabled = self.field_repo.is_sync_enabled(task.project_id, field_id)
        if not sync_enabled:
            # Автоматически включить синхронизацию при первом добавлении поля к задаче проекта
            self.field_repo.enable_project_sync(task.project_id, field_id)
        
        # Получить все задачи проекта
        project_tasks = self.task_repo.get_all_by_project(task.project_id)
        
        # Добавить поле ко всем задачам проекта
        try:
            for project_task in project_tasks:
                self.field_repo.set_task_field(project_task.id, field_id, value)
            return True, None
        except Exception as e:
            return False, f"Ошибка при синхронизации поля: {str(e)}"
    
    def update_field_in_project(self, task_id: int, field_id: int, value: str) -> tuple[bool, Optional[str]]:
        """Обновить поле задачи проекта (синхронизировать со всеми задачами)"""
        return self.sync_field_to_project(task_id, field_id, value)
    
    def remove_field_from_project(self, task_id: int, field_id: int) -> tuple[bool, Optional[str]]:
        """Удалить поле из всех задач проекта"""
        # Получить задачу
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False, "Задача не найдена"
        
        # Проверить, что задача принадлежит проекту
        if not task.project_id:
            # Просто удалить поле у задачи
            try:
                self.field_repo.delete_task_field(task_id, field_id)
                return True, None
            except Exception as e:
                return False, f"Ошибка при удалении поля: {str(e)}"
        
        # Проверить, включена ли синхронизация
        sync_enabled = self.field_repo.is_sync_enabled(task.project_id, field_id)
        if not sync_enabled:
            # Синхронизация отключена, удалить только у текущей задачи
            try:
                self.field_repo.delete_task_field(task_id, field_id)
                return True, None
            except Exception as e:
                return False, f"Ошибка при удалении поля: {str(e)}"
        
        # Получить все задачи проекта
        project_tasks = self.task_repo.get_all_by_project(task.project_id)
        
        # Удалить поле у всех задач проекта
        try:
            for project_task in project_tasks:
                self.field_repo.delete_task_field(project_task.id, field_id)
            return True, None
        except Exception as e:
            return False, f"Ошибка при синхронизации удаления поля: {str(e)}"


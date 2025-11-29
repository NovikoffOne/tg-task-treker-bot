"""
Сервис для работы с Workspace
"""
from typing import List, Optional
from repositories.workspace_repository import WorkspaceRepository
from models.workspace import Workspace

class WorkspaceService:
    def __init__(self, workspace_repo: WorkspaceRepository):
        self.workspace_repo = workspace_repo
    
    def create_workspace(self, user_id: int, name: str) -> tuple[bool, Optional[int], Optional[str]]:
        """Создать пространство"""
        # Валидация
        name = name.strip()
        if len(name) < 2:
            return False, None, "Название пространства должно быть минимум 2 символа"
        if len(name) > 100:
            return False, None, "Название пространства слишком длинное (максимум 100 символов)"
        
        # Проверка уникальности
        existing = self.workspace_repo.get_by_name(user_id, name)
        if existing:
            return False, None, "Пространство с таким названием уже существует"
        
        try:
            workspace_id = self.workspace_repo.create(user_id, name)
            return True, workspace_id, None
        except Exception as e:
            return False, None, f"Ошибка при создании пространства: {str(e)}"
    
    def get_workspace(self, workspace_id: int, user_id: int) -> Optional[Workspace]:
        """Получить пространство"""
        return self.workspace_repo.get_by_id(workspace_id, user_id)
    
    def get_workspace_by_name(self, user_id: int, name: str) -> Optional[Workspace]:
        """Получить пространство по имени"""
        return self.workspace_repo.get_by_name(user_id, name)
    
    def list_workspaces(self, user_id: int) -> List[Workspace]:
        """Получить все пространства пользователя"""
        return self.workspace_repo.get_all_by_user(user_id)
    
    def rename_workspace(self, workspace_id: int, user_id: int, new_name: str) -> tuple[bool, Optional[str]]:
        """Переименовать пространство"""
        # Валидация
        new_name = new_name.strip()
        if len(new_name) < 2:
            return False, "Название пространства должно быть минимум 2 символа"
        if len(new_name) > 100:
            return False, "Название пространства слишком длинное (максимум 100 символов)"
        
        # Проверка существования
        workspace = self.workspace_repo.get_by_id(workspace_id, user_id)
        if not workspace:
            return False, "Пространство не найдено"
        
        # Проверка уникальности
        existing = self.workspace_repo.get_by_name(user_id, new_name)
        if existing and existing.id != workspace_id:
            return False, "Пространство с таким названием уже существует"
        
        try:
            success = self.workspace_repo.update(workspace_id, user_id, new_name)
            if success:
                return True, None
            return False, "Ошибка при обновлении пространства"
        except Exception as e:
            return False, f"Ошибка при переименовании: {str(e)}"
    
    def delete_workspace(self, workspace_id: int, user_id: int) -> tuple[bool, Optional[str]]:
        """Удалить пространство"""
        # Проверка существования
        workspace = self.workspace_repo.get_by_id(workspace_id, user_id)
        if not workspace:
            return False, "Пространство не найдено"
        
        try:
            success = self.workspace_repo.delete(workspace_id, user_id)
            if success:
                return True, None
            return False, "Ошибка при удалении пространства"
        except Exception as e:
            return False, f"Ошибка при удалении: {str(e)}"


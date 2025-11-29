"""
Тесты для сервиса синхронизации полей
"""
import pytest
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
from repositories.custom_field_repository import CustomFieldRepository
from services.sync_service import SyncService

def test_sync_field_to_project(temp_db, sample_user_id):
    """Тест синхронизации поля для проекта"""
    # Создать структуру
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Очередь")
    
    project_repo = ProjectRepository(temp_db)
    project_repo.create("TEST001", workspace_id, "Тестовый проект")
    
    task_repo = TaskRepository(temp_db)
    task_id1 = task_repo.create(column_id, "Задача 1", project_id="TEST001")
    task_id2 = task_repo.create(column_id, "Задача 2", project_id="TEST001")
    
    field_repo = CustomFieldRepository(temp_db)
    field_id = field_repo.create(workspace_id, "Figma", "url")
    
    sync_service = SyncService(task_repo, field_repo)
    
    # Синхронизировать поле (синхронизация включается автоматически)
    success, error = sync_service.sync_field_to_project(task_id1, field_id, "https://figma.com/test")
    assert success is True
    assert error is None
    
    # Проверить, что поле добавлено ко всем задачам проекта
    value1 = field_repo.get_task_field(task_id1, field_id)
    value2 = field_repo.get_task_field(task_id2, field_id)
    
    assert value1 == "https://figma.com/test"
    assert value2 == "https://figma.com/test"  # Синхронизировано!

def test_sync_field_non_project_task(temp_db, sample_user_id):
    """Тест добавления поля к задаче без проекта (без синхронизации)"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Очередь")
    
    task_repo = TaskRepository(temp_db)
    task_id = task_repo.create(column_id, "Задача без проекта")
    
    field_repo = CustomFieldRepository(temp_db)
    field_id = field_repo.create(workspace_id, "Figma", "url")
    
    sync_service = SyncService(task_repo, field_repo)
    
    # Добавить поле (без синхронизации, т.к. нет проекта)
    success, error = sync_service.sync_field_to_project(task_id, field_id, "https://figma.com/test")
    assert success is True
    
    # Проверить, что поле добавлено только к этой задаче
    value = field_repo.get_task_field(task_id, field_id)
    assert value == "https://figma.com/test"


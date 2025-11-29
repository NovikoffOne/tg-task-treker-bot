"""
Тесты для репозиториев
"""
import pytest
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
from repositories.tag_repository import TagRepository
from repositories.custom_field_repository import CustomFieldRepository

def test_workspace_repository_create(temp_db, sample_user_id):
    """Тест создания пространства"""
    repo = WorkspaceRepository(temp_db)
    workspace_id = repo.create(sample_user_id, "Тестовое пространство")
    assert workspace_id > 0
    
    workspace = repo.get_by_id(workspace_id, sample_user_id)
    assert workspace is not None
    assert workspace.name == "Тестовое пространство"
    assert workspace.user_id == sample_user_id

def test_workspace_repository_get_all(temp_db, sample_user_id):
    """Тест получения всех пространств"""
    repo = WorkspaceRepository(temp_db)
    repo.create(sample_user_id, "Пространство 1")
    repo.create(sample_user_id, "Пространство 2")
    
    workspaces = repo.get_all_by_user(sample_user_id)
    assert len(workspaces) == 2

def test_board_repository_create(temp_db, sample_user_id):
    """Тест создания доски"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    assert board_id > 0
    
    board = board_repo.get_by_id(board_id)
    assert board is not None
    assert board.name == "Тестовая доска"
    assert board.workspace_id == workspace_id

def test_column_repository_create(temp_db, sample_user_id):
    """Тест создания колонки"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Тестовая колонка")
    assert column_id > 0
    
    column = column_repo.get_by_id(column_id)
    assert column is not None
    assert column.name == "Тестовая колонка"
    assert column.board_id == board_id

def test_project_repository_create(temp_db, sample_user_id):
    """Тест создания проекта"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    project_repo = ProjectRepository(temp_db)
    project_id = project_repo.create("TEST001", workspace_id, "Тестовый проект")
    assert project_id == "TEST001"
    
    project = project_repo.get_by_id(project_id)
    assert project is not None
    assert project.name == "Тестовый проект"
    assert project.workspace_id == workspace_id

def test_task_repository_create(temp_db, sample_user_id):
    """Тест создания задачи"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Тестовая колонка")
    
    task_repo = TaskRepository(temp_db)
    task_id = task_repo.create(column_id, "Тестовая задача", "Описание задачи")
    assert task_id > 0
    
    task = task_repo.get_by_id(task_id)
    assert task is not None
    assert task.title == "Тестовая задача"
    assert task.description == "Описание задачи"
    assert task.column_id == column_id

def test_tag_repository_create(temp_db, sample_user_id):
    """Тест создания метки"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    tag_repo = TagRepository(temp_db)
    tag_id = tag_repo.create(workspace_id, "тест", "#FF0000")
    assert tag_id > 0
    
    tag = tag_repo.get_by_id(tag_id)
    assert tag is not None
    assert tag.name == "тест"
    assert tag.color == "#FF0000"

def test_custom_field_repository_create(temp_db, sample_user_id):
    """Тест создания поля"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    field_repo = CustomFieldRepository(temp_db)
    field_id = field_repo.create(workspace_id, "Figma", "url")
    assert field_id > 0
    
    field = field_repo.get_by_id(field_id)
    assert field is not None
    assert field.name == "Figma"
    assert field.field_type == "url"


"""
Тесты для сервисов
"""
import pytest
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
from services.workspace_service import WorkspaceService
from services.board_service import BoardService
from services.project_service import ProjectService
from services.task_service import TaskService

def test_workspace_service_create(temp_db, sample_user_id):
    """Тест создания пространства через сервис"""
    workspace_repo = WorkspaceRepository(temp_db)
    service = WorkspaceService(workspace_repo)
    
    success, workspace_id, error = service.create_workspace(sample_user_id, "Тестовое пространство")
    assert success is True
    assert workspace_id > 0
    assert error is None
    
    workspace = service.get_workspace(workspace_id, sample_user_id)
    assert workspace is not None
    assert workspace.name == "Тестовое пространство"

def test_workspace_service_validation(temp_db, sample_user_id):
    """Тест валидации при создании пространства"""
    workspace_repo = WorkspaceRepository(temp_db)
    service = WorkspaceService(workspace_repo)
    
    # Слишком короткое имя
    success, workspace_id, error = service.create_workspace(sample_user_id, "A")
    assert success is False
    assert workspace_id is None
    assert error is not None
    
    # Дубликат имени
    service.create_workspace(sample_user_id, "Тестовое пространство")
    success, workspace_id, error = service.create_workspace(sample_user_id, "Тестовое пространство")
    assert success is False
    assert "уже существует" in error

def test_board_service_create_with_default_columns(temp_db, sample_user_id):
    """Тест создания доски с дефолтными колонками"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    column_repo = ColumnRepository(temp_db)
    service = BoardService(board_repo, column_repo)
    
    success, board_id, error = service.create_board(workspace_id, "Тестовая доска")
    assert success is True
    assert board_id > 0
    assert error is None
    
    # Проверить, что созданы дефолтные колонки
    columns = service.list_columns(board_id)
    assert len(columns) == 3
    assert any(col.name == "Очередь" for col in columns)
    assert any(col.name == "В работе" for col in columns)
    assert any(col.name == "Готово" for col in columns)

def test_project_service_create_with_tasks(temp_db, sample_user_id):
    """Тест создания проекта с задачей только на доске подготовки"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id1 = board_repo.create(workspace_id, "Подготовка")
    board_id2 = board_repo.create(workspace_id, "Доска 2")
    
    column_repo = ColumnRepository(temp_db)
    column_repo.create(board_id1, "Очередь")
    column_repo.create(board_id2, "Очередь")
    
    project_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    service = ProjectService(project_repo, board_repo, column_repo, task_repo)
    
    success, project_id, error = service.create_project("TEST001", workspace_id, "Тестовый проект")
    assert success is True
    assert project_id == "TEST001"
    assert error is None
    
    # Проверить, что создана задача только на доске "Подготовка"
    tasks = task_repo.get_all_by_project("TEST001")
    assert len(tasks) == 1  # Только одна задача на доске "Подготовка"
    
    # Проверить название задачи
    task = tasks[0]
    assert "TEST001" in task.title
    assert "Тестовый проект" in task.title
    assert "Подготовка" in task.title

def test_task_service_create(temp_db, sample_user_id):
    """Тест создания задачи через сервис"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Тестовая колонка")
    
    task_repo = TaskRepository(temp_db)
    service = TaskService(task_repo, column_repo)
    
    success, task_id, error = service.create_task(column_id, "Тестовая задача", "Описание")
    assert success is True
    assert task_id > 0
    assert error is None
    
    task = service.get_task(task_id)
    assert task is not None
    assert task.title == "Тестовая задача"

def test_task_service_validation(temp_db, sample_user_id):
    """Тест валидации при создании задачи"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Тестовое пространство")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Тестовая доска")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Тестовая колонка")
    
    task_repo = TaskRepository(temp_db)
    service = TaskService(task_repo, column_repo)
    
    # Слишком короткое название
    success, task_id, error = service.create_task(column_id, "A", "Описание")
    assert success is False
    assert task_id is None
    assert error is not None
    
    # Несуществующая колонка
    success, task_id, error = service.create_task(99999, "Тестовая задача", "Описание")
    assert success is False
    assert "не найдена" in error


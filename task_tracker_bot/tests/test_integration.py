"""
Интеграционные тесты - проверка работы всей системы
"""
import pytest
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
from repositories.custom_field_repository import CustomFieldRepository
from services.workspace_service import WorkspaceService
from services.board_service import BoardService
from services.project_service import ProjectService
from services.task_service import TaskService
from services.sync_service import SyncService

def test_full_workflow_create_project_with_tasks(temp_db, sample_user_id):
    """Полный workflow: создание пространства → доски → проекта → задач"""
    # 1. Создать пространство
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_service = WorkspaceService(workspace_repo)
    success, workspace_id, error = workspace_service.create_workspace(sample_user_id, "Работа")
    assert success is True
    
    # 2. Создать доски
    board_repo = BoardRepository(temp_db)
    column_repo = ColumnRepository(temp_db)
    board_service = BoardService(board_repo, column_repo)
    
    success, board_id1, error = board_service.create_board(workspace_id, "Подготовка")
    assert success is True
    
    success, board_id2, error = board_service.create_board(workspace_id, "Дизайн")
    assert success is True
    
    success, board_id3, error = board_service.create_board(workspace_id, "Разработка")
    assert success is True
    
    # 3. Создать проект (задача создается только на доске "Подготовка")
    project_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    project_service = ProjectService(project_repo, board_repo, column_repo, task_repo)
    
    success, project_id, error = project_service.create_project("5010", workspace_id, "Nano Banana Ai")
    assert success is True
    assert project_id == "5010"
    
    # 4. Проверить, что задача создана только на доске "Подготовка"
    tasks = task_repo.get_all_by_project("5010")
    assert len(tasks) == 1  # Только одна задача на доске "Подготовка"
    
    # 5. Проверить название задачи
    task = tasks[0]
    assert "5010" in task.title
    assert "Nano Banana Ai" in task.title
    assert "Подготовка" in task.title

def test_sync_field_workflow(temp_db, sample_user_id):
    """Workflow синхронизации полей проекта"""
    # Создать структуру
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Работа")
    
    board_repo = BoardRepository(temp_db)
    column_repo = ColumnRepository(temp_db)
    board_service = BoardService(board_repo, column_repo)
    
    # Создать доску с дефолтными колонками
    success, board_id, error = board_service.create_board(workspace_id, "Дизайн")
    assert success is True
    
    column_id = column_repo.get_first_by_board(board_id).id
    
    project_repo = ProjectRepository(temp_db)
    project_repo.create("5010", workspace_id, "Nano Banana Ai")
    
    task_repo = TaskRepository(temp_db)
    task_id1 = task_repo.create(column_id, "5010 Nano Banana Ai Дизайн", project_id="5010")
    task_id2 = task_repo.create(column_id, "5010 Nano Banana Ai Разработка", project_id="5010")
    
    # Создать поле
    field_repo = CustomFieldRepository(temp_db)
    field_id = field_repo.create(workspace_id, "Figma", "url")
    
    # Добавить поле к первой задаче (синхронизация включается автоматически)
    sync_service = SyncService(task_repo, field_repo)
    success, error = sync_service.sync_field_to_project(task_id1, field_id, "https://figma.com/file/123")
    assert success is True
    
    # Проверить синхронизацию
    value1 = field_repo.get_task_field(task_id1, field_id)
    value2 = field_repo.get_task_field(task_id2, field_id)
    
    assert value1 == "https://figma.com/file/123"
    assert value2 == "https://figma.com/file/123"  # Синхронизировано!

def test_move_task_between_columns(temp_db, sample_user_id):
    """Тест перемещения задачи между колонками"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Работа")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Дизайн")
    
    column_repo = ColumnRepository(temp_db)
    column_id1 = column_repo.create(board_id, "Очередь", 0)
    column_id2 = column_repo.create(board_id, "В работе", 1)
    
    task_repo = TaskRepository(temp_db)
    task_service = TaskService(task_repo, column_repo)
    
    # Создать задачу
    success, task_id, error = task_service.create_task(column_id1, "Тестовая задача")
    assert success is True
    
    task = task_service.get_task(task_id)
    assert task.column_id == column_id1
    
    # Переместить задачу
    success, error = task_service.move_task(task_id, column_id2)
    assert success is True
    
    task = task_service.get_task(task_id)
    assert task.column_id == column_id2

def test_project_dashboard_stage_update(temp_db, sample_user_id):
    """Тест обновления этапа дашборда проекта"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Работа")
    
    project_repo = ProjectRepository(temp_db)
    project_repo.create("5010", workspace_id, "Nano Banana Ai")
    
    project_service = ProjectService(project_repo, None, None, None)
    
    # Обновить этап
    success, error = project_service.update_dashboard_stage("5010", "development")
    assert success is True
    
    project = project_service.get_project("5010")
    assert project.dashboard_stage == "development"


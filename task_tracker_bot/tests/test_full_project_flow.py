"""
Интеграционные тесты для полного цикла работы с проектом
"""
import pytest
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
from repositories.custom_field_repository import CustomFieldRepository
from repositories.tag_repository import TagRepository
from services.workspace_service import WorkspaceService
from services.board_service import BoardService
from services.project_service import ProjectService
from services.task_service import TaskService
from services.sync_service import SyncService


def test_full_project_workflow(temp_db, sample_user_id):
    """Полный цикл работы с проектом: создание → добавление полей → синхронизация"""
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
    
    success, project_id, error = project_service.create_project("5001", workspace_id, "Pictory Ai")
    assert success is True
    assert project_id == "5001"
    
    # 4. Проверить, что задача создана только на доске "Подготовка"
    tasks = task_repo.get_all_by_project("5001")
    assert len(tasks) == 1  # Только одна задача на доске "Подготовка"
    assert "Подготовка" in tasks[0].title
    
    # 5. Создать поле
    field_repo = CustomFieldRepository(temp_db)
    field_id = field_repo.create(workspace_id, "ТЗ", "url")
    assert field_id > 0
    
    # 6. Добавить поле к задаче (синхронизация включается автоматически)
    sync_service = SyncService(task_repo, field_repo)
    task_id1 = tasks[0].id
    success, error = sync_service.sync_field_to_project(
        task_id1, field_id, "https://docs.google.com/document/d/123"
    )
    assert success is True
    
    # 7. Проверить синхронизацию - задача должна иметь поле
    # (на данный момент есть только одна задача на доске "Подготовка")
    task = tasks[0]
    value = field_repo.get_task_field(task.id, field_id)
    assert value == "https://docs.google.com/document/d/123"
    
    # 8. Добавить еще одно поле
    field_id2 = field_repo.create(workspace_id, "Figma", "url")
    
    # 9. Добавить поле к задаче (синхронизация включается автоматически)
    success, error = sync_service.sync_field_to_project(
        task.id, field_id2, "https://figma.com/file/456"
    )
    assert success is True
    
    # 10. Проверить, что задача имеет оба поля
    value1 = field_repo.get_task_field(task.id, field_id)
    value2 = field_repo.get_task_field(task.id, field_id2)
    assert value1 == "https://docs.google.com/document/d/123"
    assert value2 == "https://figma.com/file/456"


def test_project_task_movement(temp_db, sample_user_id):
    """Тест перемещения задач проекта и автоматического треканья дат"""
    # Создать структуру
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Работа")
    
    board_repo = BoardRepository(temp_db)
    column_repo = ColumnRepository(temp_db)
    board_service = BoardService(board_repo, column_repo)
    
    success, board_id, error = board_service.create_board(workspace_id, "Дизайн")
    assert success is True
    
    columns = board_service.list_columns(board_id)
    queue_column = next(c for c in columns if c.name == "Очередь")
    work_column = next(c for c in columns if c.name == "В работе")
    done_column = next(c for c in columns if c.name == "Готово")
    
    # Создать доску "Подготовка" для проекта
    success, prep_board_id, error = board_service.create_board(workspace_id, "Подготовка")
    assert success is True
    
    # Создать проект
    project_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    project_service = ProjectService(project_repo, board_repo, column_repo, task_repo)
    
    success, project_id, error = project_service.create_project("5001", workspace_id, "Test Project")
    assert success is True
    
    # Получить задачу проекта (должна быть только на доске "Подготовка")
    tasks = task_repo.get_all_by_project("5001")
    assert len(tasks) == 1  # Только одна задача на доске "Подготовка"
    task = tasks[0]
    
    # Переместить в "В работе"
    task_service = TaskService(task_repo, column_repo)
    success, error = task_service.move_task(task.id, work_column.id)
    assert success is True
    
    # Проверить, что started_at установлена
    updated_task = task_repo.get_by_id(task.id)
    assert updated_task.started_at is not None
    
    # Переместить в "Готово"
    success, error = task_service.move_task(task.id, done_column.id)
    assert success is True
    
    # Проверить, что completed_at установлена
    updated_task = task_repo.get_by_id(task.id)
    assert updated_task.completed_at is not None


def test_project_with_multiple_fields(temp_db, sample_user_id):
    """Тест проекта с множеством полей"""
    # Создать структуру
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Работа")
    
    board_repo = BoardRepository(temp_db)
    column_repo = ColumnRepository(temp_db)
    board_service = BoardService(board_repo, column_repo)
    
    success, board_id, error = board_service.create_board(workspace_id, "Подготовка")
    assert success is True
    
    # Создать проект
    project_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    project_service = ProjectService(project_repo, board_repo, column_repo, task_repo)
    
    success, project_id, error = project_service.create_project("5001", workspace_id, "Test Project")
    assert success is True
    
    tasks = task_repo.get_all_by_project("5001")
    assert len(tasks) == 1  # Только одна задача на доске "Подготовка"
    
    # Создать несколько полей
    field_repo = CustomFieldRepository(temp_db)
    sync_service = SyncService(task_repo, field_repo)
    
    fields = [
        ("ТЗ", "url", "https://docs.google.com/document/d/123"),
        ("Figma", "url", "https://figma.com/file/456"),
        ("GitHub", "url", "https://github.com/repo"),
    ]
    
    for field_name, field_type, field_value in fields:
        field_id = field_repo.create(workspace_id, field_name, field_type)
        
        # Добавить к задаче (синхронизация включается автоматически)
        success, error = sync_service.sync_field_to_project(tasks[0].id, field_id, field_value)
        assert success is True
    
    # Проверить, что задача имеет все поля
    task = tasks[0]
    for field_name, _, expected_value in fields:
        field = field_repo.get_by_name(workspace_id, field_name)
        value = field_repo.get_task_field(task.id, field.id)
        assert value == expected_value


def test_project_tags(temp_db, sample_user_id):
    """Тест добавления меток к задачам проекта"""
    # Создать структуру
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Работа")
    
    board_repo = BoardRepository(temp_db)
    column_repo = ColumnRepository(temp_db)
    board_service = BoardService(board_repo, column_repo)
    
    success, board_id, error = board_service.create_board(workspace_id, "Подготовка")
    assert success is True
    
    # Создать проект
    project_repo = ProjectRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    project_service = ProjectService(project_repo, board_repo, column_repo, task_repo)
    
    success, project_id, error = project_service.create_project("5001", workspace_id, "Test Project")
    assert success is True
    
    tasks = task_repo.get_all_by_project("5001")
    assert len(tasks) == 1  # Только одна задача на доске "Подготовка"
    
    # Создать метку
    tag_repo = TagRepository(temp_db)
    tag_id = tag_repo.create(workspace_id, "И1", "#FF5733")
    
    # Добавить метку к задаче
    success = tag_repo.add_to_task(tasks[0].id, tag_id)
    assert success is True
    
    # Проверить, что метка добавлена
    tags = tag_repo.get_task_tags(tasks[0].id)
    assert len(tags) == 1
    assert tags[0].name == "И1"


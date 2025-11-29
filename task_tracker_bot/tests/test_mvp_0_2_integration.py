"""
Интеграционные тесты для MVP 0.2
"""
import pytest
from datetime import datetime
from database import Database
from repositories.task_repository import TaskRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_dependency_repository import BoardDependencyRepository
from repositories.project_repository import ProjectRepository
from repositories.task_assignee_repository import TaskAssigneeRepository
from repositories.project_member_repository import ProjectMemberRepository
from services.task_service import TaskService
from services.dependency_service import DependencyService
from services.assignment_service import AssignmentService

@pytest.fixture
def mvp_0_2_setup(temp_db, sample_user_id):
    """Настройка для интеграционных тестов MVP 0.2"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Test Workspace")
    
    board_repo = BoardRepository(temp_db)
    board1_id = board_repo.create(workspace_id, "Подготовка")
    board2_id = board_repo.create(workspace_id, "Дизайн")
    
    column_repo = ColumnRepository(temp_db)
    col1_id = column_repo.create(board1_id, "Очередь")
    col2_id = column_repo.create(board1_id, "Готово")
    col3_id = column_repo.create(board2_id, "Очередь")
    col4_id = column_repo.create(board2_id, "В работе")
    
    project_repo = ProjectRepository(temp_db)
    project_id = project_repo.create("5001", workspace_id, "Test Project")
    
    task_repo = TaskRepository(temp_db)
    dependency_repo = BoardDependencyRepository(temp_db)
    assignee_repo = TaskAssigneeRepository(temp_db)
    member_repo = ProjectMemberRepository(temp_db)
    
    dependency_service = DependencyService(
        dependency_repo, task_repo, project_repo, column_repo, board_repo
    )
    assignment_service = AssignmentService(
        assignee_repo, member_repo, task_repo, project_repo, column_repo, board_repo
    )
    task_service = TaskService(task_repo, column_repo, dependency_service, assignment_service)
    
    return {
        'workspace_id': workspace_id,
        'board1_id': board1_id,
        'board2_id': board2_id,
        'col1_id': col1_id,
        'col2_id': col2_id,
        'col3_id': col3_id,
        'col4_id': col4_id,
        'project_id': project_id,
        'task_service': task_service,
        'dependency_service': dependency_service,
        'assignment_service': assignment_service,
        'task_repo': task_repo,
        'user_id': sample_user_id
    }

def test_auto_track_dates_on_move(mvp_0_2_setup):
    """Тест автоматического трекинга дат при перемещении"""
    setup = mvp_0_2_setup
    
    # Создать задачу
    success, task_id, error = setup['task_service'].create_task(
        setup['col1_id'], "Test Task", project_id=setup['project_id']
    )
    assert success is True
    
    # Переместить в "В работе"
    success, error = setup['task_service'].move_task(
        task_id, setup['col4_id'], setup['user_id']
    )
    assert success is True
    
    # Проверить, что started_at установлена
    task = setup['task_service'].get_task(task_id)
    assert task.started_at is not None
    
    # Переместить в "Готово"
    success, error = setup['task_service'].move_task(
        task_id, setup['col2_id'], setup['user_id']
    )
    assert success is True
    
    # Проверить, что completed_at установлена
    task = setup['task_service'].get_task(task_id)
    assert task.completed_at is not None

def test_auto_assign_on_move_to_work(mvp_0_2_setup):
    """Тест автоматического назначения при перемещении в 'В работе'"""
    setup = mvp_0_2_setup
    
    # Создать задачу проекта
    success, task_id, error = setup['task_service'].create_task(
        setup['col1_id'], "Test Task", project_id=setup['project_id']
    )
    assert success is True
    
    # Переместить в "В работе"
    success, error = setup['task_service'].move_task(
        task_id, setup['col4_id'], setup['user_id']
    )
    assert success is True
    
    # Проверить назначение
    task = setup['task_service'].get_task(task_id)
    assert task.assignee_id == setup['user_id']
    
    # Проверить добавление в участники проекта
    members = setup['assignment_service'].get_project_members(setup['project_id'])
    assert len(members) > 0
    assert any(m.user_id == setup['user_id'] for m in members)

def test_set_deadline(mvp_0_2_setup):
    """Тест установки дедлайна"""
    setup = mvp_0_2_setup
    
    # Создать задачу
    success, task_id, error = setup['task_service'].create_task(
        setup['col1_id'], "Test Task"
    )
    assert success is True
    
    # Установить дедлайн
    deadline = datetime(2025, 12, 31, 18, 0)
    success, error = setup['task_service'].set_deadline(task_id, deadline)
    assert success is True
    
    # Проверить дедлайн
    task = setup['task_service'].get_task(task_id)
    assert task.deadline is not None

def test_get_tasks_by_deadline(mvp_0_2_setup):
    """Тест получения задач по дедлайну"""
    setup = mvp_0_2_setup
    
    # Создать задачу с дедлайном на сегодня
    success, task_id, error = setup['task_service'].create_task(
        setup['col1_id'], "Test Task"
    )
    assert success is True
    
    today = datetime.now().replace(hour=23, minute=59)
    setup['task_service'].set_deadline(task_id, today)
    
    # Получить задачи на сегодня
    today_str = today.strftime("%Y-%m-%d")
    tasks = setup['task_service'].get_tasks_by_deadline(today_str)
    assert len(tasks) >= 1
    assert any(t.id == task_id for t in tasks)


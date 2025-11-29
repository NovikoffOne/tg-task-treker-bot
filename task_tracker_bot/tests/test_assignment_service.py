"""
Тесты для AssignmentService
"""
import pytest
from database import Database
from repositories.task_assignee_repository import TaskAssigneeRepository
from repositories.project_member_repository import ProjectMemberRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from services.assignment_service import AssignmentService

@pytest.fixture
def assignment_service(temp_db, sample_user_id):
    """Создать AssignmentService для тестов"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Test Workspace")
    
    board_repo = BoardRepository(temp_db)
    board_id = board_repo.create(workspace_id, "Test Board")
    
    column_repo = ColumnRepository(temp_db)
    column_id = column_repo.create(board_id, "Test Column")
    
    task_repo = TaskRepository(temp_db)
    task_id = task_repo.create(column_id, "Test Task")
    
    project_repo = ProjectRepository(temp_db)
    project_id = project_repo.create("TEST001", workspace_id, "Test Project")
    
    assignee_repo = TaskAssigneeRepository(temp_db)
    member_repo = ProjectMemberRepository(temp_db)
    
    service = AssignmentService(
        assignee_repo, member_repo, task_repo, project_repo, column_repo, board_repo
    )
    
    return service, task_id, project_id, column_id, sample_user_id

def test_assign_task(assignment_service):
    """Тест назначения задачи"""
    service, task_id, project_id, column_id, user_id = assignment_service
    
    success, error = service.assign_task(task_id, user_id, 'assignee')
    assert success is True
    assert error is None

def test_get_user_tasks(assignment_service):
    """Тест получения задач пользователя"""
    service, task_id, project_id, column_id, user_id = assignment_service
    
    # Назначить задачу
    service.assign_task(task_id, user_id, 'assignee')
    
    # Получить задачи пользователя
    tasks = service.get_user_tasks(user_id)
    assert len(tasks) == 1
    assert tasks[0].id == task_id

def test_add_project_member(assignment_service):
    """Тест добавления участника проекта"""
    service, task_id, project_id, column_id, user_id = assignment_service
    
    success, member_id, error = service.add_project_member(project_id, user_id, 'developer')
    assert success is True
    assert member_id is not None
    assert error is None

def test_get_project_members(assignment_service):
    """Тест получения участников проекта"""
    service, task_id, project_id, column_id, user_id = assignment_service
    
    # Добавить участника
    service.add_project_member(project_id, user_id, 'developer')
    
    # Получить участников
    members = service.get_project_members(project_id)
    assert len(members) == 1
    assert members[0].user_id == user_id
    assert members[0].role == 'developer'

def test_determine_role_from_board(assignment_service):
    """Тест определения роли по названию доски"""
    service, task_id, project_id, column_id, user_id = assignment_service
    
    assert service.determine_role_from_board("Дизайн") == 'designer'
    assert service.determine_role_from_board("Разработка") == 'developer'
    assert service.determine_role_from_board("Тестирование") == 'tester'
    assert service.determine_role_from_board("Неизвестная доска") == 'member'


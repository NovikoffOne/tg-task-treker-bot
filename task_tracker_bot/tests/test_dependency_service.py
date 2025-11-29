"""
Тесты для DependencyService
"""
import pytest
from datetime import datetime
from database import Database
from repositories.board_dependency_repository import BoardDependencyRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from services.dependency_service import DependencyService

@pytest.fixture
def dependency_service(temp_db, sample_user_id):
    """Создать DependencyService для тестов"""
    workspace_repo = WorkspaceRepository(temp_db)
    workspace_id = workspace_repo.create(sample_user_id, "Test Workspace")
    
    board_repo = BoardRepository(temp_db)
    board1_id = board_repo.create(workspace_id, "Board 1")
    board2_id = board_repo.create(workspace_id, "Board 2")
    
    column_repo = ColumnRepository(temp_db)
    col1_id = column_repo.create(board1_id, "Column 1")
    col2_id = column_repo.create(board2_id, "Column 2")
    
    dependency_repo = BoardDependencyRepository(temp_db)
    task_repo = TaskRepository(temp_db)
    project_repo = ProjectRepository(temp_db)
    
    service = DependencyService(
        dependency_repo, task_repo, project_repo, column_repo, board_repo
    )
    
    return service, workspace_id, board1_id, board2_id, col1_id, col2_id

def test_create_dependency(dependency_service):
    """Тест создания зависимости"""
    service, workspace_id, board1_id, board2_id, col1_id, col2_id = dependency_service
    
    success, dep_id, error = service.create_dependency(
        workspace_id=workspace_id,
        name="Test Dependency",
        source_board_id=board1_id,
        source_column_id=col1_id,
        trigger_type='enter',
        target_board_id=board2_id,
        target_column_id=col2_id,
        action_type='create_task',
        task_title_template="{project_id} {project_name} Test"
    )
    
    assert success is True
    assert dep_id is not None
    assert error is None

def test_list_dependencies(dependency_service):
    """Тест получения списка зависимостей"""
    service, workspace_id, board1_id, board2_id, col1_id, col2_id = dependency_service
    
    # Создать зависимость
    service.create_dependency(
        workspace_id=workspace_id,
        name="Test Dependency",
        source_board_id=board1_id,
        source_column_id=col1_id,
        trigger_type='enter',
        target_board_id=board2_id,
        target_column_id=col2_id,
        action_type='create_task'
    )
    
    # Получить список
    dependencies = service.list_dependencies(workspace_id)
    assert len(dependencies) == 1
    assert dependencies[0].name == "Test Dependency"

def test_delete_dependency(dependency_service):
    """Тест удаления зависимости"""
    service, workspace_id, board1_id, board2_id, col1_id, col2_id = dependency_service
    
    # Создать зависимость
    success, dep_id, _ = service.create_dependency(
        workspace_id=workspace_id,
        name="Test Dependency",
        source_board_id=board1_id,
        source_column_id=col1_id,
        trigger_type='enter',
        target_board_id=board2_id,
        target_column_id=col2_id,
        action_type='create_task'
    )
    
    # Удалить
    success, error = service.delete_dependency(dep_id)
    assert success is True
    assert error is None
    
    # Проверить, что удалена
    dependencies = service.list_dependencies(workspace_id)
    assert len(dependencies) == 0


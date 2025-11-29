"""
Unit тесты для TaskClassifier
"""
import pytest
from unittest.mock import Mock, MagicMock
from utils.task_classifier import TaskClassifier
from repositories.project_repository import ProjectRepository

@pytest.fixture
def mock_project_repo():
    """Мок репозитория проектов"""
    repo = Mock(spec=ProjectRepository)
    return repo

@pytest.fixture
def task_classifier(mock_project_repo):
    return TaskClassifier(mock_project_repo)

def test_classify_personal_task(task_classifier, mock_project_repo):
    """Тест классификации личной задачи"""
    mock_project_repo.get_by_id.return_value = None
    
    result = task_classifier.classify_task("Выгул Феры", workspace_id=1)
    
    assert result["type"] == "personal"
    assert result["project_id"] is None
    assert result["title"] == "Выгул Феры"

def test_classify_work_task_with_dash(task_classifier, mock_project_repo):
    """Тест классификации рабочей задачи с форматом '5001 - текст'"""
    from models.project import Project
    mock_project = Mock(spec=Project)
    mock_project.workspace_id = 1
    mock_project_repo.get_by_id.return_value = mock_project
    
    result = task_classifier.classify_task("5001 - Протестировать приложение", workspace_id=1)
    
    assert result["type"] == "work"
    assert result["project_id"] == "5001"
    assert "Протестировать приложение" in result["title"]

def test_classify_work_task_without_dash(task_classifier, mock_project_repo):
    """Тест классификации рабочей задачи с форматом '5001 текст'"""
    from models.project import Project
    mock_project = Mock(spec=Project)
    mock_project.workspace_id = 1
    mock_project_repo.get_by_id.return_value = mock_project
    
    result = task_classifier.classify_task("5001 Протестировать приложение", workspace_id=1)
    
    assert result["type"] == "work"
    assert result["project_id"] == "5001"

def test_classify_task_nonexistent_project(task_classifier, mock_project_repo):
    """Тест классификации задачи с несуществующим проектом"""
    mock_project_repo.get_by_id.return_value = None
    
    result = task_classifier.classify_task("5001 - Задача", workspace_id=1)
    
    # Если проект не найден, задача считается личной
    assert result["type"] == "personal"

def test_classify_task_wrong_workspace(task_classifier, mock_project_repo):
    """Тест классификации задачи с проектом из другого workspace"""
    from models.project import Project
    mock_project = Mock(spec=Project)
    mock_project.workspace_id = 2  # Другой workspace
    mock_project_repo.get_by_id.return_value = mock_project
    
    result = task_classifier.classify_task("5001 - Задача", workspace_id=1)
    
    # Если проект из другого workspace, задача считается личной
    assert result["type"] == "personal"


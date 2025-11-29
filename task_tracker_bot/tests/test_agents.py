"""
Тесты для системы AI-агентов
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.data_manager import DataManagerAgent
from agents.task_manager import TaskManagerAgent
from agents.control_manager import ControlManagerAgent
from agents.analyze_manager import AnalyzeManagerAgent
from agents.orchestrator import OrchestratorAgent
from agents.agent_coordinator import AgentCoordinator
from database import Database


@pytest.fixture
def mock_db():
    """Мок базы данных"""
    db = Mock(spec=Database)
    db.get_connection = Mock()
    return db


@pytest.fixture
def mock_api_key():
    """Мок API ключа"""
    return "test-api-key"


@pytest.fixture
def data_manager(mock_db, mock_api_key):
    """Создание DataManagerAgent с моками"""
    with patch('agents.data_manager.ProjectRepository'), \
         patch('agents.data_manager.TaskRepository'), \
         patch('agents.data_manager.BoardRepository'), \
         patch('agents.data_manager.ColumnRepository'), \
         patch('agents.data_manager.CustomFieldRepository'), \
         patch('agents.data_manager.ProjectService'), \
         patch('agents.data_manager.TaskService'), \
         patch('agents.data_manager.BoardService'), \
         patch('agents.data_manager.StatisticsService'):
        
        adm = DataManagerAgent(api_key=mock_api_key, db=mock_db)
        return adm


class TestDataManagerAgent:
    """Тесты для DataManagerAgent"""
    
    def test_get_next_project_id(self, data_manager):
        """Тест получения следующего ID проекта"""
        # Мокируем project_service
        mock_project = Mock()
        mock_project.id = "5004"
        data_manager.project_service.list_projects = Mock(return_value=[
            Mock(id="5001"), Mock(id="5002"), Mock(id="5003"), Mock(id="5004")
        ])
        
        result = data_manager.get_next_project_id(workspace_id=1)
        
        assert result["status"] == "success"
        assert result["next_project_id"] == "5005"
    
    def test_create_project(self, data_manager):
        """Тест создания проекта"""
        data_manager.project_service.create_project = Mock(return_value=(True, "5005", None))
        data_manager.project_service.get_project = Mock(return_value=Mock(
            id="5005", name="Test Project", workspace_id=1
        ))
        
        result = data_manager.create_project(
            project_id="5005",
            workspace_id=1,
            name="Test Project"
        )
        
        assert result["status"] == "success"
        assert result["data"]["id"] == "5005"
    
    def test_add_project_link(self, data_manager):
        """Тест добавления ссылки к проекту"""
        mock_project = Mock()
        mock_project.workspace_id = 1
        data_manager.project_service.get_project = Mock(return_value=mock_project)
        
        mock_field = Mock()
        mock_field.id = 1
        mock_field.field_type = "url"
        data_manager.field_repo.get_by_name = Mock(return_value=None)
        data_manager.field_repo.create = Mock(return_value=1)
        data_manager.field_repo.get_by_id = Mock(return_value=mock_field)
        
        mock_task = Mock()
        mock_task.id = 1
        data_manager.task_service.list_tasks_by_project = Mock(return_value=[mock_task])
        data_manager.field_repo.set_task_field = Mock(return_value=True)
        
        result = data_manager.add_project_link(
            project_id="5005",
            link_type="ТЗ",
            url="https://example.com"
        )
        
        assert result["status"] == "success"
        assert "ТЗ" in result["message"]


class TestTaskManagerAgent:
    """Тесты для TaskManagerAgent"""
    
    def test_create_project(self, mock_api_key, data_manager):
        """Тест создания проекта через ATM"""
        atm = TaskManagerAgent(api_key=mock_api_key, data_manager=data_manager)
        
        data_manager.create_project = Mock(return_value={
            "status": "success",
            "data": {"id": "5005", "name": "Test", "workspace_id": 1}
        })
        
        result = atm.create_project(
            workspace_id=1,
            project_id="5005",
            name="Test Project"
        )
        
        assert result["status"] == "success"
    
    def test_add_link_to_project(self, mock_api_key, data_manager):
        """Тест добавления ссылки через ATM"""
        atm = TaskManagerAgent(api_key=mock_api_key, data_manager=data_manager)
        
        data_manager.add_project_link = Mock(return_value={
            "status": "success",
            "message": "Ссылка добавлена"
        })
        
        result = atm.add_link_to_project(
            project_id="5005",
            link_type="ТЗ",
            url="https://example.com"
        )
        
        assert result["status"] == "success"


class TestControlManagerAgent:
    """Тесты для ControlManagerAgent"""
    
    def test_validate_project(self, mock_api_key, data_manager):
        """Тест валидации проекта"""
        acm = ControlManagerAgent(api_key=mock_api_key, data_manager=data_manager)
        
        data_manager.get_project = Mock(return_value={
            "id": "5005",
            "name": "Test",
            "workspace_id": 1
        })
        data_manager.get_project_boards = Mock(return_value=[
            {"id": 1, "name": "Backend", "type": "backend"},
            {"id": 2, "name": "Design", "type": "design"}
        ])
        
        result = acm._validate_project("5005", None)
        
        # Проект найден, но не все доски присутствуют
        assert "status" in result


class TestAgentCoordinator:
    """Тесты для AgentCoordinator"""
    
    @patch('agents.agent_coordinator.DataManagerAgent')
    @patch('agents.agent_coordinator.OrchestratorAgent')
    @patch('agents.agent_coordinator.TaskManagerAgent')
    @patch('agents.agent_coordinator.ControlManagerAgent')
    @patch('agents.agent_coordinator.AnalyzeManagerAgent')
    def test_initialization(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест инициализации координатора"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        assert coordinator.adm is not None
        assert coordinator.orchestrator is not None
        assert coordinator.atm is not None
        assert coordinator.acm is not None
        assert coordinator.aam is not None
    
    @patch('agents.agent_coordinator.DataManagerAgent')
    @patch('agents.agent_coordinator.OrchestratorAgent')
    @patch('agents.agent_coordinator.TaskManagerAgent')
    @patch('agents.agent_coordinator.ControlManagerAgent')
    @patch('agents.agent_coordinator.AnalyzeManagerAgent')
    def test_process_user_message(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест обработки сообщения пользователя"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        # Мокируем методы агентов
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "create_project",
            "entities": {"project_id": "id+", "project_name": "Test"},
            "plan": [
                {"agent": "ADM", "action": "get_next_project_id", "params": {"workspace_id": 1}}
            ]
        })
        
        coordinator.adm.get_next_project_id = Mock(return_value={
            "status": "success",
            "next_project_id": "5005"
        })
        
        result = coordinator.process_user_message(
            user_message="Создай проект id+ Test",
            workspace_id=1
        )
        
        assert "status" in result


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.skip(reason="Требует реального API ключа и БД")
    def test_full_flow_create_project(self):
        """Тест полного флоу создания проекта"""
        # Этот тест требует реального API ключа и БД
        # Можно запускать вручную для проверки
        pass


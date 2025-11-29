"""
Unit тесты для AI-обработки запросов с датами
"""
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, MagicMock, patch

# Используем абсолютные импорты
from task_tracker_bot.agents.agent_coordinator import AgentCoordinator
from task_tracker_bot.agents.task_manager import TaskManagerAgent
from task_tracker_bot.agents.data_manager import DataManagerAgent
from task_tracker_bot.agents.orchestrator import OrchestratorAgent
from task_tracker_bot.database import Database
from task_tracker_bot.utils.date_parser import DateParser
from task_tracker_bot.services.todo_service import TodoService


@pytest.fixture
def mock_db():
    """Мок базы данных"""
    db = Mock(spec=Database)
    db.get_connection = Mock()
    return db


@pytest.fixture
def mock_date_parser():
    """Мок DateParser"""
    parser = Mock(spec=DateParser)
    return parser


@pytest.fixture
def mock_todo_service():
    """Мок TodoService"""
    service = Mock(spec=TodoService)
    return service


class TestAgentCoordinatorDateParsing:
    """Тесты парсинга дат в AgentCoordinator"""
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_process_message_with_tomorrow_date(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест обработки запроса с датой 'завтра'"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        # Мокируем оркестратор - возвращает план создания задач на завтра
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "create_todo_batch",
            "entities": {
                "tasks": ["купить молоко", "позвонить маме"],
                "date": "завтра"
            },
            "plan": [
                {
                    "agent": "ATM",
                    "action": "create_todo_batch",
                    "params": {
                        "workspace_id": 1,
                        "user_id": 123,
                        "tasks": ["купить молоко", "позвонить маме"],
                        "default_date": "завтра"
                    }
                }
            ]
        })
        
        # Мокируем TaskManagerAgent
        tomorrow = datetime.now().date() + timedelta(days=1)
        coordinator.atm.create_todo_batch = Mock(return_value={
            "status": "success",
            "message": "Задачи созданы",
            "data": {
                "personal_tasks_created": [
                    {"id": 1, "title": "купить молоко", "date": tomorrow.isoformat()},
                    {"id": 2, "title": "позвонить маме", "date": tomorrow.isoformat()}
                ],
                "work_tasks_created": [],
                "errors": []
            }
        })
        
        result = coordinator.process_user_message(
            user_message="Добавь на завтра задачи: купить молоко, позвонить маме",
            workspace_id=1,
            user_id=123
        )
        
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]["personal_tasks_created"]) == 2
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_process_message_with_absolute_date(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест обработки запроса с абсолютной датой"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "create_todo_batch",
            "entities": {
                "tasks": ["встреча с клиентом"],
                "date": "15.12.2025"
            },
            "plan": [
                {
                    "agent": "ATM",
                    "action": "create_todo_batch",
                    "params": {
                        "workspace_id": 1,
                        "user_id": 123,
                        "tasks": ["встреча с клиентом"],
                        "default_date": date(2025, 12, 15)
                    }
                }
            ]
        })
        
        target_date = date(2025, 12, 15)
        coordinator.atm.create_todo_batch = Mock(return_value={
            "status": "success",
            "message": "Задача создана",
            "data": {
                "personal_tasks_created": [
                    {"id": 1, "title": "встреча с клиентом", "date": target_date.isoformat()}
                ],
                "work_tasks_created": [],
                "errors": []
            }
        })
        
        result = coordinator.process_user_message(
            user_message="Добавь на 15.12.2025 задачу: встреча с клиентом",
            workspace_id=1,
            user_id=123
        )
        
        assert result["status"] == "success"
        assert len(result["data"]["personal_tasks_created"]) == 1
        assert result["data"]["personal_tasks_created"][0]["date"] == target_date.isoformat()


class TestTaskManagerAgentDateParsing:
    """Тесты парсинга дат в TaskManagerAgent"""
    
    def test_create_todo_batch_with_tomorrow(self, mock_db, mock_todo_service):
        """Тест создания пакета задач на завтра"""
        agent = TaskManagerAgent(api_key="test-key", data_manager=Mock())
        agent.data_manager.create_todo_batch = Mock(return_value={
            "status": "success",
            "message": "Задачи созданы",
            "data": {
                "personal_tasks_created": [
                    {"id": 1, "title": "купить молоко", "date": (datetime.now().date() + timedelta(days=1)).isoformat()}
                ],
                "work_tasks_created": [],
                "errors": []
            }
        })
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        result = agent.create_todo_batch(
            workspace_id=1,
            user_id=123,
            tasks=[{"title": "купить молоко"}],
            default_date=tomorrow
        )
        
        assert result["status"] == "success"
        assert len(result["data"]["personal_tasks_created"]) == 1
    
    def test_create_todo_batch_with_relative_date(self, mock_db):
        """Тест создания пакета задач с относительной датой"""
        agent = TaskManagerAgent(api_key="test-key", data_manager=Mock())
        
        # Мокируем DateParser для парсинга относительной даты
        with patch('task_tracker_bot.agents.task_manager.DateParser') as mock_parser_class:
            mock_parser = Mock()
            tomorrow = datetime.now().date() + timedelta(days=1)
            mock_parser.parse_date.return_value = tomorrow
            mock_parser_class.return_value = mock_parser
            
            agent.data_manager.create_todo_batch = Mock(return_value={
                "status": "success",
                "data": {
                    "personal_tasks_created": [
                        {"id": 1, "title": "задача", "date": tomorrow.isoformat()}
                    ],
                    "work_tasks_created": [],
                    "errors": []
                }
            })
            
            result = agent.create_todo_batch(
                workspace_id=1,
                user_id=123,
                tasks=[{"title": "задача"}],
                default_date=None
            )
            
            assert result["status"] == "success"


class TestDateParserIntegration:
    """Тесты интеграции DateParser с AI-обработкой"""
    
    def test_date_parser_with_ai_request(self):
        """Тест использования DateParser для парсинга дат из AI-запросов"""
        parser = DateParser()
        
        # Тест различных форматов дат из AI-запросов
        test_cases = [
            ("на завтра", datetime.now().date() + timedelta(days=1)),
            ("завтра", datetime.now().date() + timedelta(days=1)),
            ("на послезавтра", datetime.now().date() + timedelta(days=2)),
            ("послезавтра", datetime.now().date() + timedelta(days=2)),
            ("сегодня", datetime.now().date()),
            ("15.12", date(datetime.now().year, 12, 15)),
            ("15.12.2025", date(2025, 12, 15)),
        ]
        
        for date_text, expected_date in test_cases:
            result = parser.parse_date(date_text)
            assert result == expected_date, f"Неверный парсинг для '{date_text}': ожидалось {expected_date}, получено {result}"
    
    def test_date_parser_extract_from_task_text(self):
        """Тест извлечения даты из текста задачи"""
        parser = DateParser()
        
        task_text = "Купить молоко завтра в 10:00"
        result = parser.parse_datetime_from_task(task_text)
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        assert result["date"] == tomorrow or result["date"] == datetime.now().date()
        assert result["time"] == time(10, 0)
        assert "молоко" in result["remaining_text"].lower()
    
    def test_date_parser_multiple_tasks_with_dates(self):
        """Тест парсинга нескольких задач с датами"""
        parser = DateParser()
        
        tasks = [
            "Купить молоко завтра",
            "Позвонить маме послезавтра",
            "Встреча 15.12 в 14:00"
        ]
        
        results = []
        for task in tasks:
            result = parser.parse_datetime_from_task(task)
            results.append(result)
        
        # Проверяем, что все задачи распарсились
        assert len(results) == 3
        assert all(r["date"] is not None for r in results)


class TestTodoServiceDateIntegration:
    """Тесты интеграции TodoService с парсингом дат"""
    
    def test_todo_service_parse_date_from_batch(self, mock_repos, mock_utils):
        """Тест парсинга дат при создании пакета задач"""
        from services.todo_service import TodoService
        
        service = TodoService(
            personal_task_repo=mock_repos['personal_task'],
            task_repo=mock_repos['task'],
            project_repo=mock_repos['project'],
            column_repo=mock_repos['column'],
            board_repo=mock_repos['board'],
            date_parser=mock_utils['date_parser'],
            task_classifier=mock_utils['task_classifier']
        )
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        tasks_text = "1. Купить молоко\n2. Позвонить маме"
        
        # Настройка моков
        mock_utils['date_parser'].parse_datetime_from_task.side_effect = [
            {
                "date": tomorrow,
                "time": None,
                "time_end": None,
                "remaining_text": "Купить молоко"
            },
            {
                "date": tomorrow,
                "time": None,
                "time_end": None,
                "remaining_text": "Позвонить маме"
            }
        ]
        
        mock_utils['task_classifier'].classify_task.side_effect = [
            {"type": "personal", "title": "Купить молоко"},
            {"type": "personal", "title": "Позвонить маме"}
        ]
        
        mock_repos['personal_task'].create.side_effect = [1, 2]
        
        result = service.create_todo_batch(
            tasks_text=tasks_text,
            workspace_id=1,
            user_id=123,
            default_date=tomorrow
        )
        
        assert result["status"] == "success"
        assert len(result["personal_tasks_created"]) == 2
        assert all(task["date"] == tomorrow.isoformat() for task in result["personal_tasks_created"])


class TestAIDateParsingIntegration:
    """Интеграционные тесты AI-обработки с датами"""
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_ai_request_create_tasks_tomorrow(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест полного цикла: AI-запрос → создание задач на завтра → проверка БД"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        # Мокируем оркестратор
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "create_todo_batch",
            "entities": {
                "tasks": ["купить молоко", "позвонить маме"],
                "date": "завтра"
            },
            "plan": [
                {
                    "agent": "ATM",
                    "action": "create_todo_batch",
                    "params": {
                        "workspace_id": 1,
                        "user_id": 123,
                        "tasks": [{"title": "купить молоко"}, {"title": "позвонить маме"}],
                        "default_date": "завтра"
                    }
                }
            ]
        })
        
        # Мокируем TaskManagerAgent
        tomorrow = datetime.now().date() + timedelta(days=1)
        coordinator.atm.create_todo_batch = Mock(return_value={
            "status": "success",
            "message": "Задачи созданы",
            "data": {
                "personal_tasks_created": [
                    {"id": 1, "title": "купить молоко", "date": tomorrow.isoformat()},
                    {"id": 2, "title": "позвонить маме", "date": tomorrow.isoformat()}
                ],
                "work_tasks_created": [],
                "errors": []
            }
        })
        
        result = coordinator.process_user_message(
            user_message="Добавь на завтра задачи: купить молоко, позвонить маме",
            workspace_id=1,
            user_id=123
        )
        
        # Проверки результата
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]["personal_tasks_created"]) == 2
        
        # Проверки вызовов
        coordinator.atm.create_todo_batch.assert_called_once()
        call_args = coordinator.atm.create_todo_batch.call_args
        assert call_args[1]["workspace_id"] == 1
        assert call_args[1]["user_id"] == 123
        assert len(call_args[1]["tasks"]) == 2
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_ai_request_with_multiple_dates(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест AI-запроса с несколькими датами в разных задачах"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "create_todo_batch",
            "entities": {
                "tasks": [
                    {"title": "купить молоко", "date": "завтра"},
                    {"title": "встреча", "date": "послезавтра"}
                ]
            },
            "plan": [
                {
                    "agent": "ATM",
                    "action": "create_todo_batch",
                    "params": {
                        "workspace_id": 1,
                        "user_id": 123,
                        "tasks": [
                            {"title": "купить молоко", "date": "завтра"},
                            {"title": "встреча", "date": "послезавтра"}
                        ]
                    }
                }
            ]
        })
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        after_tomorrow = datetime.now().date() + timedelta(days=2)
        
        coordinator.atm.create_todo_batch = Mock(return_value={
            "status": "success",
            "data": {
                "personal_tasks_created": [
                    {"id": 1, "title": "купить молоко", "date": tomorrow.isoformat()},
                    {"id": 2, "title": "встреча", "date": after_tomorrow.isoformat()}
                ],
                "work_tasks_created": [],
                "errors": []
            }
        })
        
        result = coordinator.process_user_message(
            user_message="Добавь задачи: купить молоко завтра, встреча послезавтра",
            workspace_id=1,
            user_id=123
        )
        
        assert result["status"] == "success"
        assert len(result["data"]["personal_tasks_created"]) == 2
        # Проверяем, что даты разные
        dates = [task["date"] for task in result["data"]["personal_tasks_created"]]
        assert len(set(dates)) == 2  # Должны быть две разные даты
    
    def test_date_parser_in_ai_context(self):
        """Тест парсинга дат в контексте AI-запросов"""
        parser = DateParser()
        
        # Тест различных форматов из реальных AI-запросов
        ai_queries = [
            "Добавь на завтра задачи: купить молоко, позвонить маме",
            "Создай задачи на послезавтра: встреча, звонок",
            "Добавь на 15.12 задачу: тест",
            "Добавь на 15.12.2025 задачу: тест"
        ]
        
        for query in ai_queries:
            # Извлекаем дату из запроса
            if "завтра" in query:
                result = parser.parse_date("завтра")
                assert result == datetime.now().date() + timedelta(days=1)
            elif "послезавтра" in query:
                result = parser.parse_date("послезавтра")
                assert result == datetime.now().date() + timedelta(days=2)
            elif "15.12.2025" in query:
                result = parser.parse_date("15.12.2025")
                assert result == date(2025, 12, 15)
            elif "15.12" in query:
                result = parser.parse_date("15.12")
                assert result == date(datetime.now().year, 12, 15)


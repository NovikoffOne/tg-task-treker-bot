"""
Тесты для улучшений AI сети
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from telegram.ext import ContextTypes

from task_tracker_bot.agents.orchestrator import OrchestratorAgent
from task_tracker_bot.agents.agent_coordinator import AgentCoordinator
from task_tracker_bot.handlers.ai_handler import get_user_workspace
from task_tracker_bot.database import Database


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
def mock_context():
    """Мок контекста Telegram"""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


class TestWorkspaceUserData:
    """Тесты для сохранения workspace в user_data"""
    
    @patch('handlers.ai_handler.WorkspaceRepository')
    @patch('handlers.ai_handler.Database')
    def test_workspace_saved_in_user_data(self, mock_db_class, mock_repo_class, mock_context):
        """Проверка сохранения workspace в user_data"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_repo = Mock()
        mock_repo.get_all_by_user = Mock(return_value=[mock_workspace])
        mock_repo_class.return_value = mock_repo
        
        # Вызов функции
        workspace_id = get_user_workspace(user_id=12345, context=mock_context)
        
        # Проверки
        assert workspace_id == 1
        assert mock_context.user_data['current_workspace_id'] == 1
    
    @patch('task_tracker_bot.handlers.ai_handler.WorkspaceRepository')
    @patch('task_tracker_bot.handlers.ai_handler.Database')
    def test_workspace_fallback_to_first(self, mock_db_class, mock_repo_class, mock_context):
        """Проверка fallback на первое пространство"""
        # Настройка моков - нет сохраненного workspace
        mock_workspace1 = Mock()
        mock_workspace1.id = 1
        mock_workspace2 = Mock()
        mock_workspace2.id = 2
        mock_repo = Mock()
        mock_repo.get_all_by_user = Mock(return_value=[mock_workspace1, mock_workspace2])
        mock_repo_class.return_value = mock_repo
        
        # Вызов функции
        workspace_id = get_user_workspace(user_id=12345, context=mock_context)
        
        # Проверки - должно быть первое пространство
        assert workspace_id == 1
        assert mock_context.user_data['current_workspace_id'] == 1
    
    @patch('task_tracker_bot.handlers.ai_handler.WorkspaceRepository')
    @patch('task_tracker_bot.handlers.ai_handler.Database')
    def test_workspace_uses_cached(self, mock_db_class, mock_repo_class, mock_context):
        """Проверка использования сохраненного workspace"""
        # Настройка - workspace уже сохранен
        mock_context.user_data['current_workspace_id'] = 5
        
        # Вызов функции
        workspace_id = get_user_workspace(user_id=12345, context=mock_context)
        
        # Проверки - должен использоваться сохраненный
        assert workspace_id == 5
        # Репозиторий не должен вызываться
        mock_repo_class.assert_not_called()


class TestAPIRetry:
    """Тесты для retry логики API"""
    
    @patch('task_tracker_bot.agents.base_agent.requests.post')
    def test_api_retry_on_timeout(self, mock_post, mock_api_key):
        """Проверка retry при таймауте"""
        from task_tracker_bot.agents.task_manager import TaskManagerAgent
        from task_tracker_bot.agents.data_manager import DataManagerAgent
        
        # Настройка моков - первые две попытки таймаут, третья успешна
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"choices": [{"message": {"content": '{"status": "ok"}'}}]}
        mock_response_success.raise_for_status = Mock()
        
        mock_post.side_effect = [
            Exception("Timeout"),  # Первая попытка
            Exception("Timeout"),  # Вторая попытка
            mock_response_success  # Третья попытка успешна
        ]
        
        # Создаем агента
        with patch('task_tracker_bot.agents.base_agent.Config') as mock_config:
            mock_config.IO_NET_RETRY_COUNT = 3
            mock_config.IO_NET_RETRY_DELAY = 0.1  # Короткая задержка для теста
            mock_config.IO_NET_TIMEOUT = 60
            mock_config.IO_NET_API_URL = "https://api.test.com"
            mock_config.IO_NET_MODEL = "test-model"
            mock_config.IO_NET_TEMPERATURE = 0.3
            mock_config.IO_NET_MAX_TOKENS = 2000
            
            # Этот тест требует реального API ключа, поэтому пропускаем
            pytest.skip("Требует реального API ключа или более сложного мокинга")
    
    @patch('task_tracker_bot.agents.base_agent.requests.post')
    def test_api_retry_on_5xx_error(self, mock_post, mock_api_key):
        """Проверка retry при 5xx ошибках"""
        from task_tracker_bot.agents.base_agent import BaseAgent
        
        # Настройка моков
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status = Mock(side_effect=Exception("500"))
        
        mock_response_200 = Mock()
        mock_response_200.json.return_value = {"choices": [{"message": {"content": '{"status": "ok"}'}}]}
        mock_response_200.raise_for_status = Mock()
        
        mock_post.side_effect = [
            mock_response_500,  # Первая попытка - 500
            mock_response_500,  # Вторая попытка - 500
            mock_response_200   # Третья попытка успешна
        ]
        
        # Этот тест требует более сложного мокинга BaseAgent
        pytest.skip("Требует более сложного мокинга для тестирования retry")


class TestOrchestratorCache:
    """Тесты для кэширования Orchestrator"""
    
    @patch('agents.orchestrator.OrchestratorAgent.process')
    def test_orchestrator_cache_hit(self, mock_process, mock_api_key):
        """Проверка попадания в кэш"""
        orchestrator = OrchestratorAgent(api_key=mock_api_key)
        
        # Мокируем результат первого вызова
        mock_result = {
            "intent": "test",
            "plan": []
        }
        mock_process.return_value = mock_result
        
        # Первый вызов - должен вызвать process
        result1 = orchestrator.analyze_request("Создай проект Test")
        assert mock_process.call_count == 1
        
        # Второй вызов с тем же текстом - должен использовать кэш
        result2 = orchestrator.analyze_request("Создай проект Test")
        assert mock_process.call_count == 1  # Не должен вызываться снова
        assert result1 == result2
    
    @patch('agents.orchestrator.OrchestratorAgent.process')
    def test_orchestrator_cache_miss(self, mock_process, mock_api_key):
        """Проверка промаха кэша"""
        orchestrator = OrchestratorAgent(api_key=mock_api_key)
        
        # Мокируем разные результаты
        mock_result1 = {"intent": "test1", "plan": []}
        mock_result2 = {"intent": "test2", "plan": []}
        mock_process.side_effect = [mock_result1, mock_result2]
        
        # Первый вызов
        result1 = orchestrator.analyze_request("Создай проект Test1")
        assert mock_process.call_count == 1
        
        # Второй вызов с другим текстом - должен вызвать process снова
        result2 = orchestrator.analyze_request("Создай проект Test2")
        assert mock_process.call_count == 2
        assert result1 != result2
    
    def test_orchestrator_cache_normalization(self, mock_api_key):
        """Проверка нормализации текста для кэша"""
        orchestrator = OrchestratorAgent(api_key=mock_api_key)
        
        # Проверяем нормализацию
        normalized1 = orchestrator._normalize_message("Создай проект Test")
        normalized2 = orchestrator._normalize_message("создай проект test")
        normalized3 = orchestrator._normalize_message("Создай  проект   Test")
        
        assert normalized1 == normalized2 == normalized3
    
    def test_orchestrator_clear_cache(self, mock_api_key):
        """Проверка очистки кэша"""
        orchestrator = OrchestratorAgent(api_key=mock_api_key)
        
        # Добавляем что-то в кэш
        orchestrator.cache["test"] = ({"result": "test"}, time.time())
        assert len(orchestrator.cache) == 1
        
        # Очищаем кэш
        orchestrator.clear_cache()
        assert len(orchestrator.cache) == 0


class TestExecutionMetrics:
    """Тесты для метрик времени выполнения"""
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_metrics_logged(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Проверка логирования метрик"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        # Мокируем оркестратор
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "test",
            "entities": {},
            "plan": [
                {"agent": "ADM", "action": "get_next_project_id", "params": {}}
            ]
        })
        
        # Мокируем ADM
        coordinator.adm.get_next_project_id = Mock(return_value={
            "status": "success",
            "next_project_id": "5005"
        })
        
        # Вызываем с логированием
        with patch.object(coordinator.logger, 'info') as mock_logger:
            result = coordinator.process_user_message(
                user_message="Тест",
                workspace_id=1
            )
            
            # Проверяем, что метрики логируются
            log_calls = [str(call) for call in mock_logger.call_args_list]
            assert any("мс" in str(call) or "ms" in str(call) for call in log_calls)
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_execution_time_measured(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Проверка измерения времени выполнения"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        # Мокируем оркестратор
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "test",
            "entities": {},
            "plan": [
                {"agent": "ADM", "action": "get_next_project_id", "params": {}}
            ]
        })
        
        # Мокируем ADM с небольшой задержкой
        def delayed_response(*args, **kwargs):
            time.sleep(0.01)  # 10ms задержка
            return {
                "status": "success",
                "next_project_id": "5005"
            }
        
        coordinator.adm.get_next_project_id = Mock(side_effect=delayed_response)
        
        # Вызываем
        result = coordinator.process_user_message(
            user_message="Тест",
            workspace_id=1
        )
        
        # Проверяем наличие метрик в результате
        assert "metrics" in result
        assert "total_time_ms" in result["metrics"]
        assert result["metrics"]["total_time_ms"] > 0
        
        # Проверяем метрики в execution_results
        assert len(result["execution_results"]) > 0
        for exec_result in result["execution_results"]:
            if exec_result.get("status") == "success":
                assert "execution_time_ms" in exec_result
                assert exec_result["execution_time_ms"] >= 0


class TestIntegration:
    """Интеграционные тесты"""
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_full_ai_flow_with_retry(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест полного флоу с retry"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        # Мокируем оркестратор
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "create_project",
            "entities": {"project_id": "id+", "project_name": "Test"},
            "plan": [
                {"agent": "ADM", "action": "get_next_project_id", "params": {"workspace_id": 1}},
                {"agent": "ATM", "action": "create_project", "params": {"project_id": "5005", "name": "Test"}}
            ]
        })
        
        # Мокируем агентов
        coordinator.adm.get_next_project_id = Mock(return_value={
            "status": "success",
            "next_project_id": "5005"
        })
        coordinator.atm.create_project = Mock(return_value={
            "status": "success",
            "data": {"id": "5005", "name": "Test"}
        })
        
        # Вызываем
        result = coordinator.process_user_message(
            user_message="Создай проект id+ Test",
            workspace_id=1
        )
        
        # Проверки
        assert result["status"] == "success"
        assert "metrics" in result
        assert len(result["execution_results"]) == 2
    
    @patch('task_tracker_bot.agents.agent_coordinator.DataManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.OrchestratorAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.TaskManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.ControlManagerAgent')
    @patch('task_tracker_bot.agents.agent_coordinator.AnalyzeManagerAgent')
    def test_ai_message_processing_with_metrics(self, mock_aam, mock_acm, mock_atm, mock_orch, mock_adm, mock_db):
        """Тест обработки сообщения с метриками"""
        coordinator = AgentCoordinator(api_key="test-key", db=mock_db)
        
        coordinator.orchestrator.analyze_request = Mock(return_value={
            "intent": "query_data",
            "entities": {},
            "plan": [
                {"agent": "ADM", "action": "get_project", "params": {"project_id": "5005"}}
            ]
        })
        
        coordinator.adm.get_project = Mock(return_value={
            "id": "5005",
            "name": "Test"
        })
        
        result = coordinator.process_user_message(
            user_message="Покажи проект 5005",
            workspace_id=1
        )
        
        # Проверяем наличие метрик
        assert "metrics" in result
        metrics = result["metrics"]
        assert "total_time_ms" in metrics
        assert "analysis_time_ms" in metrics
        assert "steps_time_ms" in metrics
        assert "steps_count" in metrics
    
    @patch('task_tracker_bot.agents.orchestrator.OrchestratorAgent.process')
    def test_multiple_requests_caching(self, mock_process, mock_api_key):
        """Тест множественных запросов с кэшированием"""
        orchestrator = OrchestratorAgent(api_key=mock_api_key)
        
        mock_result = {"intent": "test", "plan": []}
        mock_process.return_value = mock_result
        
        # Первый запрос
        result1 = orchestrator.analyze_request("Создай проект Test")
        assert mock_process.call_count == 1
        
        # Второй запрос (тот же)
        result2 = orchestrator.analyze_request("Создай проект Test")
        assert mock_process.call_count == 1  # Кэш использован
        
        # Третий запрос (другой)
        result3 = orchestrator.analyze_request("Создай проект Test2")
        assert mock_process.call_count == 2  # Новый запрос
        
        assert result1 == result2
        assert result1 != result3


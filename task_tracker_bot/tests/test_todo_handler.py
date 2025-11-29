"""
Unit тесты для обработчиков команды /todo
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from telegram import Update, Message, User, CallbackQuery
from telegram.ext import ContextTypes

from handlers.todo_handler import (
    todo_command,
    handle_todo_date_callback,
    handle_todo_navigation,
    handle_mark_todo_completed
)


@pytest.fixture
def mock_update():
    """Мок Update для тестов"""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=User)
    update.effective_user.id = 12345
    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Мок Context для тестов"""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


@pytest.fixture
def mock_callback_query():
    """Мок CallbackQuery для тестов"""
    query = Mock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.from_user = Mock(spec=User)
    query.from_user.id = 12345
    query.data = "todo_nav_prev_2025-11-29"
    return query


@pytest.fixture
def mock_update_with_callback(mock_callback_query):
    """Мок Update с CallbackQuery"""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=User)
    update.effective_user.id = 12345
    update.callback_query = mock_callback_query
    return update


class TestTodoCommand:
    """Тесты для команды /todo"""
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    @patch('handlers.todo_handler.date_parser')
    async def test_todo_command_default_date(self, mock_date_parser, mock_todo_service, mock_workspace_repo, mock_update, mock_context):
        """Тест команды /todo без аргументов (используется сегодня)"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        today = datetime.now().date()
        mock_todo_list = {
            "date": today.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await todo_command(mock_update, mock_context)
        
        # Проверки
        mock_todo_service.get_todo_list.assert_called_once_with(
            user_id=12345,
            target_date=today,
            include_work_tasks=True
        )
        mock_update.message.reply_text.assert_called_once()
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    @patch('handlers.todo_handler.date_parser')
    async def test_todo_command_with_date_arg(self, mock_date_parser, mock_todo_service, mock_workspace_repo, mock_update, mock_context):
        """Тест команды /todo с аргументом даты"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        mock_context.args = ["завтра"]
        mock_date_parser.parse_date.return_value = tomorrow
        
        mock_todo_list = {
            "date": tomorrow.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await todo_command(mock_update, mock_context)
        
        # Проверки
        mock_date_parser.parse_date.assert_called_once_with("завтра")
        mock_todo_service.get_todo_list.assert_called_once_with(
            user_id=12345,
            target_date=tomorrow,
            include_work_tasks=True
        )
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    @patch('handlers.todo_handler.date_parser')
    async def test_todo_command_invalid_date(self, mock_date_parser, mock_todo_service, mock_workspace_repo, mock_update, mock_context):
        """Тест команды /todo с невалидной датой"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        mock_context.args = ["невалидная дата"]
        mock_date_parser.parse_date.return_value = None
        
        today = datetime.now().date()
        mock_todo_list = {
            "date": today.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await todo_command(mock_update, mock_context)
        
        # Проверки - должно быть сообщение об ошибке и использование сегодняшней даты
        assert mock_update.message.reply_text.call_count >= 1
        # Последний вызов должен быть с туду-листом
        last_call = mock_update.message.reply_text.call_args_list[-1]
        assert "туду" in str(last_call).lower() or "задач" in str(last_call).lower()
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    async def test_todo_command_no_workspace(self, mock_workspace_repo, mock_update, mock_context):
        """Тест команды /todo без workspace"""
        # Настройка моков - нет workspace
        mock_workspace_repo.return_value.get_all_by_user.return_value = []
        
        await todo_command(mock_update, mock_context)
        
        # Проверки - должно быть сообщение об ошибке
        mock_update.message.reply_text.assert_called_once()
        call_args = str(mock_update.message.reply_text.call_args)
        assert "пространств" in call_args.lower() or "workspace" in call_args.lower()


class TestTodoNavigation:
    """Тесты для навигации по датам"""
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    async def test_todo_navigation_prev(self, mock_todo_service, mock_workspace_repo, mock_update_with_callback, mock_context):
        """Тест навигации на предыдущий день"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        yesterday = datetime.now().date() - timedelta(days=1)
        mock_update_with_callback.callback_query.data = f"todo_nav_prev_{yesterday.isoformat()}"
        
        mock_todo_list = {
            "date": yesterday.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await handle_todo_navigation(mock_update_with_callback, mock_context)
        
        # Проверки
        mock_todo_service.get_todo_list.assert_called_once_with(
            user_id=12345,
            target_date=yesterday,
            include_work_tasks=True
        )
        mock_update_with_callback.callback_query.edit_message_text.assert_called_once()
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    async def test_todo_navigation_next(self, mock_todo_service, mock_workspace_repo, mock_update_with_callback, mock_context):
        """Тест навигации на следующий день"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        mock_update_with_callback.callback_query.data = f"todo_nav_next_{tomorrow.isoformat()}"
        
        mock_todo_list = {
            "date": tomorrow.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await handle_todo_navigation(mock_update_with_callback, mock_context)
        
        # Проверки
        mock_todo_service.get_todo_list.assert_called_once_with(
            user_id=12345,
            target_date=tomorrow,
            include_work_tasks=True
        )
        mock_update_with_callback.callback_query.edit_message_text.assert_called_once()
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    async def test_todo_navigation_today(self, mock_todo_service, mock_workspace_repo, mock_update_with_callback, mock_context):
        """Тест навигации на сегодня"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        today = datetime.now().date()
        mock_update_with_callback.callback_query.data = f"todo_nav_today_{today.isoformat()}"
        
        mock_todo_list = {
            "date": today.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await handle_todo_navigation(mock_update_with_callback, mock_context)
        
        # Проверки
        mock_todo_service.get_todo_list.assert_called_once_with(
            user_id=12345,
            target_date=today,
            include_work_tasks=True
        )


class TestTodoDateCallback:
    """Тесты для выбора даты через callback"""
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    async def test_todo_date_callback(self, mock_todo_service, mock_workspace_repo, mock_update_with_callback, mock_context):
        """Тест выбора конкретной даты через callback"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        target_date = date(2025, 12, 15)
        mock_update_with_callback.callback_query.data = f"todo_date_{target_date.isoformat()}"
        
        mock_todo_list = {
            "date": target_date.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await handle_todo_date_callback(mock_update_with_callback, mock_context)
        
        # Проверки
        mock_todo_service.get_todo_list.assert_called_once_with(
            user_id=12345,
            target_date=target_date,
            include_work_tasks=True
        )
        mock_update_with_callback.callback_query.edit_message_text.assert_called_once()
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    async def test_todo_date_callback_invalid_date(self, mock_todo_service, mock_workspace_repo, mock_update_with_callback, mock_context):
        """Тест выбора невалидной даты через callback"""
        # Настройка моков
        mock_update_with_callback.callback_query.data = "todo_date_invalid"
        
        await handle_todo_date_callback(mock_update_with_callback, mock_context)
        
        # Проверки - должно быть сообщение об ошибке
        mock_update_with_callback.callback_query.edit_message_text.assert_called_once()
        call_args = str(mock_update_with_callback.callback_query.edit_message_text.call_args)
        assert "некоррект" in call_args.lower() or "ошибк" in call_args.lower()


class TestMarkTodoCompleted:
    """Тесты для отметки задач как выполненных"""
    
    @patch('repositories.workspace_repository.WorkspaceRepository')
    @patch('handlers.todo_handler.todo_service')
    async def test_mark_todo_completed_success(self, mock_todo_service, mock_workspace_repo, mock_update_with_callback, mock_context):
        """Тест успешной отметки задачи как выполненной"""
        # Настройка моков
        mock_workspace = Mock()
        mock_workspace.id = 1
        mock_workspace_repo.return_value.get_all_by_user.return_value = [mock_workspace]
        
        task_id = 123
        mock_update_with_callback.callback_query.data = f"todo_complete_{task_id}"
        mock_todo_service.mark_personal_task_completed.return_value = (True, None)
        
        today = datetime.now().date()
        mock_todo_list = {
            "date": today.strftime("%d.%m.%Y"),
            "personal_tasks": [],
            "work_tasks": [],
            "grouped_by_time": {}
        }
        mock_todo_service.get_todo_list.return_value = mock_todo_list
        
        await handle_mark_todo_completed(mock_update_with_callback, mock_context)
        
        # Проверки
        mock_todo_service.mark_personal_task_completed.assert_called_once_with(task_id, 12345)
        mock_update_with_callback.callback_query.answer.assert_called_once()
        mock_update_with_callback.callback_query.edit_message_text.assert_called_once()
    
    @patch('handlers.todo_handler.todo_service')
    async def test_mark_todo_completed_failure(self, mock_todo_service, mock_update_with_callback, mock_context):
        """Тест неудачной отметки задачи как выполненной"""
        # Настройка моков
        task_id = 123
        mock_update_with_callback.callback_query.data = f"todo_complete_{task_id}"
        mock_todo_service.mark_personal_task_completed.return_value = (False, "Задача не найдена")
        
        await handle_mark_todo_completed(mock_update_with_callback, mock_context)
        
        # Проверки
        mock_todo_service.mark_personal_task_completed.assert_called_once_with(task_id, 12345)
        mock_update_with_callback.callback_query.answer.assert_called_once()
        # Не должно быть edit_message_text при ошибке
        mock_update_with_callback.callback_query.edit_message_text.assert_not_called()
    
    async def test_mark_todo_completed_invalid_callback(self, mock_update_with_callback, mock_context):
        """Тест обработки невалидного callback"""
        # Настройка моков
        mock_update_with_callback.callback_query.data = "invalid_callback"
        
        await handle_mark_todo_completed(mock_update_with_callback, mock_context)
        
        # Проверки - должно быть сообщение об ошибке
        mock_update_with_callback.callback_query.edit_message_text.assert_called_once()
        call_args = str(mock_update_with_callback.callback_query.edit_message_text.call_args)
        assert "некоррект" in call_args.lower()


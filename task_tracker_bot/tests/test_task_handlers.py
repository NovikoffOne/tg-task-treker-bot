"""
Тесты для handlers задач (tasks)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User

from handlers.task import (
    task_command,
    movetask_command,
    priority_command,
    deltask_command,
    mytasks_command,
    today_command,
    deadline_command
)


@pytest.fixture
def mock_update():
    """Создать мок Update"""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Создать мок Context"""
    context = MagicMock()
    context.user_data = {}
    context.args = []
    return context


@pytest.mark.asyncio
async def test_task_command_success(mock_update, mock_context):
    """Тест команды /task - успешный просмотр"""
    from models.task import Task
    
    mock_context.args = ["123"]
    task = Task(id=123, column_id=1, title="Test Task")
    
    with patch('handlers.task.task_repo') as mock_repo:
        mock_repo.get_by_id.return_value = task
        
        await task_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_task_command_not_found(mock_update, mock_context):
    """Тест команды /task - задача не найдена"""
    mock_context.args = ["999"]
    
    with patch('handlers.task.task_repo') as mock_repo:
        mock_repo.get_by_id.return_value = None
        
        await task_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert 'не найдена' in call_args.args[0].lower()


@pytest.mark.asyncio
async def test_movetask_command_success(mock_update, mock_context):
    """Тест команды /movetask - успешное перемещение"""
    from models.task import Task
    from models.column import Column
    
    mock_context.args = ["123", "В работе"]
    task = Task(id=123, column_id=1, title="Test Task")
    column = Column(id=2, board_id=1, name="В работе")
    
    with patch('handlers.task.task_repo') as mock_task_repo, \
         patch('handlers.task.column_repo') as mock_column_repo, \
         patch('handlers.task.task_service') as mock_task_service:
        mock_task_repo.get_by_id.return_value = task
        mock_column_repo.get_by_name.return_value = column
        mock_task_service.move_task.return_value = (True, None)
        
        await movetask_command(mock_update, mock_context)
        
        mock_task_service.move_task.assert_called_once()
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_priority_command_success(mock_update, mock_context):
    """Тест команды /priority - успешная установка приоритета"""
    from models.task import Task
    
    mock_context.args = ["123", "2"]
    task = Task(id=123, column_id=1, title="Test Task")
    
    with patch('handlers.task.task_repo') as mock_repo, \
         patch('handlers.task.task_service') as mock_service:
        mock_repo.get_by_id.return_value = task
        mock_service.set_priority.return_value = (True, None)
        
        await priority_command(mock_update, mock_context)
        
        mock_service.set_priority.assert_called_once_with(123, 2)
        mock_update.message.reply_text.assert_called()


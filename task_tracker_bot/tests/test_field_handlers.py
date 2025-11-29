"""
Тесты для handlers полей (fields)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User

from handlers.field import (
    newfield_command,
    addfield_command
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
async def test_newfield_command_success(mock_update, mock_context):
    """Тест команды /newfield - успешное создание"""
    from models.workspace import Workspace
    from datetime import datetime
    
    mock_context.args = ["Figma", "url"]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.field.workspace_repo') as mock_workspace_repo, \
         patch('handlers.field.field_repo') as mock_field_repo:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_field_repo.create.return_value = 1
        
        await newfield_command(mock_update, mock_context)
        
        mock_field_repo.create.assert_called_once_with(1, "Figma", "url")
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_newfield_command_invalid_type(mock_update, mock_context):
    """Тест команды /newfield - неверный тип поля"""
    mock_context.args = ["Figma", "invalid"]
    
    await newfield_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called()
    call_args = mock_update.message.reply_text.call_args
    assert 'некорректный тип' in call_args.args[0].lower()


@pytest.mark.asyncio
async def test_addfield_command_success(mock_update, mock_context):
    """Тест команды /addfield - успешное добавление"""
    from models.task import Task
    from models.workspace import Workspace
    from models.custom_field import CustomField
    from datetime import datetime
    
    mock_context.args = ["123", "Figma", "https://figma.com/file/123"]
    task = Task(id=123, column_id=1, title="Test Task", project_id=None, created_at=datetime.now(), updated_at=datetime.now())
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    field = CustomField(id=1, workspace_id=1, name="Figma", field_type="url", created_at=datetime.now())
    
    with patch('handlers.field.task_repo') as mock_task_repo, \
         patch('handlers.field.column_repo') as mock_column_repo, \
         patch('handlers.field.board_repo') as mock_board_repo, \
         patch('handlers.field.workspace_repo') as mock_workspace_repo, \
         patch('handlers.field.field_repo') as mock_field_repo, \
         patch('handlers.field.sync_service') as mock_sync_service:
        mock_task_repo.get_by_id.return_value = task
        mock_column_repo.get_by_id.return_value = MagicMock(board_id=1)
        mock_board_repo.get_by_id.return_value = MagicMock(workspace_id=1)
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_field_repo.get_by_name.return_value = field
        mock_sync_service.sync_field_to_project.return_value = (True, None)
        
        await addfield_command(mock_update, mock_context)
        
        mock_sync_service.sync_field_to_project.assert_called_once()
        mock_update.message.reply_text.assert_called()


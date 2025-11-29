"""
Тесты для handlers пространств (workspaces)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

from handlers.workspace import (
    workspaces_command,
    newworkspace_command,
    process_workspace_name,
    delworkspace_command,
    renameworkspace_command
)


@pytest.fixture
def mock_update():
    """Создать мок Update"""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test"
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = None
    return update


@pytest.fixture
def mock_context(temp_db):
    """Создать мок Context"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.args = []
    return context


@pytest.mark.asyncio
async def test_workspaces_command_empty(temp_db, mock_update, mock_context):
    """Тест команды /workspaces когда нет пространств"""
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.list_workspaces.return_value = []
        
        await workspaces_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert 'HTML' in call_args.kwargs.get('parse_mode', '')


@pytest.mark.asyncio
async def test_workspaces_command_with_workspaces(temp_db, mock_update, mock_context):
    """Тест команды /workspaces когда есть пространства"""
    from models.workspace import Workspace
    from datetime import datetime
    
    workspace1 = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    workspace2 = Workspace(id=2, user_id=12345, name="Дом", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.list_workspaces.return_value = [workspace1, workspace2]
        
        await workspaces_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert 'Работа' in call_args.args[0] or 'Дом' in call_args.args[0]


@pytest.mark.asyncio
async def test_newworkspace_command_with_args(temp_db, mock_update, mock_context):
    """Тест команды /newworkspace с аргументами"""
    mock_context.args = ["Тестовое", "пространство"]
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.create_workspace.return_value = (True, 1, None)
        
        result = await newworkspace_command(mock_update, mock_context)
        
        from telegram.ext import ConversationHandler
        assert result == ConversationHandler.END
        mock_service.create_workspace.assert_called_once_with(12345, "Тестовое пространство")
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_newworkspace_command_interactive(temp_db, mock_update, mock_context):
    """Тест команды /newworkspace в интерактивном режиме"""
    mock_context.args = []
    
    result = await newworkspace_command(mock_update, mock_context)
    
    assert result == 1  # WAITING_WORKSPACE_NAME
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_process_workspace_name_success(temp_db, mock_update, mock_context):
    """Тест обработки названия пространства - успешное создание"""
    mock_update.message.text = "Тестовое пространство"
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.create_workspace.return_value = (True, 1, None)
        mock_service.list_workspaces.return_value = []
        
        result = await process_workspace_name(mock_update, mock_context)
        
        from telegram.ext import ConversationHandler
        assert result == ConversationHandler.END
        mock_service.create_workspace.assert_called_once_with(12345, "Тестовое пространство")
        assert 'waiting_workspace_name' not in mock_context.user_data


@pytest.mark.asyncio
async def test_process_workspace_name_error(temp_db, mock_update, mock_context):
    """Тест обработки названия пространства - ошибка"""
    mock_update.message.text = "Тестовое пространство"
    mock_context.user_data['waiting_workspace_name'] = True
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.create_workspace.return_value = (False, None, "Ошибка")
        
        result = await process_workspace_name(mock_update, mock_context)
        
        assert result == 1  # WAITING_WORKSPACE_NAME
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_process_workspace_name_cancel(temp_db, mock_update, mock_context):
    """Тест обработки названия пространства - отмена"""
    mock_update.message.text = "/cancel"
    mock_context.user_data['waiting_workspace_name'] = True
    
    result = await process_workspace_name(mock_update, mock_context)
    
    from telegram.ext import ConversationHandler
    assert result == ConversationHandler.END
    assert 'waiting_workspace_name' not in mock_context.user_data


@pytest.mark.asyncio
async def test_delworkspace_command_success(temp_db, mock_update, mock_context):
    """Тест команды /delworkspace - успешное удаление"""
    from models.workspace import Workspace
    from datetime import datetime
    
    mock_context.args = ["Тестовое пространство"]
    workspace = Workspace(id=1, user_id=12345, name="Тестовое пространство", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.get_workspace_by_name.return_value = workspace
        mock_service.delete_workspace.return_value = (True, None)
        
        await delworkspace_command(mock_update, mock_context)
        
        mock_service.delete_workspace.assert_called_once_with(1, 12345)
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_delworkspace_command_not_found(temp_db, mock_update, mock_context):
    """Тест команды /delworkspace - пространство не найдено"""
    mock_context.args = ["Несуществующее"]
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.get_workspace_by_name.return_value = None
        
        await delworkspace_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert 'не найдено' in call_args.args[0].lower()


@pytest.mark.asyncio
async def test_renameworkspace_command_success(temp_db, mock_update, mock_context):
    """Тест команды /renameworkspace - успешное переименование"""
    from models.workspace import Workspace
    from datetime import datetime
    
    mock_context.args = ["Старое", "Новое"]
    workspace = Workspace(id=1, user_id=12345, name="Старое", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.list_workspaces.return_value = [workspace]
        mock_service.get_workspace_by_name.return_value = workspace
        mock_service.rename_workspace.return_value = (True, None)
        
        await renameworkspace_command(mock_update, mock_context)
        
        mock_service.rename_workspace.assert_called_once_with(1, 12345, "Новое")
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_renameworkspace_command_not_found(temp_db, mock_update, mock_context):
    """Тест команды /renameworkspace - пространство не найдено"""
    mock_context.args = ["Несуществующее", "Новое"]
    
    with patch('handlers.workspace.workspace_service') as mock_service:
        mock_service.list_workspaces.return_value = []
        mock_service.get_workspace_by_name.return_value = None
        
        await renameworkspace_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert 'не найдено' in call_args.args[0].lower()


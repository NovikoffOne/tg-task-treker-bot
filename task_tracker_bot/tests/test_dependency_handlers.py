"""
Тесты для handlers зависимостей досок (dependencies)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User

from handlers.dependency import (
    dependencies_command,
    newdependency_command,
    deldependency_command
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
async def test_dependencies_command_empty(mock_update, mock_context):
    """Тест команды /dependencies когда нет зависимостей"""
    from models.workspace import Workspace
    from datetime import datetime
    
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.dependency.workspace_repo') as mock_workspace_repo, \
         patch('handlers.dependency.dependency_service') as mock_dependency_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_dependency_service.list_dependencies.return_value = []
        
        await dependencies_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert 'нет зависимостей' in call_args.args[0].lower() or 'HTML' in call_args.kwargs.get('parse_mode', '')


@pytest.mark.asyncio
async def test_newdependency_command_success(mock_update, mock_context):
    """Тест команды /newdependency - успешное создание"""
    from models.workspace import Workspace
    from models.board import Board
    from models.column import Column
    from datetime import datetime
    
    mock_context.args = [
        "Подготовка->Дизайн",
        "Подготовка",
        "Готово",
        "Дизайн",
        "Очередь",
        "create_task"
    ]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    source_board = Board(id=1, workspace_id=1, name="Подготовка", created_at=datetime.now(), updated_at=datetime.now())
    target_board = Board(id=2, workspace_id=1, name="Дизайн", created_at=datetime.now(), updated_at=datetime.now())
    source_column = Column(id=1, board_id=1, name="Готово", created_at=datetime.now())
    target_column = Column(id=2, board_id=2, name="Очередь", created_at=datetime.now())
    
    with patch('handlers.dependency.workspace_repo') as mock_workspace_repo, \
         patch('handlers.dependency.board_repo') as mock_board_repo, \
         patch('handlers.dependency.column_repo') as mock_column_repo, \
         patch('handlers.dependency.dependency_service') as mock_dependency_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_board_repo.get_by_name.side_effect = [source_board, target_board]
        mock_column_repo.get_by_name.side_effect = [source_column, target_column]
        mock_dependency_service.create_dependency.return_value = (True, 1, None)
        
        await newdependency_command(mock_update, mock_context)
        
        mock_dependency_service.create_dependency.assert_called_once()
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_deldependency_command_success(mock_update, mock_context):
    """Тест команды /deldependency - успешное удаление"""
    mock_context.args = ["1"]
    
    with patch('handlers.dependency.dependency_service') as mock_dependency_service:
        mock_dependency_service.delete_dependency.return_value = (True, None)
        
        await deldependency_command(mock_update, mock_context)
        
        mock_dependency_service.delete_dependency.assert_called_once_with(1)
        mock_update.message.reply_text.assert_called()


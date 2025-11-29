"""
Тесты для handlers досок (boards)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User

from handlers.board import (
    boards_command,
    newboard_command,
    delboard_command,
    board_command,
    columns_command,
    addcolumn_command,
    delcolumn_command,
    boardlist_command
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
async def test_boards_command_no_workspace(mock_update, mock_context):
    """Тест команды /boards когда нет пространств"""
    with patch('handlers.board.workspace_repo') as mock_repo:
        mock_repo.get_all_by_user.return_value = []
        
        await boards_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert 'нет пространств' in call_args.args[0].lower()


@pytest.mark.asyncio
async def test_newboard_command_success(mock_update, mock_context):
    """Тест команды /newboard - успешное создание"""
    from models.workspace import Workspace
    from datetime import datetime
    
    mock_context.args = ["Дизайн"]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.board.workspace_repo') as mock_workspace_repo, \
         patch('handlers.board.board_service') as mock_board_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_board_service.create_board.return_value = (True, 1, None)
        
        await newboard_command(mock_update, mock_context)
        
        mock_board_service.create_board.assert_called_once_with(1, "Дизайн")
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_board_command_success(mock_update, mock_context):
    """Тест команды /board - успешный просмотр"""
    from models.workspace import Workspace
    from models.board import Board
    from datetime import datetime
    
    mock_context.args = ["Дизайн"]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    board = Board(id=1, workspace_id=1, name="Дизайн", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.board.workspace_repo') as mock_workspace_repo, \
         patch('handlers.board.board_service') as mock_board_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_board_service.get_board_by_name.return_value = board
        
        await board_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_addcolumn_command_success(mock_update, mock_context):
    """Тест команды /addcolumn - успешное добавление"""
    from models.workspace import Workspace
    from models.board import Board
    from datetime import datetime
    
    mock_context.args = ["Дизайн", "План на неделю"]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    board = Board(id=1, workspace_id=1, name="Дизайн", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.board.workspace_repo') as mock_workspace_repo, \
         patch('handlers.board.board_service') as mock_board_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_board_service.get_board_by_name.return_value = board
        mock_board_service.create_column.return_value = (True, 1, None)
        
        await addcolumn_command(mock_update, mock_context)
        
        mock_board_service.create_column.assert_called_once_with(1, "План на неделю")
        mock_update.message.reply_text.assert_called()


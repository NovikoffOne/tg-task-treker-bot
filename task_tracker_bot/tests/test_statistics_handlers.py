"""
Тесты для handlers статистики (statistics)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User

from handlers.statistics import (
    stats_command,
    statsproject_command,
    statsboard_command
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
async def test_stats_command_success(mock_update, mock_context):
    """Тест команды /stats - успешный просмотр статистики"""
    from models.workspace import Workspace
    from datetime import datetime
    
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    stats = {
        'workspaces': 1,
        'boards': 2,
        'tasks': 10,
        'completed': 5,
        'in_progress': 3,
        'queued': 2
    }
    
    with patch('handlers.statistics.workspace_repo') as mock_workspace_repo, \
         patch('handlers.statistics.stats_service') as mock_stats_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_stats_service.get_workspace_stats.return_value = stats
        
        await stats_command(mock_update, mock_context)
        
        mock_stats_service.get_workspace_stats.assert_called_once_with(1)
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_statsproject_command_success(mock_update, mock_context):
    """Тест команды /statsproject - успешный просмотр статистики проекта"""
    mock_context.args = ["5001"]
    stats = {
        'project_id': '5001',
        'project_name': 'Pictory Ai',
        'total_tasks': 5,
        'completed': 2,
        'in_progress': 1,
        'queued': 2
    }
    
    with patch('handlers.statistics.stats_service') as mock_stats_service:
        mock_stats_service.get_project_stats.return_value = stats
        
        await statsproject_command(mock_update, mock_context)
        
        mock_stats_service.get_project_stats.assert_called_once_with("5001")
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_statsboard_command_success(mock_update, mock_context):
    """Тест команды /statsboard - успешный просмотр статистики доски"""
    from models.workspace import Workspace
    from models.board import Board
    from datetime import datetime
    
    mock_context.args = ["Дизайн"]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    board = Board(id=1, workspace_id=1, name="Дизайн", created_at=datetime.now(), updated_at=datetime.now())
    stats = {
        'board_id': 1,
        'board_name': 'Дизайн',
        'total_tasks': 10,
        'by_column': {},
        'by_priority': {}
    }
    
    with patch('handlers.statistics.workspace_repo') as mock_workspace_repo, \
         patch('handlers.statistics.board_repo') as mock_board_repo, \
         patch('handlers.statistics.stats_service') as mock_stats_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_board_repo.get_by_name.return_value = board
        mock_stats_service.get_board_stats.return_value = stats
        
        await statsboard_command(mock_update, mock_context)
        
        mock_stats_service.get_board_stats.assert_called_once_with(1)
        mock_update.message.reply_text.assert_called()


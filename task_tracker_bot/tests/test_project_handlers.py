"""
Тесты для handlers проектов (projects)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User

from handlers.project import (
    projects_command,
    newproject_command,
    project_command,
    projectdashboard_command,
    delproject_command
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
async def test_projects_command_no_workspace(mock_update, mock_context):
    """Тест команды /projects когда нет пространств"""
    with patch('handlers.project.workspace_repo') as mock_repo:
        mock_repo.get_all_by_user.return_value = []
        
        await projects_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert 'нет пространств' in call_args.args[0].lower()


@pytest.mark.asyncio
async def test_newproject_command_success(mock_update, mock_context):
    """Тест команды /newproject - успешное создание"""
    from models.workspace import Workspace
    from datetime import datetime
    
    mock_context.args = ["5001", "Pictory Ai"]
    workspace = Workspace(id=1, user_id=12345, name="Работа", created_at=datetime.now(), updated_at=datetime.now())
    
    with patch('handlers.project.workspace_repo') as mock_workspace_repo, \
         patch('handlers.project.project_service') as mock_project_service:
        mock_workspace_repo.get_all_by_user.return_value = [workspace]
        mock_project_service.create_project.return_value = (True, "5001", None)
        
        await newproject_command(mock_update, mock_context)
        
        mock_project_service.create_project.assert_called_once_with("5001", 1, "Pictory Ai")
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_project_command_success(mock_update, mock_context):
    """Тест команды /project - успешный просмотр"""
    from models.project import Project
    
    mock_context.args = ["5001"]
    project = Project(id="5001", workspace_id=1, name="Pictory Ai")
    
    with patch('handlers.project.project_service') as mock_project_service:
        mock_project_service.get_project.return_value = project
        
        await project_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_project_command_not_found(mock_update, mock_context):
    """Тест команды /project - проект не найден"""
    mock_context.args = ["9999"]
    
    with patch('handlers.project.project_service') as mock_project_service:
        mock_project_service.get_project.return_value = None
        
        await project_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args
        assert 'не найден' in call_args.args[0].lower()


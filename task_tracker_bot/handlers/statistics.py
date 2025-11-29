"""
Handlers для статистики
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.column_repository import ColumnRepository
from services.statistics_service import StatisticsService
from utils.formatters import format_stats, format_project_stats, format_board_stats

# Инициализация
db = Database()
task_repo = TaskRepository(db)
project_repo = ProjectRepository(db)
board_repo = BoardRepository(db)
workspace_repo = WorkspaceRepository(db)
column_repo = ColumnRepository(db)
stats_service = StatisticsService(task_repo, project_repo, board_repo, workspace_repo, column_repo)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Общая статистика"""
    user_id = update.effective_user.id
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ У вас нет пространств")
        return
    
    workspace_id = workspaces[0].id
    
    try:
        stats = stats_service.get_workspace_stats(workspace_id)
        text = format_stats(stats)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def statsproject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика проекта"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID проекта: /statsproject <id>")
        return
    
    project_id = context.args[0]
    
    try:
        stats = stats_service.get_project_stats(project_id)
        if not stats:
            await update.message.reply_text("❌ Проект не найден")
            return
        
        text = format_project_stats(stats)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def statsboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика доски"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название доски: /statsboard <название>")
        return
    
    user_id = update.effective_user.id
    board_name = " ".join(context.args)
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    board = board_repo.get_by_name(workspace_id, board_name)
    if not board:
        await update.message.reply_text("❌ Доска не найдена")
        return
    
    try:
        stats = stats_service.get_board_stats(board.id)
        text = format_board_stats(stats)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


"""
Handlers для работы с Project
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.project_repository import ProjectRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.task_repository import TaskRepository
from repositories.workspace_repository import WorkspaceRepository
from services.project_service import ProjectService
from utils.formatters import format_project, format_project_dashboard, format_project_list
from utils.keyboards import project_dashboard_keyboard

# Инициализация
db = Database()
project_repo = ProjectRepository(db)
board_repo = BoardRepository(db)
column_repo = ColumnRepository(db)
task_repo = TaskRepository(db)
workspace_repo = WorkspaceRepository(db)
project_service = ProjectService(project_repo, board_repo, column_repo, task_repo)

async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список проектов с улучшенным UI"""
    user_id = update.effective_user.id
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text(
            "❌ <b>У вас нет пространств</b>\n\n"
            "Создайте пространство:\n"
            "<code>/newworkspace &lt;название&gt;</code>",
            parse_mode='HTML'
        )
        return
    
    workspace_id = workspaces[0].id
    
    try:
        projects = project_service.list_projects(workspace_id)
        text = format_project_list(projects)
        from utils.keyboards import projects_keyboard
        await update.message.reply_text(
            text,
            reply_markup=projects_keyboard(projects)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def newproject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать проект с автоматическими задачами на досках"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите ID и название: /newproject <id> <название>")
        return
    
    user_id = update.effective_user.id
    project_id = context.args[0]
    project_name = " ".join(context.args[1:])
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ У вас нет пространств. Создайте пространство: /newworkspace <название>")
        return
    
    workspace_id = workspaces[0].id
    
    success, created_id, error = project_service.create_project(project_id, workspace_id, project_name)
    if success:
        await update.message.reply_text(
            f"✅ Проект '{project_id} {project_name}' создан!\n"
            f"Задача создана на доске 'Подготовка'.\n"
            f"Задачи на других досках будут создаваться автоматически через зависимости досок."
        )
    else:
        await update.message.reply_text(f"❌ {error}")

async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать проект"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID проекта: /project <id>")
        return
    
    project_id = context.args[0]
    
    project = project_service.get_project(project_id)
    if not project:
        await update.message.reply_text("❌ Проект не найден")
        return
    
    try:
        text = format_project(project, project_service, task_repo, column_repo, board_repo)
        await update.message.reply_text(
            text,
            reply_markup=project_dashboard_keyboard(project_id),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def projectdashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать дашборд проекта"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID проекта: /projectdashboard <id>")
        return
    
    project_id = context.args[0]
    
    project = project_service.get_project(project_id)
    if not project:
        await update.message.reply_text("❌ Проект не найден")
        return
    
    try:
        text = format_project_dashboard(project, project_service, task_repo, column_repo, board_repo)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def delproject_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить проект"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID проекта: /delproject <id>")
        return
    
    project_id = context.args[0]
    
    success, error = project_service.delete_project(project_id)
    if success:
        await update.message.reply_text(f"✅ Проект '{project_id}' удален (задачи остались)")
    else:
        await update.message.reply_text(f"❌ {error}")


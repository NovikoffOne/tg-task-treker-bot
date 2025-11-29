"""
Handlers для работы с CustomField
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.custom_field_repository import CustomFieldRepository
from repositories.task_repository import TaskRepository
from repositories.workspace_repository import WorkspaceRepository
from services.sync_service import SyncService
from utils.validators import validate_url

# Инициализация
db = Database()
field_repo = CustomFieldRepository(db)
task_repo = TaskRepository(db)
workspace_repo = WorkspaceRepository(db)
sync_service = SyncService(task_repo, field_repo)

async def newfield_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать поле"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите название и тип: /newfield <название> <тип>")
        return
    
    user_id = update.effective_user.id
    name = context.args[0]
    field_type = context.args[1]
    
    valid_types = ['text', 'url', 'number', 'date', 'select']
    if field_type not in valid_types:
        await update.message.reply_text(f"❌ Некорректный тип. Допустимые: {', '.join(valid_types)}")
        return
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ У вас нет пространств")
        return
    
    workspace_id = workspaces[0].id
    
    try:
        field_id = field_repo.create(workspace_id, name, field_type)
        await update.message.reply_text(f"✅ Поле '{name}' создано (тип: {field_type})")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def addfield_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавить поле к задаче (с синхронизацией для проектов)"""
    if len(context.args) < 3:
        await update.message.reply_text("❌ Укажите ID задачи, название поля и значение: /addfield <id> <поле> <значение>")
        return
    
    try:
        task_id = int(context.args[0])
        field_name = context.args[1]
        value = " ".join(context.args[2:])
        
        task = task_repo.get_by_id(task_id)
        if not task:
            await update.message.reply_text("❌ Задача не найдена")
            return
        
        # Получить поле
        workspace_id = None
        if task.project_id:
            project = project_repo.get_by_id(task.project_id)
            if project:
                workspace_id = project.workspace_id
        else:
            column = column_repo.get_by_id(task.column_id)
            if column:
                board = board_repo.get_by_id(column.board_id)
                if board:
                    workspace_id = board.workspace_id
        
        if not workspace_id:
            await update.message.reply_text("❌ Не удалось определить пространство")
            return
        
        field = field_repo.get_by_name(workspace_id, field_name)
        if not field:
            await update.message.reply_text("❌ Поле не найдено")
            return
        
        # Валидация значения по типу
        if field.field_type == 'url':
            is_valid, error = validate_url(value)
            if not is_valid:
                await update.message.reply_text(f"❌ {error}")
                return
        
        # Если задача принадлежит проекту, автоматически включить синхронизацию для этого поля
        if task.project_id:
            field_repo.enable_project_sync(task.project_id, field.id)
        
        # Синхронизировать поле
        success, error = sync_service.sync_field_to_project(task_id, field.id, value)
        if success:
            if task.project_id:
                await update.message.reply_text(f"✅ Поле '{field_name}' добавлено и синхронизировано со всеми задачами проекта")
            else:
                await update.message.reply_text(f"✅ Поле '{field_name}' добавлено")
        else:
            await update.message.reply_text(f"❌ {error}")
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

# Добавить импорты для addfield_command
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository

project_repo = ProjectRepository(db)
column_repo = ColumnRepository(db)
board_repo = BoardRepository(db)


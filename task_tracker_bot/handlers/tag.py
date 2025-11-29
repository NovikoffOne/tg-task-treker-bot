"""
Handlers для работы с метками (Tags)
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.tag_repository import TagRepository
from repositories.task_repository import TaskRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository

# Инициализация
db = Database()
tag_repo = TagRepository(db)
task_repo = TaskRepository(db)
workspace_repo = WorkspaceRepository(db)
column_repo = ColumnRepository(db)
board_repo = BoardRepository(db)

async def newtag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать метку"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название метки: /newtag <название> [цвет]")
        return
    
    user_id = update.effective_user.id
    name = context.args[0]
    color = context.args[1] if len(context.args) > 1 else "#3498db"
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ У вас нет пространств")
        return
    
    workspace_id = workspaces[0].id
    
    # Проверить существование метки
    existing_tag = tag_repo.get_by_name(workspace_id, name)
    if existing_tag:
        await update.message.reply_text(f"⚠️ Метка '{name}' уже существует")
        return
    
    try:
        tag_id = tag_repo.create(workspace_id, name, color)
        await update.message.reply_text(f"✅ Метка '{name}' создана (цвет: {color})")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def addtag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавить метку к задаче"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите ID задачи и название метки: /addtag <task_id> <метка>")
        return
    
    try:
        task_id = int(context.args[0])
        tag_name = context.args[1]
        
        task = task_repo.get_by_id(task_id)
        if not task:
            await update.message.reply_text("❌ Задача не найдена")
            return
        
        # Получить workspace_id
        column = column_repo.get_by_id(task.column_id)
        if not column:
            await update.message.reply_text("❌ Колонка не найдена")
            return
        
        board = board_repo.get_by_id(column.board_id)
        if not board:
            await update.message.reply_text("❌ Доска не найдена")
            return
        
        workspace_id = board.workspace_id
        
        # Найти метку
        tag = tag_repo.get_by_name(workspace_id, tag_name)
        if not tag:
            await update.message.reply_text(f"❌ Метка '{tag_name}' не найдена. Создайте её: /newtag {tag_name}")
            return
        
        # Проверить, не добавлена ли уже метка
        task_tags = tag_repo.get_task_tags(task_id)
        if any(t.id == tag.id for t in task_tags):
            await update.message.reply_text(f"⚠️ Метка '{tag_name}' уже добавлена к задаче")
            return
        
        # Добавить метку
        success = tag_repo.add_to_task(task_id, tag.id)
        if success:
            await update.message.reply_text(f"✅ Метка '{tag_name}' добавлена к задаче #{task_id}")
        else:
            await update.message.reply_text("❌ Ошибка при добавлении метки")
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def deltag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить метку с задачи"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите ID задачи и название метки: /deltag <task_id> <метка>")
        return
    
    try:
        task_id = int(context.args[0])
        tag_name = context.args[1]
        
        task = task_repo.get_by_id(task_id)
        if not task:
            await update.message.reply_text("❌ Задача не найдена")
            return
        
        # Получить workspace_id
        column = column_repo.get_by_id(task.column_id)
        if not column:
            await update.message.reply_text("❌ Колонка не найдена")
            return
        
        board = board_repo.get_by_id(column.board_id)
        if not board:
            await update.message.reply_text("❌ Доска не найдена")
            return
        
        workspace_id = board.workspace_id
        
        # Найти метку
        tag = tag_repo.get_by_name(workspace_id, tag_name)
        if not tag:
            await update.message.reply_text(f"❌ Метка '{tag_name}' не найдена")
            return
        
        # Удалить метку
        success = tag_repo.remove_from_task(task_id, tag.id)
        if success:
            await update.message.reply_text(f"✅ Метка '{tag_name}' удалена с задачи #{task_id}")
        else:
            await update.message.reply_text("❌ Ошибка при удалении метки или метка не была добавлена")
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


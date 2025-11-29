"""
Шаблон handlers/tasks.py
Обработчики команд для работы с задачами
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from typing import Optional

from database import Database
from models import Task
from utils.validators import validate_title, validate_description, validate_task_id
from utils.formatters import format_task, format_tasks_list
from utils.keyboards import task_actions_keyboard, pagination_keyboard
from config import Config

db = Database()

# Состояния для ConversationHandler
WAITING_TITLE, WAITING_DESCRIPTION = range(2)
WAITING_EDIT_FIELD, WAITING_EDIT_VALUE = range(2, 4)

async def new_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало создания задачи"""
    await update.message.reply_text("Введите название задачи:")
    return WAITING_TITLE

async def process_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка названия задачи"""
    title = update.message.text
    
    is_valid, error = validate_title(title)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return WAITING_TITLE
    
    context.user_data['task_title'] = title
    await update.message.reply_text(
        "Введите описание задачи (или отправьте /skip для пропуска):"
    )
    return WAITING_DESCRIPTION

async def process_task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка описания задачи"""
    user_id = update.effective_user.id
    title = context.user_data.get('task_title')
    
    if update.message.text == '/skip':
        description = None
    else:
        description = update.message.text
        is_valid, error = validate_description(description)
        if not is_valid:
            await update.message.reply_text(f"❌ {error}")
            return WAITING_DESCRIPTION
    
    # Создание задачи
    try:
        task_id = db.create_task(user_id, title, description)
        task = db.get_task(task_id, user_id)
        
        await update.message.reply_text(
            f"✅ Задача создана!\n\n{format_task(task)}",
            reply_markup=task_actions_keyboard(task_id)
        )
        
        # Очистка данных
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при создании задачи. Попробуйте позже.")
        context.user_data.clear()
        return ConversationHandler.END

async def list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE, status: Optional[str] = None) -> None:
    """Показать список задач"""
    user_id = update.effective_user.id
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    
    try:
        tasks, total = db.get_user_tasks(
            user_id, 
            status=status,
            limit=Config.TASKS_PER_PAGE,
            offset=(page - 1) * Config.TASKS_PER_PAGE
        )
        
        total_pages = (total + Config.TASKS_PER_PAGE - 1) // Config.TASKS_PER_PAGE
        
        text = format_tasks_list(tasks, page, total, total_pages)
        keyboard = pagination_keyboard(page, total_pages, callback_prefix="page_all")
        
        await update.message.reply_text(text, reply_markup=keyboard)
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при получении задач.")

async def active_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать активные задачи"""
    await list_tasks_command(update, context, status='active')

async def done_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать завершенные задачи"""
    await list_tasks_command(update, context, status='completed')

async def edit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало редактирования задачи"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID задачи: /edit <id>")
        return ConversationHandler.END
    
    is_valid, task_id, error = validate_task_id(context.args[0])
    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    task = db.get_task(task_id, user_id)
    
    if not task:
        await update.message.reply_text("❌ Задача не найдена.")
        return ConversationHandler.END
    
    context.user_data['edit_task_id'] = task_id
    await update.message.reply_text(
        f"Что вы хотите изменить?\n\n"
        f"Текущая задача:\n{format_task(task)}\n\n"
        f"Отправьте 'название' или 'описание':"
    )
    return WAITING_EDIT_FIELD

async def process_edit_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка редактирования задачи"""
    # Реализация обработки редактирования
    # См. полную реализацию в TECHNICAL_SPECIFICATION.md
    pass

async def delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить задачу"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID задачи: /delete <id>")
        return
    
    is_valid, task_id, error = validate_task_id(context.args[0])
    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return
    
    user_id = update.effective_user.id
    task = db.get_task(task_id, user_id)
    
    if not task:
        await update.message.reply_text("❌ Задача не найдена.")
        return
    
    # Удаление через callback с подтверждением
    from utils.keyboards import confirm_delete_keyboard
    await update.message.reply_text(
        f"⚠️ Вы уверены, что хотите удалить задачу?\n\n{format_task(task)}",
        reply_markup=confirm_delete_keyboard(task_id)
    )

async def done_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отметить задачу выполненной"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID задачи: /done_task <id>")
        return
    
    is_valid, task_id, error = validate_task_id(context.args[0])
    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return
    
    user_id = update.effective_user.id
    
    if db.update_task_status(task_id, user_id, 'completed'):
        task = db.get_task(task_id, user_id)
        await update.message.reply_text(
            f"✅ Задача отмечена как выполненная!\n\n{format_task(task)}",
            reply_markup=task_actions_keyboard(task_id)
        )
    else:
        await update.message.reply_text("❌ Задача не найдена или уже выполнена.")


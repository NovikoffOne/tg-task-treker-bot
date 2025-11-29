"""
Шаблон handlers/callbacks.py
Обработка inline-кнопок
"""
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from utils.formatters import format_task, format_tasks_list
from utils.keyboards import task_actions_keyboard, pagination_keyboard, confirm_delete_keyboard, main_menu_keyboard
from config import Config

db = Database()

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех callback-запросов"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    # Разбор callback_data
    if callback_data.startswith("done_"):
        task_id = int(callback_data.split("_")[1])
        await handle_done_task(query, task_id, user_id)
    
    elif callback_data.startswith("edit_"):
        task_id = int(callback_data.split("_")[1])
        await handle_edit_task(query, task_id, user_id)
    
    elif callback_data.startswith("delete_"):
        task_id = int(callback_data.split("_")[1])
        await handle_delete_task(query, task_id, user_id)
    
    elif callback_data.startswith("confirm_delete_"):
        task_id = int(callback_data.split("_")[2])
        await handle_confirm_delete(query, task_id, user_id)
    
    elif callback_data.startswith("cancel_delete_"):
        await query.edit_message_text("❌ Удаление отменено.")
    
    elif callback_data.startswith("page_"):
        page = int(callback_data.split("_")[1])
        status = callback_data.split("_")[2] if len(callback_data.split("_")) > 2 else None
        await handle_pagination(query, page, user_id, status)
    
    elif callback_data == "list_tasks":
        await handle_list_tasks(query, user_id)
    
    elif callback_data == "main_menu":
        await query.edit_message_text(
            "🏠 Главное меню",
            reply_markup=None
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu_keyboard()
        )

async def handle_done_task(query, task_id: int, user_id: int) -> None:
    """Обработка отметки задачи выполненной"""
    if db.update_task_status(task_id, user_id, 'completed'):
        task = db.get_task(task_id, user_id)
        await query.edit_message_text(
            f"✅ Задача отмечена как выполненная!\n\n{format_task(task)}",
            reply_markup=task_actions_keyboard(task_id)
        )
    else:
        await query.answer("❌ Задача не найдена.", show_alert=True)

async def handle_edit_task(query, task_id: int, user_id: int) -> None:
    """Обработка редактирования задачи"""
    task = db.get_task(task_id, user_id)
    if task:
        await query.edit_message_text(
            f"✏️ Редактирование задачи:\n\n{format_task(task)}\n\n"
            f"Используйте команду /edit {task_id} для редактирования.",
            reply_markup=task_actions_keyboard(task_id)
        )
    else:
        await query.answer("❌ Задача не найдена.", show_alert=True)

async def handle_delete_task(query, task_id: int, user_id: int) -> None:
    """Обработка запроса на удаление"""
    task = db.get_task(task_id, user_id)
    if task:
        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите удалить задачу?\n\n{format_task(task)}",
            reply_markup=confirm_delete_keyboard(task_id)
        )
    else:
        await query.answer("❌ Задача не найдена.", show_alert=True)

async def handle_confirm_delete(query, task_id: int, user_id: int) -> None:
    """Обработка подтверждения удаления"""
    if db.delete_task(task_id, user_id):
        await query.edit_message_text("✅ Задача удалена.")
    else:
        await query.answer("❌ Задача не найдена.", show_alert=True)

async def handle_pagination(query, page: int, user_id: int, status: Optional[str] = None) -> None:
    """Обработка пагинации"""
    tasks, total = db.get_user_tasks(
        user_id,
        status=status,
        limit=Config.TASKS_PER_PAGE,
        offset=(page - 1) * Config.TASKS_PER_PAGE
    )
    
    total_pages = (total + Config.TASKS_PER_PAGE - 1) // Config.TASKS_PER_PAGE
    text = format_tasks_list(tasks, page, total, total_pages)
    keyboard = pagination_keyboard(page, total_pages, callback_prefix=f"page_{status or 'all'}")
    
    await query.edit_message_text(text, reply_markup=keyboard)

async def handle_list_tasks(query, user_id: int) -> None:
    """Обработка возврата к списку задач"""
    await handle_pagination(query, 1, user_id, None)


"""
Handlers для работы с Todo List
"""
import logging
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from repositories.personal_task_repository import PersonalTaskRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from services.todo_service import TodoService
from utils.date_parser import DateParser
from utils.task_classifier import TaskClassifier
from utils.formatters import format_todo_list
from utils.keyboards import todo_list_keyboard

logger = logging.getLogger(__name__)

# Инициализация сервисов
db = Database()
personal_task_repo = PersonalTaskRepository(db)
task_repo = TaskRepository(db)
project_repo = ProjectRepository(db)
column_repo = ColumnRepository(db)
board_repo = BoardRepository(db)
date_parser = DateParser()
task_classifier = TaskClassifier(project_repo)
todo_service = TodoService(
    personal_task_repo,
    task_repo,
    project_repo,
    column_repo,
    board_repo,
    date_parser,
    task_classifier
)

async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /todo [дата]"""
    import time
    start_time = time.time()
    user_id = update.effective_user.id
    args = context.args or []
    
    logger.info(f"Обработка команды /todo для user_id={user_id}, args={args}")
    
    # Получить дату из аргументов или использовать сегодня
    target_date = datetime.now().date()
    if context.args:
        date_arg = " ".join(context.args)
        logger.debug(f"Парсинг даты: '{date_arg}'")
        parsed_date = date_parser.parse_date(date_arg)
        if parsed_date:
            target_date = parsed_date
            logger.debug(f"Дата распарсена: '{date_arg}' → {parsed_date}")
        else:
            logger.warning(f"Не удалось распарсить дату: '{date_arg}', используется сегодня")
            await update.message.reply_text(
                f"❌ Не удалось распарсить дату: {date_arg}\n"
                f"Используется сегодня: {target_date.strftime('%d.%m.%Y')}"
            )
    
    # Получить туду-лист
    try:
        # Получаем workspace_id из первого workspace пользователя
        from repositories.workspace_repository import WorkspaceRepository
        workspace_repo = WorkspaceRepository(db)
        workspaces = workspace_repo.get_all_by_user(user_id)
        
        if not workspaces:
            await update.message.reply_text(
                "❌ У вас нет пространств. Создайте пространство: /newworkspace <название>"
            )
            return
        
        workspace_id = workspaces[0].id
        
        todo_list = todo_service.get_todo_list(
            user_id=user_id,
            target_date=target_date,
            include_work_tasks=True
        )
        
        personal_tasks_count = len(todo_list.get("personal_tasks", []))
        work_tasks_count = len(todo_list.get("work_tasks", []))
        logger.info(f"Получен туду-лист: личных задач={personal_tasks_count}, рабочих={work_tasks_count}")
        
        # Форматирование и отправка
        formatted_text = format_todo_list(todo_list)
        keyboard = todo_list_keyboard(target_date, todo_list.get("personal_tasks", []))
        
        elapsed_time = time.time() - start_time
        logger.info(f"Команда /todo выполнена за {elapsed_time:.2f}s для user_id={user_id}, date={target_date}")
        
        await update.message.reply_text(
            formatted_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Ошибка при получении туду-листа (время: {elapsed_time:.2f}s): {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка при получении туду-листа: {str(e)}")

async def handle_todo_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора даты через callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Извлечь дату из callback_data (формат: todo_date_2025-11-30)
    if callback_data.startswith("todo_date_"):
        date_str = callback_data.replace("todo_date_", "")
        try:
            target_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            await query.edit_message_text("❌ Некорректная дата")
            return
    else:
        target_date = datetime.now().date()
    
    # Получить туду-лист
    try:
        from task_tracker_bot.repositories.workspace_repository import WorkspaceRepository
        workspace_repo = WorkspaceRepository(db)
        workspaces = workspace_repo.get_all_by_user(user_id)
        
        if not workspaces:
            await query.edit_message_text("❌ У вас нет пространств")
            return
        
        workspace_id = workspaces[0].id
        
        todo_list = todo_service.get_todo_list(
            user_id=user_id,
            target_date=target_date,
            include_work_tasks=True
        )
        
        formatted_text = format_todo_list(todo_list)
        keyboard = todo_list_keyboard(target_date, todo_list.get("personal_tasks", []))
        
        await query.edit_message_text(
            formatted_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при получении туду-листа: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def handle_todo_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Навигация по датам (вчера/сегодня/завтра)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Извлечь дату из callback_data (формат: todo_nav_prev_2025-11-29)
    target_date = datetime.now().date()
    if "_" in callback_data:
        parts = callback_data.split("_")
        if len(parts) >= 4:
            try:
                date_str = "_".join(parts[3:])  # Берем все после третьего подчеркивания
                target_date = datetime.fromisoformat(date_str).date()
            except ValueError:
                # Если не удалось распарсить, используем логику по направлению
                today = datetime.now().date()
                if "prev" in callback_data:
                    target_date = today - timedelta(days=1)
                elif "next" in callback_data:
                    target_date = today + timedelta(days=1)
                else:
                    target_date = today
    
    # Получить туду-лист
    try:
        from task_tracker_bot.repositories.workspace_repository import WorkspaceRepository
        workspace_repo = WorkspaceRepository(db)
        workspaces = workspace_repo.get_all_by_user(user_id)
        
        if not workspaces:
            await query.edit_message_text("❌ У вас нет пространств")
            return
        
        workspace_id = workspaces[0].id
        
        todo_list = todo_service.get_todo_list(
            user_id=user_id,
            target_date=target_date,
            include_work_tasks=True
        )
        
        formatted_text = format_todo_list(todo_list)
        keyboard = todo_list_keyboard(target_date, todo_list.get("personal_tasks", []))
        
        await query.edit_message_text(
            formatted_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при навигации по туду-листу: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def handle_mark_todo_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отметка задачи как выполненной"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Извлечь task_id из callback_data (формат: todo_complete_123)
    if callback_data.startswith("todo_complete_"):
        try:
            task_id = int(callback_data.replace("todo_complete_", ""))
        except ValueError:
            await query.edit_message_text("❌ Некорректный ID задачи")
            return
    else:
        await query.edit_message_text("❌ Некорректный callback")
        return
    
    # Отметить задачу как выполненную
    try:
        success, error = todo_service.mark_personal_task_completed(task_id, user_id)
        if success:
            await query.answer("✅ Задача отмечена как выполненная", show_alert=False)
            
            # Обновить сообщение с туду-листом
            # Получаем текущую дату из сообщения или используем сегодня
            today = datetime.now().date()
            todo_list = todo_service.get_todo_list(
                user_id=user_id,
                target_date=today,
                include_work_tasks=True
            )
            
            formatted_text = format_todo_list(todo_list)
            keyboard = todo_list_keyboard(today, todo_list.get("personal_tasks", []))
            
            await query.edit_message_text(
                formatted_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await query.answer(f"❌ {error}", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отметке задачи: {e}", exc_info=True)
        await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


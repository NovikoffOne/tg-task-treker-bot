"""
Главный файл для запуска Advanced Telegram Task Tracker Bot
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, ContextTypes

from config import Config
from database import Database
from handlers.start import start_command, help_command, menu_command, start_test_basecase_command, test_handlers_command
from handlers.workspace import (
    workspaces_command, newworkspace_command, process_workspace_name,
    delworkspace_command, renameworkspace_command, WAITING_WORKSPACE_NAME
)
from handlers.board import boards_command, newboard_command, delboard_command, board_command, columns_command, addcolumn_command, delcolumn_command, boardlist_command
from handlers.project import projects_command, newproject_command, project_command, projectdashboard_command, delproject_command
from handlers.task import (
    newtask_command, process_task_board, process_task_column, process_task_title, process_task_description,
    task_command, movetask_command, priority_command, deltask_command, mytasks_command, today_command, deadline_command
)
from handlers.dependency import dependencies_command, newdependency_command, deldependency_command
from handlers.field import newfield_command, addfield_command
from handlers.tag import newtag_command, addtag_command, deltag_command
from handlers.statistics import stats_command, statsproject_command, statsboard_command
from handlers.menu_buttons import handle_menu_button
from handlers.ai_handler import ai_command, handle_ai_message
from handlers.todo_handler import (
    todo_command, handle_todo_date_callback, 
    handle_todo_navigation, handle_mark_todo_completed
)
from callbacks.handle_callbacks import handle_callback_query

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Временно включено для отладки промптов
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_TASK_BOARD, WAITING_TASK_COLUMN, WAITING_TASK_TITLE, WAITING_TASK_DESCRIPTION = range(4)
WAITING_WORKSPACE_NAME = 10
WAITING_BOARD_NAME = 11
WAITING_PROJECT_ID = 12
WAITING_PROJECT_NAME = 13

def setup_handlers(application: Application) -> None:
    """Регистрация всех обработчиков команд"""
    
    # Базовые команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("test_handlers", test_handlers_command))
    
    # AI команда
    application.add_handler(CommandHandler("ai", ai_command))
    
    # Команда для запуска базового теста
    try:
        application.add_handler(CommandHandler("start_test_basecase", start_test_basecase_command))
        logger.info("✅ Команда /start_test_basecase зарегистрирована")
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации команды /start_test_basecase: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Обработка упоминаний бота с тегом @start_test_baseCase
    async def handle_test_mention(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка упоминаний бота с тегом @start_test_baseCase"""
        if update.message and update.message.text:
            text = update.message.text.lower()
            if "@start_test_basecase" in text or "start_test_basecase" in text:
                logger.info(f"Тег найден в сообщении: {update.message.text}")
                await start_test_basecase_command(update, context)
    
    # Обработка текстовых сообщений с тегом (в группе 0, до других обработчиков)
    # Используем простую проверку внутри обработчика вместо фильтра
    async def handle_text_with_test_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка текстовых сообщений с проверкой тега"""
        logger.info(f"handle_text_with_test_tag вызван: text={update.message.text if update.message else None}")
        if update.message and update.message.text:
            text = update.message.text.lower()
            if "@start_test_basecase" in text or "start_test_basecase" in text:
                logger.info("Тег найден, обрабатываем")
                await handle_test_mention(update, context)
            else:
                # Если тег не найден, передаем обработку дальше
                logger.info(f"handle_text_with_test_tag: тег не найден, передаем дальше: {update.message.text[:50]}")
                return
    
    # Регистрируем обработчик для текстовых сообщений
    try:
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_with_test_tag
        ), group=0)
        logger.info("Обработчик тега @start_test_basecase зарегистрирован")
    except Exception as e:
        logger.error(f"Ошибка регистрации обработчика тега: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Пространства
    application.add_handler(CommandHandler("workspaces", workspaces_command))
    
    # Создание пространства (ConversationHandler)
    workspace_conv = ConversationHandler(
        entry_points=[
            CommandHandler("newworkspace", newworkspace_command),
        ],
        states={
            WAITING_WORKSPACE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_workspace_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(workspace_conv)
    
    # Обработка AI запросов (естественный язык) - РАНЬШЕ других обработчиков группы 1
    # Должен быть перед обработчиком workspace_name_input, чтобы не блокировать AI запросы
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message), group=1)
    
    # Обработка ввода названия пространства через кнопку (вне ConversationHandler)
    async def handle_workspace_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка ввода названия пространства через кнопку"""
        if context.user_data.get('waiting_workspace_name'):
            await process_workspace_name(update, context)
        else:
            # Если флаг не установлен, передаем обработку дальше
            # Не обрабатываем, чтобы сообщение прошло дальше по цепочке
            logger.debug(f"handle_workspace_name_input: пропущено (флаг не установлен), текст: {update.message.text if update.message else None}")
            return
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_workspace_name_input), group=1)
    
    application.add_handler(CommandHandler("delworkspace", delworkspace_command))
    application.add_handler(CommandHandler("renameworkspace", renameworkspace_command))
    
    # Доски
    application.add_handler(CommandHandler("boards", boards_command))
    application.add_handler(CommandHandler("newboard", newboard_command))
    application.add_handler(CommandHandler("delboard", delboard_command))
    application.add_handler(CommandHandler("board", board_command))
    application.add_handler(CommandHandler("boardlist", boardlist_command))
    application.add_handler(CommandHandler("columns", columns_command))
    application.add_handler(CommandHandler("addcolumn", addcolumn_command))
    application.add_handler(CommandHandler("delcolumn", delcolumn_command))
    
    # Проекты
    application.add_handler(CommandHandler("projects", projects_command))
    application.add_handler(CommandHandler("newproject", newproject_command))
    application.add_handler(CommandHandler("project", project_command))
    application.add_handler(CommandHandler("projectdashboard", projectdashboard_command))
    application.add_handler(CommandHandler("delproject", delproject_command))
    
    # Создание задачи (ConversationHandler)
    task_conv = ConversationHandler(
        entry_points=[
            CommandHandler("newtask", newtask_command),
        ],
        states={
            WAITING_TASK_BOARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_board)
            ],
            WAITING_TASK_COLUMN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_column)
            ],
            WAITING_TASK_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_title)
            ],
            WAITING_TASK_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_description),
                CommandHandler("skip", process_task_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(task_conv)
    
    # Задачи
    application.add_handler(CommandHandler("task", task_command))
    application.add_handler(CommandHandler("movetask", movetask_command))
    application.add_handler(CommandHandler("priority", priority_command))
    application.add_handler(CommandHandler("deltask", deltask_command))
    application.add_handler(CommandHandler("mytasks", mytasks_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("deadline", deadline_command))
    
    # Todo List
    application.add_handler(CommandHandler("todo", todo_command))
    
    # Зависимости досок
    application.add_handler(CommandHandler("dependencies", dependencies_command))
    application.add_handler(CommandHandler("newdependency", newdependency_command))
    application.add_handler(CommandHandler("deldependency", deldependency_command))
    
    # Поля
    application.add_handler(CommandHandler("newfield", newfield_command))
    application.add_handler(CommandHandler("addfield", addfield_command))
    
    # Метки
    application.add_handler(CommandHandler("newtag", newtag_command))
    application.add_handler(CommandHandler("addtag", addtag_command))
    application.add_handler(CommandHandler("deltag", deltag_command))
    
    # Статистика
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("statsproject", statsproject_command))
    application.add_handler(CommandHandler("statsboard", statsboard_command))
    
    # Обработка inline-кнопок для туду-листа (до общего обработчика)
    async def handle_todo_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка callbacks для туду-листа"""
        query = update.callback_query
        if not query or not query.data:
            return
        
        callback_data = query.data
        
        # Обработка callbacks туду-листа
        if callback_data.startswith("todo_nav_"):
            await handle_todo_navigation(update, context)
        elif callback_data.startswith("todo_date_"):
            await handle_todo_date_callback(update, context)
        elif callback_data.startswith("todo_complete_"):
            await handle_mark_todo_completed(update, context)
        elif callback_data.startswith("todo_refresh_"):
            # Извлечь дату из callback_data и вызвать todo_command
            date_str = callback_data.replace("todo_refresh_", "")
            from datetime import datetime
            try:
                target_date = datetime.fromisoformat(date_str).date()
                # Создаем временный context.args для передачи даты
                context.args = [target_date.strftime("%d.%m.%Y")]
                await todo_command(update, context)
            except ValueError:
                await query.answer("❌ Некорректная дата", show_alert=True)
        else:
            # Передаем обработку общему обработчику
            await handle_callback_query(update, context)
    
    application.add_handler(CallbackQueryHandler(handle_todo_callbacks), group=0)
    
    # Обработка остальных inline-кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query), group=1)
    
    # Обработка кнопок главного меню (ReplyKeyboardMarkup)
    # Должен быть последним, чтобы не перехватывать другие сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_button), group=2)

def main() -> None:
    """Главная функция запуска бота"""
    load_dotenv()
    
    token = Config.BOT_TOKEN
    if not token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения!")
    
    # Инициализация БД
    db = Database()
    db.init_db()
    logger.info("База данных инициализирована")
    
    # Выполнение миграции MVP 0.2
    try:
        from migrations.migrate_0_2 import migrate
        migrate()
        logger.info("Миграция MVP 0.2 выполнена")
    except Exception as e:
        logger.warning(f"Ошибка при выполнении миграции MVP 0.2: {e}")
        import traceback
        logger.warning(traceback.format_exc())
    
    # Выполнение миграции Todo List
    try:
        from migrations.migrate_todo_list import migrate as migrate_todo_list
        migrate_todo_list()
        logger.info("Миграция Todo List выполнена")
    except Exception as e:
        logger.warning(f"Ошибка при выполнении миграции Todo List: {e}")
        import traceback
        logger.warning(traceback.format_exc())
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков
    setup_handlers(application)
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()


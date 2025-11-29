"""
Шаблон главного файла бота
Используйте этот файл как основу для bot.py
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

from config import Config
from database import Database
from handlers.start import start_command, help_command, menu_command
from handlers.tasks import (
    new_task_command, process_task_title, process_task_description,
    list_tasks_command, active_tasks_command, done_tasks_command,
    edit_task_command, process_edit_task, delete_task_command,
    done_task_command
)
from handlers.callbacks import handle_callback_query

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_TITLE, WAITING_DESCRIPTION = range(2)
WAITING_EDIT_FIELD, WAITING_EDIT_VALUE = range(2, 4)

def setup_handlers(application: Application) -> None:
    """Регистрация всех обработчиков команд"""
    
    # Базовые команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Создание задачи (ConversationHandler)
    task_conv = ConversationHandler(
        entry_points=[
            CommandHandler("newtask", new_task_command),
            MessageHandler(filters.Regex("^➕ Создать задачу$"), new_task_command)
        ],
        states={
            WAITING_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_title)
            ],
            WAITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_description),
                CommandHandler("skip", process_task_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(task_conv)
    
    # Просмотр задач
    application.add_handler(CommandHandler("tasks", list_tasks_command))
    application.add_handler(CommandHandler("active", active_tasks_command))
    application.add_handler(CommandHandler("done", done_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои задачи$"), list_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^⏳ Активные$"), active_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^✅ Выполненные$"), done_tasks_command))
    
    # Редактирование задачи
    edit_conv = ConversationHandler(
        entry_points=[
            CommandHandler("edit", edit_task_command),
        ],
        states={
            WAITING_EDIT_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_task)
            ],
            WAITING_EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_task)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(edit_conv)
    
    # Действия с задачами
    application.add_handler(CommandHandler("delete", delete_task_command))
    application.add_handler(CommandHandler("done_task", done_task_command))
    
    # Обработка inline-кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query))

def main() -> None:
    """Главная функция запуска бота"""
    load_dotenv()
    
    token = Config.BOT_TOKEN
    if not token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения!")
    
    # Инициализация БД
    db = Database()
    db.init_db()
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков
    setup_handlers(application)
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()


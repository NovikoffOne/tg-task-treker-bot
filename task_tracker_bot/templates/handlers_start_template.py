"""
Шаблон handlers/start.py
Базовые команды: /start, /help, /menu
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.keyboards import main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Привет! Я бот для управления задачами.\n\n"
        "Я помогу вам:\n"
        "• Создавать задачи\n"
        "• Отслеживать их статус\n"
        "• Редактировать и удалять задачи\n\n"
        "Используйте меню ниже или команду /help для справки."
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📚 Справка по командам:\n\n"
        "/start - Начать работу с ботом\n"
        "/newtask - Создать новую задачу\n"
        "/tasks - Показать все задачи\n"
        "/active - Показать активные задачи\n"
        "/done - Показать завершенные задачи\n"
        "/edit <id> - Редактировать задачу\n"
        "/delete <id> - Удалить задачу\n"
        "/done_task <id> - Отметить задачу выполненной\n"
        "/cancel - Отменить текущую операцию\n"
        "/menu - Показать главное меню\n\n"
        "Также вы можете использовать кнопки меню для быстрого доступа к функциям."
    )
    
    await update.message.reply_text(help_text)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /menu"""
    await update.message.reply_text(
        "🏠 Главное меню",
        reply_markup=main_menu_keyboard()
    )


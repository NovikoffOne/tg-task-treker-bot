"""
Обработчики для кнопок главного меню (ReplyKeyboardMarkup)
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.workspace import workspaces_command
from handlers.board import boards_command
from handlers.project import projects_command
from handlers.statistics import stats_command
from handlers.start import help_command
from handlers.task import mytasks_command, today_command
from handlers.todo_handler import todo_command
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на кнопки главного меню"""
    text = update.message.text
    logger.debug(f"handle_menu_button вызван: text='{text[:50]}...'")
    
    # Проверяем, не ожидаем ли мы ввода названия пространства
    if context.user_data.get('waiting_workspace_name'):
        # Это обрабатывается в workspace.py через handle_workspace_name_input
        return
    
    # Проверяем, не находимся ли мы в ConversationHandler для задач
    # ConversationHandler сам управляет состояниями, поэтому проверяем через активные состояния
    if any(key.startswith('waiting_') for key in context.user_data.keys()):
        # Передаем обработку ConversationHandler
        return
    
    # Обрабатываем только известные кнопки меню
    menu_buttons = [
        "📁 Пространства", "📋 Доски", "📊 Проекты", 
        "📝 Задачи", "👤 Мои задачи", "📅 Сегодня",
        "📅 Туду-лист", "📈 Статистика", "⚙️ Настройки", "❓ Помощь"
    ]
    
    if text not in menu_buttons:
        # Не кнопка меню - игнорируем, передаем обработку дальше
        logger.debug(f"handle_menu_button: текст не является кнопкой меню, передаем дальше: '{text[:50]}...'")
        return
    
    if text == "📁 Пространства":
        await workspaces_command(update, context)
    elif text == "📋 Доски":
        await boards_command(update, context)
    elif text == "📊 Проекты":
        await projects_command(update, context)
    elif text == "📝 Задачи":
        await update.message.reply_text(
            "📝 <b>Задачи</b>\n\n"
            "Используйте команды:\n"
            "• <code>/newtask</code> - создать задачу\n"
            "• <code>/task &lt;id&gt;</code> - показать задачу\n"
            "• <code>/boards</code> - просмотреть доски с задачами",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard()
        )
    elif text == "👤 Мои задачи":
        await mytasks_command(update, context)
    elif text == "📅 Сегодня":
        await today_command(update, context)
    elif text == "📅 Туду-лист":
        await todo_command(update, context)
    elif text == "📈 Статистика":
        await stats_command(update, context)
    elif text == "⚙️ Настройки":
        await update.message.reply_text(
            "⚙️ <b>Настройки</b>\n\n"
            "Настройки бота:\n"
            "• Используйте команды для управления\n"
            "• Все изменения сохраняются автоматически\n\n"
            "Для справки используйте <code>/help</code>",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard()
        )
    elif text == "❓ Помощь":
        await help_command(update, context)


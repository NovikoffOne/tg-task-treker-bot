"""
Callbacks для навигации
"""
from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import main_menu_keyboard

async def handle_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка навигационных callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_menu":
        user_name = query.from_user.first_name or "Пользователь"
        await query.edit_message_text(
            f"🏠 <b>Главное меню</b>\n\n"
            f"Привет, {user_name}! Выберите действие:",
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )
    elif data == "back_to_tasks":
        await query.edit_message_text(
            "📋 <b>Список задач</b>\n\n"
            "Используйте команды:\n"
            "• <code>/boards</code> - список досок\n"
            "• <code>/board &lt;название&gt;</code> - показать доску\n"
            "• <code>/task &lt;id&gt;</code> - показать задачу",
            parse_mode='HTML'
        )


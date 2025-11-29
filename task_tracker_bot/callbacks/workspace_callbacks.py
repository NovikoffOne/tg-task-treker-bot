"""
Callbacks для работы с пространствами
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.workspace_repository import WorkspaceRepository
from services.workspace_service import WorkspaceService
from utils.formatters import format_workspace_list
from utils.keyboards import workspace_keyboard, main_menu_keyboard

db = Database()
workspace_repo = WorkspaceRepository(db)
workspace_service = WorkspaceService(workspace_repo)

async def handle_workspace_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка callback для пространств"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "new_workspace":
        # Устанавливаем флаг для обработки следующего сообщения
        context.user_data['waiting_workspace_name'] = True
        await query.message.reply_text(
            "📁 <b>Создание пространства</b>\n\n"
            "Введите название пространства:\n\n"
            "Или отправьте <code>/cancel</code> для отмены",
            parse_mode='HTML'
        )
    elif data.startswith("select_workspace_"):
        workspace_id = int(data.split("_")[2])
        workspace = workspace_service.get_workspace(workspace_id, user_id)
        if workspace:
            await query.edit_message_text(
                f"📁 <b>Пространство: {workspace.name}</b>\n\n"
                f"📅 Создано: {workspace.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Используйте команды:\n"
                f"• <code>/boards</code> - список досок\n"
                f"• <code>/newboard &lt;название&gt;</code> - создать доску\n"
                f"• <code>/projects</code> - список проектов",
                parse_mode='HTML',
                reply_markup=main_menu_keyboard()
            )
    elif data == "workspaces_more":
        await query.answer("Показываем первые 10 пространств. Используйте команду /workspaces для полного списка")


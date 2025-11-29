"""
Handlers для работы с Workspace
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from repositories.workspace_repository import WorkspaceRepository
from services.workspace_service import WorkspaceService
from utils.formatters import format_workspace_list
from utils.keyboards import workspace_keyboard, main_menu_keyboard

# Инициализация
db = Database()
workspace_repo = WorkspaceRepository(db)
workspace_service = WorkspaceService(workspace_repo)

# Состояния для ConversationHandler
WAITING_WORKSPACE_NAME = 1

async def workspaces_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список пространств с улучшенным UI"""
    user_id = update.effective_user.id
    
    # Проверяем, не ожидаем ли мы ввода названия пространства
    if context.user_data.get('waiting_workspace_name'):
        await process_workspace_name(update, context)
        return
    
    try:
        workspaces = workspace_service.list_workspaces(user_id)
        text = format_workspace_list(workspaces)
        await update.message.reply_text(
            text,
            reply_markup=workspace_keyboard(workspaces),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def newworkspace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начать создание пространства (интерактивный режим)"""
    # Если команда вызвана с аргументами (старый способ)
    if context.args:
        user_id = update.effective_user.id
        name = " ".join(context.args)
        success, workspace_id, error = workspace_service.create_workspace(user_id, name)
        if success:
            await update.message.reply_text(
                f"✅ <b>Пространство '{name}' создано!</b>",
                parse_mode='HTML',
                reply_markup=main_menu_keyboard()
            )
        else:
            await update.message.reply_text(f"❌ {error}")
        return ConversationHandler.END
    
    # Интерактивный режим
    await update.message.reply_text(
        "📁 <b>Создание пространства</b>\n\n"
        "Введите название пространства:\n\n"
        "Или отправьте <code>/cancel</code> для отмены",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )
    return WAITING_WORKSPACE_NAME

async def process_workspace_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка названия пространства"""
    user_id = update.effective_user.id
    
    # Проверяем команду отмены
    if update.message.text and update.message.text.strip().lower() == '/cancel':
        context.user_data.pop('waiting_workspace_name', None)
        await update.message.reply_text("❌ Создание пространства отменено", reply_markup=main_menu_keyboard())
        return ConversationHandler.END
    
    name = update.message.text.strip() if update.message.text else ""
    
    if not name:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз:")
        return WAITING_WORKSPACE_NAME
    
    success, workspace_id, error = workspace_service.create_workspace(user_id, name)
    if success:
        # Убираем флаг
        context.user_data.pop('waiting_workspace_name', None)
        workspaces = workspace_service.list_workspaces(user_id)
        await update.message.reply_text(
            f"✅ <b>Пространство '{name}' создано!</b>\n\n"
            f"{format_workspace_list(workspaces)}",
            parse_mode='HTML',
            reply_markup=workspace_keyboard(workspaces)
        )
    else:
        await update.message.reply_text(
            f"❌ {error}\n\nПопробуйте другое название:",
            parse_mode='HTML'
        )
        return WAITING_WORKSPACE_NAME
    
    return ConversationHandler.END

async def delworkspace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить пространство"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название: /delworkspace <название>")
        return
    
    user_id = update.effective_user.id
    name = " ".join(context.args)
    
    workspace = workspace_service.get_workspace_by_name(user_id, name)
    if not workspace:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    success, error = workspace_service.delete_workspace(workspace.id, user_id)
    if success:
        await update.message.reply_text(f"✅ Пространство '{name}' удалено")
    else:
        await update.message.reply_text(f"❌ {error}")

async def renameworkspace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Переименовать пространство"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите старое и новое название: /renameworkspace <старое> <новое>")
        return
    
    user_id = update.effective_user.id
    all_args_text = " ".join(context.args)
    
    # Получаем список пространств пользователя
    workspaces = workspace_service.list_workspaces(user_id)
    
    # Ищем старое имя среди существующих пространств
    # Пробуем найти самое длинное совпадение
    old_name = None
    new_name = None
    
    # Сортируем пространства по длине имени (от длинного к короткому)
    # чтобы сначала проверять более длинные имена
    sorted_workspaces = sorted(workspaces, key=lambda ws: len(ws.name), reverse=True)
    
    for ws in sorted_workspaces:
        if all_args_text.startswith(ws.name):
            # Нашли пространство, имя которого совпадает с началом аргументов
            old_name = ws.name
            # Новое имя - все что после старого имени
            new_name = all_args_text[len(old_name):].strip()
            break
    
    # Если не нашли точное совпадение, используем первый аргумент как старое имя
    if not old_name:
        old_name = context.args[0]
        new_name = " ".join(context.args[1:])
    
    workspace = workspace_service.get_workspace_by_name(user_id, old_name)
    if not workspace:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    success, error = workspace_service.rename_workspace(workspace.id, user_id, new_name)
    if success:
        await update.message.reply_text(f"✅ Пространство переименовано: '{old_name}' → '{new_name}'")
    else:
        await update.message.reply_text(f"❌ {error}")


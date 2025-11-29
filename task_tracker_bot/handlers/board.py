"""
Handlers для работы с Board и Column
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.task_repository import TaskRepository
from services.board_service import BoardService
from services.task_service import TaskService
from utils.formatters import format_board_list, format_column_list, format_board_view, format_task
from utils.keyboards import board_keyboard, task_card_keyboard
from utils.board_visualizer import BoardVisualizer

# Инициализация
db = Database()
board_repo = BoardRepository(db)
column_repo = ColumnRepository(db)
workspace_repo = WorkspaceRepository(db)
task_repo = TaskRepository(db)
board_service = BoardService(board_repo, column_repo)
task_service = TaskService(task_repo, column_repo)
board_visualizer = BoardVisualizer(board_service)

async def boards_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список досок с улучшенным UI"""
    user_id = update.effective_user.id
    
    # Получить текущее пространство (пока берем первое)
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text(
            "❌ <b>У вас нет пространств</b>\n\n"
            "Создайте пространство:\n"
            "<code>/newworkspace &lt;название&gt;</code>",
            parse_mode='HTML'
        )
        return
    
    workspace_id = workspaces[0].id
    
    try:
        boards = board_service.list_boards(workspace_id)
        text = format_board_list(boards, workspace_id)
        from utils.keyboards import boards_keyboard
        await update.message.reply_text(
            text,
            reply_markup=boards_keyboard(boards),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def newboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать доску"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название: /newboard <название>")
        return
    
    user_id = update.effective_user.id
    name = " ".join(context.args)
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ У вас нет пространств. Создайте пространство: /newworkspace <название>")
        return
    
    workspace_id = workspaces[0].id
    
    success, board_id, error = board_service.create_board(workspace_id, name)
    if success:
        await update.message.reply_text(f"✅ Доска '{name}' создана с дефолтными колонками!")
    else:
        await update.message.reply_text(f"❌ {error}")

async def delboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить доску"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название: /delboard <название>")
        return
    
    user_id = update.effective_user.id
    name = " ".join(context.args)
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    board = board_service.get_board_by_name(workspace_id, name)
    if not board:
        await update.message.reply_text("❌ Доска не найдена")
        return
    
    success, error = board_service.delete_board(board.id)
    if success:
        await update.message.reply_text(f"✅ Доска '{name}' удалена")
    else:
        await update.message.reply_text(f"❌ {error}")

async def board_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать доску"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название: /board <название>")
        return
    
    user_id = update.effective_user.id
    name = " ".join(context.args)
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    board = board_service.get_board_by_name(workspace_id, name)
    if not board:
        await update.message.reply_text("❌ Доска не найдена")
        return
    
    try:
        text = format_board_view(board, board_service)
        await update.message.reply_text(
            text,
            reply_markup=board_keyboard(board.id),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def columns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать колонки доски"""
    if not context.args:
        await update.message.reply_text("❌ Укажите доску: /columns <доска>")
        return
    
    user_id = update.effective_user.id
    board_name = " ".join(context.args)
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    board = board_service.get_board_by_name(workspace_id, board_name)
    if not board:
        await update.message.reply_text("❌ Доска не найдена")
        return
    
    try:
        columns = board_service.list_columns(board.id)
        text = format_column_list(columns, board_name)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def addcolumn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Добавить колонку"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите доску и название: /addcolumn <доска> <название>")
        return
    
    user_id = update.effective_user.id
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    # Парсим аргументы с учетом кавычек
    from utils.validators import parse_quoted_args
    args = parse_quoted_args(context.args)
    
    if len(args) < 2:
        await update.message.reply_text("❌ Укажите доску и название: /addcolumn <доска> <название>")
        return
    
    # Последний аргумент - название колонки, все остальные - название доски
    column_name = args[-1]
    board_name = " ".join(args[:-1])
    
    board = board_service.get_board_by_name(workspace_id, board_name)
    if not board:
        await update.message.reply_text(f"❌ Доска '{board_name}' не найдена")
        return
    
    success, column_id, error = board_service.create_column(board.id, column_name)
    if success:
        await update.message.reply_text(f"✅ Колонка '{column_name}' добавлена в доску '{board_name}'")
    else:
        await update.message.reply_text(f"❌ {error}")

async def delcolumn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить колонку"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите доску и колонку: /delcolumn <доска> <колонка>")
        return
    
    user_id = update.effective_user.id
    board_name = context.args[0]
    column_name = " ".join(context.args[1:])
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    board = board_service.get_board_by_name(workspace_id, board_name)
    if not board:
        await update.message.reply_text("❌ Доска не найдена")
        return
    
    column = column_repo.get_by_name(board.id, column_name)
    if not column:
        await update.message.reply_text("❌ Колонка не найдена")
        return
    
    success, error = board_service.delete_column(column.id)
    if success:
        await update.message.reply_text(f"✅ Колонка '{column_name}' удалена")
    else:
        await update.message.reply_text(f"❌ {error}")

async def boardlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать доску в виде списка задач по колонкам"""
    if not context.args:
        await update.message.reply_text("❌ Укажите название: /boardlist <название>")
        return
    
    user_id = update.effective_user.id
    name = " ".join(context.args)
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ Пространство не найдено")
        return
    
    workspace_id = workspaces[0].id
    
    board = board_service.get_board_by_name(workspace_id, name)
    if not board:
        await update.message.reply_text("❌ Доска не найдена")
        return
    
    try:
        text = board_visualizer.visualize_board_list(board)
        await update.message.reply_text(text, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def view_task_from_board(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int, board_id: int) -> None:
    """Показать полную информацию о задаче из доски"""
    task = task_service.get_task(task_id)
    if not task:
        await update.callback_query.answer("❌ Задача не найдена", show_alert=True)
        return
    
    text = format_task(task, column_repo, board_repo)
    await update.callback_query.edit_message_text(
        text,
        reply_markup=task_card_keyboard(task_id, board_id),
        parse_mode='HTML'
    )


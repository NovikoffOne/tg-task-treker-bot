"""
Callbacks для работы с досками
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.task_repository import TaskRepository
from services.board_service import BoardService
from services.task_service import TaskService
from repositories.column_repository import ColumnRepository
from utils.formatters import format_board_view, format_board_list, format_task
from utils.keyboards import board_keyboard, columns_keyboard, main_menu_keyboard, task_card_keyboard

db = Database()
board_repo = BoardRepository(db)
column_repo = ColumnRepository(db)
workspace_repo = WorkspaceRepository(db)
task_repo = TaskRepository(db)
board_service = BoardService(board_repo, column_repo)
task_service = TaskService(task_repo, column_repo)

# Для использования в других функциях
def get_board_service():
    return board_service

async def handle_board_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка callback для досок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("select_board_"):
        board_id = int(data.split("_")[2])
        board = board_service.get_board(board_id)
        if board:
            try:
                text = format_board_view(board, board_service)
                await query.edit_message_text(
                    text,
                    reply_markup=board_keyboard(board_id),
                    parse_mode='HTML'
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка: {str(e)}")
    
    elif data.startswith("new_task_board_"):
        board_id = int(data.split("_")[3])
        await query.edit_message_text(
            "📝 <b>Создание задачи</b>\n\n"
            "Отправьте команду:\n"
            "<code>/newtask</code>\n\n"
            "Или используйте интерактивный режим создания.",
            parse_mode='HTML'
        )
    
    elif data.startswith("stats_board_"):
        board_id = int(data.split("_")[2])
        await query.answer("Статистика доски. Используйте команду /statsboard <название>")
    
    elif data.startswith("columns_board_"):
        board_id = int(data.split("_")[2])
        columns = board_service.list_columns(board_id)
        await query.edit_message_text(
            f"📌 <b>Колонки доски:</b>\n\n" +
            "\n".join([f"{i+1}. {col.name}" for i, col in enumerate(columns)]),
            parse_mode='HTML',
            reply_markup=columns_keyboard(columns, board_id)
        )
    
    elif data.startswith("refresh_board_"):
        board_id = int(data.split("_")[2])
        board = board_service.get_board(board_id)
        if board:
            text = format_board_view(board, board_service)
            await query.edit_message_text(
                text,
                reply_markup=board_keyboard(board_id),
                parse_mode='HTML'
            )
    
    elif data == "new_board":
        await query.edit_message_text(
            "📋 <b>Создание доски</b>\n\n"
            "Отправьте команду:\n"
            "<code>/newboard &lt;название&gt;</code>\n\n"
            "Например: <code>/newboard Дизайн</code>",
            parse_mode='HTML'
        )
    
    elif data == "boards_stats":
        await query.answer("Используйте команду /stats для общей статистики")
    
    elif data.startswith("view_task_from_board_"):
        # Формат: view_task_from_board_<task_id>_<board_id>
        parts = data.split("_")
        if len(parts) >= 5:
            task_id = int(parts[3])
            board_id = int(parts[4])
            task = task_service.get_task(task_id)
            if task:
                text = format_task(task, column_repo, board_repo)
                await query.edit_message_text(
                    text,
                    reply_markup=task_card_keyboard(task_id, board_id),
                    parse_mode='HTML'
                )
            else:
                await query.answer("❌ Задача не найдена", show_alert=True)


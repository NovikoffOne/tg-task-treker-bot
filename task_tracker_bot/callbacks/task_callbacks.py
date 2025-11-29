"""
Callbacks для работы с задачами
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.task_repository import TaskRepository
from services.task_service import TaskService
from repositories.column_repository import ColumnRepository
from utils.formatters import format_task
from utils.keyboards import task_actions_keyboard, priority_keyboard, confirm_delete_keyboard

# Инициализация
db = Database()
task_repo = TaskRepository(db)
column_repo = ColumnRepository(db)
from repositories.board_repository import BoardRepository
from repositories.board_dependency_repository import BoardDependencyRepository
from repositories.project_repository import ProjectRepository
from repositories.task_assignee_repository import TaskAssigneeRepository
from repositories.project_member_repository import ProjectMemberRepository
from services.dependency_service import DependencyService
from services.assignment_service import AssignmentService

board_repo = BoardRepository(db)
dependency_repo = BoardDependencyRepository(db)
project_repo = ProjectRepository(db)
assignee_repo = TaskAssigneeRepository(db)
member_repo = ProjectMemberRepository(db)

dependency_service = DependencyService(
    dependency_repo, task_repo, project_repo, column_repo, board_repo
)
assignment_service = AssignmentService(
    assignee_repo, member_repo, task_repo, project_repo, column_repo, board_repo
)
task_service = TaskService(task_repo, column_repo, dependency_service, assignment_service)

async def handle_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка callback для задач"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("edit_task_"):
        task_id = int(data.split("_")[2])
        await handle_edit_task(query, task_id)
    elif data.startswith("delete_task_"):
        task_id = int(data.split("_")[2])
        await handle_delete_task(query, task_id)
    elif data.startswith("priority_task_"):
        task_id = int(data.split("_")[2])
        await handle_priority_task(query, task_id)
    elif data.startswith("set_priority_"):
        parts = data.split("_")
        task_id = int(parts[2])
        priority = int(parts[3])
        await handle_set_priority(query, task_id, priority)
    elif data.startswith("confirm_delete_"):
        task_id = int(data.split("_")[2])
        await handle_confirm_delete(query, task_id)
    elif data.startswith("cancel_delete_"):
        task_id = int(data.split("_")[2])
        task = task_service.get_task(task_id)
        if task:
            from repositories.board_repository import BoardRepository
            board_repo = BoardRepository(db)
            text = format_task(task, column_repo, board_repo)
            await query.edit_message_text(
                f"❌ <b>Удаление отменено</b>\n\n{text}",
                reply_markup=task_actions_keyboard(task_id),
                parse_mode='HTML'
            )
    elif data.startswith("move_task_"):
        task_id = int(data.split("_")[2])
        await handle_move_task(query, task_id)
    elif data.startswith("fields_task_"):
        task_id = int(data.split("_")[2])
        await handle_fields_task(query, task_id)
    elif data.startswith("tags_task_"):
        task_id = int(data.split("_")[2])
        await handle_tags_task(query, task_id)
    elif data.startswith("subtasks_task_"):
        task_id = int(data.split("_")[2])
        await handle_subtasks_task(query, task_id)
    elif data.startswith("task_"):
        task_id = int(data.split("_")[1])
        await handle_show_task(query, task_id)
    elif data.startswith("move_to_column_"):
        parts = data.split("_")
        task_id = int(parts[3])
        column_id = int(parts[4])
        await handle_move_to_column(query, task_id, column_id)

async def handle_edit_task(query, task_id: int):
    """Обработка редактирования задачи"""
    task = task_service.get_task(task_id)
    if not task:
        await query.edit_message_text("❌ Задача не найдена")
        return
    
    from repositories.board_repository import BoardRepository
    board_repo = BoardRepository(db)
    await query.edit_message_text(
        f"✏️ <b>Редактирование задачи:</b>\n\n{format_task(task, column_repo, board_repo)}\n\n"
        f"<b>Используйте команды:</b>\n"
        f"• <code>/movetask {task_id} &lt;колонка&gt;</code> - переместить\n"
        f"• <code>/priority {task_id} &lt;0-3&gt;</code> - установить приоритет\n\n"
        f"Или используйте кнопки ниже ⬇️",
        reply_markup=task_actions_keyboard(task_id),
        parse_mode='HTML'
    )

async def handle_delete_task(query, task_id: int):
    """Обработка удаления задачи (показать подтверждение)"""
    task = task_service.get_task(task_id)
    if not task:
        await query.edit_message_text("❌ Задача не найдена")
        return
    
    from repositories.board_repository import BoardRepository
    board_repo = BoardRepository(db)
    await query.edit_message_text(
        f"⚠️ <b>Вы уверены, что хотите удалить задачу?</b>\n\n{format_task(task, column_repo, board_repo)}",
        reply_markup=confirm_delete_keyboard(task_id),
        parse_mode='HTML'
    )

async def handle_confirm_delete(query, task_id: int):
    """Подтверждение удаления задачи"""
    success, error = task_service.delete_task(task_id)
    if success:
        await query.edit_message_text("✅ <b>Задача удалена</b>", parse_mode='HTML')
    else:
        await query.edit_message_text(f"❌ {error}")

async def handle_priority_task(query, task_id: int):
    """Обработка выбора приоритета"""
    task = task_service.get_task(task_id)
    if not task:
        await query.edit_message_text("❌ Задача не найдена")
        return
    
    from repositories.board_repository import BoardRepository
    board_repo = BoardRepository(db)
    await query.edit_message_text(
        f"🔴 <b>Выберите приоритет для задачи:</b>\n\n{format_task(task, column_repo, board_repo)}",
        reply_markup=priority_keyboard(task_id),
        parse_mode='HTML'
    )

async def handle_set_priority(query, task_id: int, priority: int):
    """Установка приоритета"""
    success, error = task_service.update_task(task_id, priority=priority)
    if success:
        priority_names = {0: 'Низкий', 1: 'Средний', 2: 'Высокий', 3: 'Критический'}
        task = task_service.get_task(task_id)
        from repositories.board_repository import BoardRepository
        board_repo = BoardRepository(db)
        await query.edit_message_text(
            f"✅ <b>Приоритет установлен: {priority_names[priority]}</b>\n\n{format_task(task, column_repo, board_repo)}",
            reply_markup=task_actions_keyboard(task_id),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(f"❌ {error}")

async def handle_move_task(query, task_id: int):
    """Обработка перемещения задачи"""
    task = task_service.get_task(task_id)
    if not task:
        await query.edit_message_text("❌ Задача не найдена")
        return
    
    column = column_repo.get_by_id(task.column_id)
    if not column:
        await query.edit_message_text("❌ Колонка не найдена")
        return
    
    from repositories.board_repository import BoardRepository
    board_repo = BoardRepository(db)
    from callbacks.board_callbacks import get_board_service
    board_service = get_board_service()
    board = board_repo.get_by_id(column.board_id)
    if not board:
        await query.edit_message_text("❌ Доска не найдена")
        return
    
    columns = board_service.list_columns(board.id)
    from utils.keyboards import move_task_column_keyboard
    await query.edit_message_text(
        f"➡️ <b>Переместить задачу:</b>\n\n"
        f"{format_task(task, column_repo, board_repo)}\n\n"
        f"<b>Выберите колонку:</b>",
        reply_markup=move_task_column_keyboard(columns, task_id),
        parse_mode='HTML'
    )

async def handle_fields_task(query, task_id: int):
    """Обработка полей задачи"""
    await query.edit_message_text(
        f"📎 <b>Поля задачи #{task_id}</b>\n\n"
        f"Используйте команду:\n"
        f"<code>/addfield {task_id} &lt;поле&gt; &lt;значение&gt;</code>\n\n"
        f"Например: <code>/addfield {task_id} Figma https://figma.com/...</code>",
        parse_mode='HTML'
    )

async def handle_tags_task(query, task_id: int):
    """Обработка меток задачи"""
    await query.edit_message_text(
        f"🏷 <b>Метки задачи #{task_id}</b>\n\n"
        f"Используйте команду:\n"
        f"<code>/addtag {task_id} &lt;метка&gt;</code>",
        parse_mode='HTML'
    )

async def handle_subtasks_task(query, task_id: int):
    """Обработка подзадач"""
    subtasks = task_service.get_subtasks(task_id)
    if subtasks:
        text = f"<b>📋 Подзадачи:</b>\n\n"
        for subtask in subtasks:
            text += f"• {subtask.priority_emoji} {subtask.title}\n"
    else:
        text = "📭 Подзадач пока нет\n\nИспользуйте команду:\n<code>/newsubtask &lt;parent_id&gt; &lt;название&gt;</code>"
    
    await query.edit_message_text(text, parse_mode='HTML')

async def handle_show_task(query, task_id: int):
    """Показать задачу"""
    task = task_service.get_task(task_id)
    if not task:
        await query.edit_message_text("❌ Задача не найдена")
        return
    
    from repositories.board_repository import BoardRepository
    board_repo = BoardRepository(db)
    text = format_task(task, column_repo, board_repo)
    await query.edit_message_text(
        text,
        reply_markup=task_actions_keyboard(task_id),
        parse_mode='HTML'
    )

async def handle_move_to_column(query, task_id: int, column_id: int):
    """Переместить задачу в колонку"""
    user_id = query.from_user.id
    success, error = task_service.move_task(task_id, column_id, user_id)
    if success:
        task = task_service.get_task(task_id)
        column = column_repo.get_by_id(column_id)
        from repositories.board_repository import BoardRepository
        board_repo = BoardRepository(db)
        text = format_task(task, column_repo, board_repo)
        await query.edit_message_text(
            f"✅ <b>Задача перемещена в колонку '{column.name if column else 'Неизвестно'}'</b>\n\n{text}",
            reply_markup=task_actions_keyboard(task_id),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(f"❌ {error}")


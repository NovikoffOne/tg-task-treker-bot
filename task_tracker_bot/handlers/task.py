"""
Handlers для работы с Task
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from database import Database
from repositories.task_repository import TaskRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.board_dependency_repository import BoardDependencyRepository
from repositories.project_repository import ProjectRepository
from services.task_service import TaskService
from services.dependency_service import DependencyService
from services.assignment_service import AssignmentService
from repositories.task_assignee_repository import TaskAssigneeRepository
from repositories.project_member_repository import ProjectMemberRepository
from utils.formatters import format_task
from utils.keyboards import task_actions_keyboard

# Инициализация
db = Database()
task_repo = TaskRepository(db)
column_repo = ColumnRepository(db)
board_repo = BoardRepository(db)
workspace_repo = WorkspaceRepository(db)
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

# Состояния для ConversationHandler
WAITING_TASK_BOARD, WAITING_TASK_COLUMN, WAITING_TASK_TITLE, WAITING_TASK_DESCRIPTION = range(4)

async def newtask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало создания задачи"""
    user_id = update.effective_user.id
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text("❌ У вас нет пространств. Создайте пространство: /newworkspace <название>")
        return ConversationHandler.END
    
    workspace_id = workspaces[0].id
    boards = board_repo.get_all_by_workspace(workspace_id)
    
    if not boards:
        await update.message.reply_text("❌ У вас нет досок. Создайте доску: /newboard <название>")
        return ConversationHandler.END
    
    # Сохранить список досок
    context.user_data['boards'] = boards
    context.user_data['workspace_id'] = workspace_id
    
    # Показать список досок
    board_list = "\n".join([f"{i+1}. {b.name}" for i, b in enumerate(boards)])
    await update.message.reply_text(f"Выберите доску (введите номер):\n\n{board_list}")
    
    return WAITING_TASK_BOARD

async def process_task_board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора доски"""
    try:
        board_num = int(update.message.text) - 1
        boards = context.user_data.get('boards', [])
        
        if board_num < 0 or board_num >= len(boards):
            await update.message.reply_text("❌ Неверный номер доски. Попробуйте снова:")
            return WAITING_TASK_BOARD
        
        board = boards[board_num]
        context.user_data['board_id'] = board.id
        
        # Получить колонки доски
        columns = column_repo.get_all_by_board(board.id)
        context.user_data['columns'] = columns
        
        column_list = "\n".join([f"{i+1}. {c.name}" for i, c in enumerate(columns)])
        await update.message.reply_text(f"Выберите колонку (введите номер):\n\n{column_list}")
        
        return WAITING_TASK_COLUMN
    except ValueError:
        await update.message.reply_text("❌ Введите число. Попробуйте снова:")
        return WAITING_TASK_BOARD

async def process_task_column(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора колонки"""
    try:
        column_num = int(update.message.text) - 1
        columns = context.user_data.get('columns', [])
        
        if column_num < 0 or column_num >= len(columns):
            await update.message.reply_text("❌ Неверный номер колонки. Попробуйте снова:")
            return WAITING_TASK_COLUMN
        
        column = columns[column_num]
        context.user_data['column_id'] = column.id
        
        await update.message.reply_text("Введите название задачи:")
        return WAITING_TASK_TITLE
    except ValueError:
        await update.message.reply_text("❌ Введите число. Попробуйте снова:")
        return WAITING_TASK_COLUMN

async def process_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка названия задачи"""
    title = update.message.text.strip()
    
    if len(title) < 2:
        await update.message.reply_text("❌ Название задачи должно быть минимум 2 символа. Попробуйте снова:")
        return WAITING_TASK_TITLE
    
    context.user_data['task_title'] = title
    await update.message.reply_text("Введите описание задачи (или отправьте /skip для пропуска):")
    return WAITING_TASK_DESCRIPTION

async def process_task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка описания задачи"""
    column_id = context.user_data.get('column_id')
    title = context.user_data.get('task_title')
    
    if update.message.text == '/skip':
        description = None
    else:
        description = update.message.text.strip()
        if len(description) > 2000:
            await update.message.reply_text("❌ Описание слишком длинное (максимум 2000 символов). Попробуйте снова:")
            return WAITING_TASK_DESCRIPTION
    
    # Создать задачу
    success, task_id, error = task_service.create_task(column_id, title, description)
    
    if success:
        task = task_service.get_task(task_id)
        await update.message.reply_text(
            f"✅ <b>Задача создана!</b>\n\n{format_task(task, column_repo, board_repo)}",
            reply_markup=task_actions_keyboard(task_id),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(f"❌ {error}")
    
    # Очистка данных
    context.user_data.clear()
    return ConversationHandler.END

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать задачу"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID задачи: /task <id>")
        return
    
    try:
        task_id = int(context.args[0])
        task = task_service.get_task(task_id)
        
        if not task:
            await update.message.reply_text("❌ Задача не найдена")
            return
        
        text = format_task(task, column_repo, board_repo)
        await update.message.reply_text(
            text,
            reply_markup=task_actions_keyboard(task_id),
            parse_mode='HTML'
        )
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def movetask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Переместить задачу"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите ID задачи и колонку: /movetask <id> <колонка>")
        return
    
    try:
        task_id = int(context.args[0])
        column_name = " ".join(context.args[1:])
        
        task = task_service.get_task(task_id)
        if not task:
            await update.message.reply_text("❌ Задача не найдена")
            return
        
        # Получить текущую колонку задачи
        current_column = column_repo.get_by_id(task.column_id)
        if not current_column:
            await update.message.reply_text("❌ Колонка задачи не найдена")
            return
        
        # Найти колонку по имени в той же доске
        column = column_repo.get_by_name(current_column.board_id, column_name)
        
        if not column:
            await update.message.reply_text("❌ Колонка не найдена")
            return
        
        user_id = update.effective_user.id
        success, error = task_service.move_task(task_id, column.id, user_id)
        if success:
            await update.message.reply_text(f"✅ Задача перемещена в колонку '{column_name}'")
        else:
            await update.message.reply_text(f"❌ {error}")
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def priority_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установить приоритет задачи"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Укажите ID задачи и приоритет: /priority <id> <0-3>")
        return
    
    try:
        task_id = int(context.args[0])
        priority = int(context.args[1])
        
        if priority < 0 or priority > 3:
            await update.message.reply_text("❌ Приоритет должен быть от 0 до 3 (0=низкий, 1=средний, 2=высокий, 3=критический)")
            return
        
        success, error = task_service.update_task(task_id, priority=priority)
        if success:
            priority_names = {0: 'Низкий', 1: 'Средний', 2: 'Высокий', 3: 'Критический'}
            await update.message.reply_text(f"✅ Приоритет установлен: {priority_names[priority]}")
        else:
            await update.message.reply_text(f"❌ {error}")
    except ValueError:
        await update.message.reply_text("❌ ID и приоритет должны быть числами")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def deltask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить задачу"""
    if not context.args:
        await update.message.reply_text("❌ Укажите ID задачи: /deltask <id>")
        return
    
    try:
        task_id = int(context.args[0])
        success, error = task_service.delete_task(task_id)
        if success:
            await update.message.reply_text("✅ Задача удалена")
        else:
            await update.message.reply_text(f"❌ {error}")
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать мои задачи (где пользователь является ответственным)"""
    user_id = update.effective_user.id
    
    tasks = assignment_service.get_user_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text(
            "📋 <b>Мои задачи</b>\n\n"
            "У вас нет назначенных задач.",
            parse_mode='HTML'
        )
        return
    
    text = f"📋 <b>Мои задачи ({len(tasks)}):</b>\n\n"
    for task in tasks:
        column = column_repo.get_by_id(task.column_id)
        board = board_repo.get_by_id(column.board_id) if column else None
        text += f"{task.priority_emoji} <b>#{task.id}</b> {task.title}\n"
        if board and column:
            text += f"   📋 {board.name} → {column.name}\n"
        if task.deadline:
            deadline_str = task.deadline.strftime("%d.%m.%Y") if isinstance(task.deadline, datetime) else str(task.deadline)
            text += f"   ⏰ Дедлайн: {deadline_str}\n"
        text += "\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать задачи с дедлайном на сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = task_service.get_tasks_by_deadline(today)
    
    if not tasks:
        await update.message.reply_text(
            "📅 <b>Задачи на сегодня</b>\n\n"
            "Нет задач с дедлайном на сегодня.",
            parse_mode='HTML'
        )
        return
    
    text = f"📅 <b>Задачи на сегодня ({len(tasks)}):</b>\n\n"
    for task in tasks:
        column = column_repo.get_by_id(task.column_id)
        board = board_repo.get_by_id(column.board_id) if column else None
        deadline_str = task.deadline.strftime("%d.%m.%Y %H:%M") if isinstance(task.deadline, datetime) else str(task.deadline)
        text += f"{task.priority_emoji} <b>#{task.id}</b> {task.title}\n"
        if board and column:
            text += f"   📋 {board.name} → {column.name}\n"
        text += f"   ⏰ Дедлайн: {deadline_str}\n"
        text += "\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def deadline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Установить дедлайн задачи"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажите ID задачи и дедлайн:\n"
            "<code>/deadline &lt;id&gt; &lt;дата&gt; [время]</code>\n\n"
            "Формат даты: DD.MM.YYYY или DD.MM.YYYY HH:MM\n"
            "Пример: /deadline 123 31.12.2025 18:00",
            parse_mode='HTML'
        )
        return
    
    try:
        task_id = int(context.args[0])
        date_str = context.args[1]
        time_str = context.args[2] if len(context.args) > 2 else None
        
        # Парсинг даты
        try:
            if time_str:
                deadline = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
            else:
                deadline = datetime.strptime(date_str, "%d.%m.%Y")
                # Устанавливаем время на конец дня, если не указано
                deadline = deadline.replace(hour=23, minute=59)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте: DD.MM.YYYY или DD.MM.YYYY HH:MM"
            )
            return
        
        success, error = task_service.set_deadline(task_id, deadline)
        if success:
            deadline_str = deadline.strftime("%d.%m.%Y %H:%M")
            await update.message.reply_text(f"✅ Дедлайн установлен: {deadline_str}")
        else:
            await update.message.reply_text(f"❌ {error}")
    except ValueError:
        await update.message.reply_text("❌ ID задачи должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


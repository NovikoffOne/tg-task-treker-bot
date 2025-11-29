"""
Handlers для работы с зависимостями досок
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.board_dependency_repository import BoardDependencyRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.workspace_repository import WorkspaceRepository
from services.dependency_service import DependencyService
from services.task_service import TaskService
from utils.validators import parse_quoted_args

# Инициализация
db = Database()
dependency_repo = BoardDependencyRepository(db)
board_repo = BoardRepository(db)
column_repo = ColumnRepository(db)
workspace_repo = WorkspaceRepository(db)
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
project_repo = ProjectRepository(db)
task_repo = TaskRepository(db)

dependency_service = DependencyService(
    dependency_repo, task_repo, project_repo, column_repo, board_repo
)

async def dependencies_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список зависимостей"""
    user_id = update.effective_user.id
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text(
            "❌ У вас нет пространств. Создайте пространство: /newworkspace <название>"
        )
        return
    
    workspace_id = workspaces[0].id
    dependencies = dependency_service.list_dependencies(workspace_id)
    
    if not dependencies:
        await update.message.reply_text(
            "📋 <b>Зависимости досок</b>\n\n"
            "У вас пока нет зависимостей.\n\n"
            "Создайте зависимость:\n"
            "<code>/newdependency</code>",
            parse_mode='HTML'
        )
        return
    
    text = "📋 <b>Зависимости досок:</b>\n\n"
    for i, dep in enumerate(dependencies, 1):
        status = "✅" if dep.enabled else "❌"
        text += f"{i}. {status} <b>{dep.name}</b>\n"
        text += f"   От: доска #{dep.source_board_id}, колонка #{dep.source_column_id}\n"
        text += f"   К: доска #{dep.target_board_id}, колонка #{dep.target_column_id}\n"
        text += f"   Действие: {dep.action_type}\n\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def newdependency_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать новую зависимость (упрощенная версия)"""
    user_id = update.effective_user.id
    
    # Получить текущее пространство
    workspaces = workspace_repo.get_all_by_user(user_id)
    if not workspaces:
        await update.message.reply_text(
            "❌ У вас нет пространств. Создайте пространство: /newworkspace <название>"
        )
        return
    
    workspace_id = workspaces[0].id
    
    # Упрощенная версия - требуем все параметры в команде
    # Формат: /newdependency <name> <source_board> <source_column> <target_board> <target_column> <action_type> [template]
    # Парсим аргументы с учетом кавычек
    raw_args = context.args
    args = parse_quoted_args(raw_args)
    
    # Ищем action_type в аргументах (может быть в разных позициях из-за кавычек)
    action_type = None
    action_index = None
    valid_actions = ['create_task', 'move_task']
    
    for i, arg in enumerate(args):
        arg_clean = arg.strip().strip('"').strip("'")
        if arg_clean in valid_actions:
            action_type = arg_clean
            action_index = i
            break
    
    if not action_type:
        await update.message.reply_text(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Не найден тип действия (create_task или move_task)\n\n"
            "Использование:\n"
            "<code>/newdependency &lt;название&gt; &lt;исходная_доска&gt; &lt;исходная_колонка&gt; "
            "&lt;целевая_доска&gt; &lt;целевая_колонка&gt; &lt;действие&gt; [шаблон]</code>\n\n"
            "Примеры:\n"
            "<code>/newdependency \"Подготовка->Дизайн\" Подготовка Готово Дизайн Очередь create_task "
            "\"{project_id} {project_name} Дизайн\"</code>\n\n"
            "<code>/newdependency \"Тест\" Тестирование Реджект Разработка \"Фикс Багов\" move_task</code>\n\n"
            "Действия: create_task, move_task",
            parse_mode='HTML'
        )
        return
    
    # Разделяем аргументы: до action_type и после
    args_before_action = args[:action_index]
    args_after_action = args[action_index + 1:]
    
    if len(args_before_action) < 5:
        await update.message.reply_text(
            "❌ <b>Неверный формат команды</b>\n\n"
            "Недостаточно аргументов перед действием. Ожидается 5 аргументов:\n"
            "1. Название зависимости\n"
            "2. Исходная доска\n"
            "3. Исходная колонка\n"
            "4. Целевая доска\n"
            "5. Целевая колонка\n\n"
            "Использование:\n"
            "<code>/newdependency &lt;название&gt; &lt;исходная_доска&gt; &lt;исходная_колонка&gt; "
            "&lt;целевая_доска&gt; &lt;целевая_колонка&gt; &lt;действие&gt; [шаблон]</code>",
            parse_mode='HTML'
        )
        return
    
    name = args_before_action[0]
    source_board_name = args_before_action[1]
    source_column_name = args_before_action[2]
    target_board_name = args_before_action[3]
    target_column_name = args_before_action[4]
    task_title_template = " ".join(args_after_action) if args_after_action else None
    
    # Убираем кавычки из шаблона, если они есть
    if task_title_template:
        task_title_template = task_title_template.strip()
        if task_title_template.startswith('"') and task_title_template.endswith('"'):
            task_title_template = task_title_template[1:-1]
        elif task_title_template.startswith("'") and task_title_template.endswith("'"):
            task_title_template = task_title_template[1:-1]
    
    # Найти доски и колонки
    source_board = board_repo.get_by_name(workspace_id, source_board_name)
    if not source_board:
        await update.message.reply_text(f"❌ Доска '{source_board_name}' не найдена")
        return
    
    source_column = column_repo.get_by_name(source_board.id, source_column_name)
    if not source_column:
        await update.message.reply_text(
            f"❌ Колонка '{source_column_name}' не найдена на доске '{source_board_name}'"
        )
        return
    
    target_board = board_repo.get_by_name(workspace_id, target_board_name)
    if not target_board:
        await update.message.reply_text(f"❌ Доска '{target_board_name}' не найдена")
        return
    
    target_column = column_repo.get_by_name(target_board.id, target_column_name)
    if not target_column:
        await update.message.reply_text(
            f"❌ Колонка '{target_column_name}' не найдена на доске '{target_board_name}'"
        )
        return
    
    # Создать зависимость
    success, dependency_id, error = dependency_service.create_dependency(
        workspace_id=workspace_id,
        name=name,
        source_board_id=source_board.id,
        source_column_id=source_column.id,
        trigger_type='enter',
        target_board_id=target_board.id,
        target_column_id=target_column.id,
        action_type=action_type,
        task_title_template=task_title_template
    )
    
    if success:
        await update.message.reply_text(
            f"✅ Зависимость '{name}' создана успешно (ID: {dependency_id})"
        )
    else:
        await update.message.reply_text(f"❌ Ошибка при создании зависимости: {error}")

async def deldependency_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить зависимость"""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "❌ Укажите ID зависимости для удаления:\n"
            "<code>/deldependency &lt;id&gt;</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        dependency_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом")
        return
    
    success, error = dependency_service.delete_dependency(dependency_id)
    
    if success:
        await update.message.reply_text(f"✅ Зависимость #{dependency_id} удалена")
    else:
        await update.message.reply_text(f"❌ Ошибка при удалении: {error}")


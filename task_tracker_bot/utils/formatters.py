"""
Утилиты для форматирования сообщений
"""
from datetime import datetime
from typing import List, Optional, Dict
from models.workspace import Workspace
from models.board import Board
from models.column import Column
from models.project import Project
from models.task import Task
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from repositories.task_repository import TaskRepository
from services.board_service import BoardService
from services.project_service import ProjectService

def format_datetime(dt: datetime) -> str:
    """Форматировать datetime в читаемый формат"""
    return dt.strftime("%d.%m.%Y %H:%M")

def format_workspace_list(workspaces: List[Workspace]) -> str:
    """Форматировать список пространств с улучшенным UI"""
    if not workspaces:
        return "📭 <b>У вас пока нет пространств</b>\n\nИспользуйте команду:\n<code>/newworkspace &lt;название&gt;</code>\n\nИли нажмите кнопку ниже ⬇️"
    
    text = "📁 <b>Ваши пространства:</b>\n\n"
    for i, ws in enumerate(workspaces, 1):
        text += f"{i}. <b>🏢 {ws.name}</b>\n"
        text += f"   📅 {format_datetime(ws.created_at)}\n\n"
    
    text += "Выберите пространство или создайте новое ⬇️"
    return text

def format_board_list(boards: List[Board], workspace_id: int) -> str:
    """Форматировать список досок с улучшенным UI"""
    if not boards:
        return "📭 <b>У вас пока нет досок</b>\n\nИспользуйте команду:\n<code>/newboard &lt;название&gt;</code>\n\nИли нажмите кнопку ниже ⬇️"
    
    text = "📋 <b>Доски в пространстве:</b>\n\n"
    for i, board in enumerate(boards, 1):
        text += f"{i}. <b>📋 {board.name}</b>\n"
        text += f"   📍 Позиция: {board.position}\n\n"
    
    text += "Выберите доску или создайте новую ⬇️"
    return text

def format_column_list(columns: List[Column], board_name: str) -> str:
    """Форматировать список колонок"""
    if not columns:
        return f"📭 В доске '{board_name}' нет колонок."
    
    text = f"📌 Колонки доски '{board_name}':\n\n"
    for i, col in enumerate(columns, 1):
        text += f"{i}. {col.name} (позиция: {col.position})\n"
    
    return text.strip()

def format_task(task: Task, column_repo: Optional[ColumnRepository] = None,
                board_repo: Optional[BoardRepository] = None) -> str:
    """Форматировать задачу с улучшенным UI"""
    text = f"<b>📋 Задача #{task.id}</b>\n"
    text += f"<b>{task.title}</b>\n\n"
    
    if task.description:
        text += f"📝 <i>{task.description}</i>\n\n"
    
    # Информация о расположении
    location_info = []
    if column_repo:
        column = column_repo.get_by_id(task.column_id)
        if column:
            location_info.append(f"📌 {column.name}")
            if board_repo:
                board = board_repo.get_by_id(column.board_id)
                if board:
                    location_info.append(f"📊 {board.name}")
    
    if location_info:
        text += " | ".join(location_info) + "\n\n"
    
    # Приоритет и проект
    info_line = []
    info_line.append(f"{task.priority_emoji} {task.priority_name}")
    
    if task.project_id:
        info_line.append(f"📁 {task.project_id}")
    
    text += " | ".join(info_line) + "\n\n"
    
    # Ответственный
    if task.assignee_id:
        text += f"👤 Ответственный: ID {task.assignee_id}\n"
    
    # Даты работы
    if task.started_at:
        started_str = format_datetime(task.started_at) if isinstance(task.started_at, datetime) else str(task.started_at)
        text += f"▶️ Начато: {started_str}\n"
    
    if task.completed_at:
        completed_str = format_datetime(task.completed_at) if isinstance(task.completed_at, datetime) else str(task.completed_at)
        text += f"✅ Завершено: {completed_str}\n"
    
    # Дедлайн
    if task.deadline:
        deadline_str = format_datetime(task.deadline) if isinstance(task.deadline, datetime) else str(task.deadline)
        text += f"⏰ Дедлайн: {deadline_str}\n"
    
    # Даты создания и обновления
    text += f"\n📅 Создано: {format_datetime(task.created_at)}\n"
    text += f"🔄 Обновлено: {format_datetime(task.updated_at)}"
    
    return text

def format_project(project: Project, project_service: ProjectService,
                  task_repo: TaskRepository, column_repo: ColumnRepository,
                  board_repo: BoardRepository) -> str:
    """Форматировать проект с улучшенным UI"""
    text = f"<b>📊 Проект: {project.id}</b>\n"
    text += f"<b>{project.name}</b>\n\n"
    
    # Этап дашборда
    stage_names = {
        'preparation': '🔵 Подготовка',
        'design': '🎨 Дизайн',
        'development': '💻 Разработка',
        'testing': '🧪 Тестирование',
        'submission': '📤 На отправку',
        'moderation': '👀 Модерация',
        'rejected': '❌ Реджект',
        'published': '✅ Опубликовано'
    }
    stage_emoji = stage_names.get(project.dashboard_stage, '⚪ ' + project.dashboard_stage)
    text += f"📈 <b>Этап:</b> {stage_emoji}\n\n"
    
    # Получить задачи проекта
    tasks = task_repo.get_all_by_project(project.id)
    if tasks:
        text += f"<b>📋 Задачи проекта ({len(tasks)}):</b>\n\n"
        for task in tasks:
            column = column_repo.get_by_id(task.column_id)
            column_name = column.name if column else "Неизвестно"
            text += f"  • {task.priority_emoji} {task.title}\n"
            text += f"    📌 {column_name}\n\n"
    else:
        text += "📭 Задач пока нет\n\n"
    
    text += "Используйте кнопки ниже для управления ⬇️"
    return text

def format_project_dashboard(project: Project, project_service: ProjectService,
                            task_repo: TaskRepository, column_repo: ColumnRepository,
                            board_repo: BoardRepository) -> str:
    """Форматировать дашборд проекта"""
    text = f"📊 Дашборд проекта: {project.id} {project.name}\n\n"
    text += f"📈 Текущий этап: {project.dashboard_stage}\n\n"
    
    # Этапы дашборда
    stages = {
        'preparation': 'Подготовка',
        'design': 'Дизайн',
        'development': 'Разработка',
        'testing': 'Тестирование',
        'submission': 'На отправку',
        'moderation': 'Модерация',
        'rejected': 'Реджект',
        'published': 'Опубликовано'
    }
    
    current_stage = project.dashboard_stage
    text += "Этапы:\n"
    for stage_key, stage_name in stages.items():
        if stage_key == current_stage:
            text += f"🔄 {stage_name} ← текущий\n"
        elif stage_key in ['preparation', 'design', 'development']:
            # Проверить, завершен ли этап (задача в колонке "Готово")
            text += f"✅ {stage_name}\n"
        else:
            text += f"⏳ {stage_name}\n"
    
    return text

def format_project_list(projects: List[Project]) -> str:
    """Форматировать список проектов"""
    if not projects:
        return "📭 У вас пока нет проектов.\n\nСоздайте проект: /newproject <id> <название>"
    
    text = "📊 Ваши проекты:\n\n"
    for project in projects:
        text += f"📁 {project.id} {project.name}\n"
        text += f"   Этап: {project.dashboard_stage}\n\n"
    
    return text.strip()

def format_board_view(board: Board, board_service: BoardService) -> str:
    """Форматировать вид доски"""
    from utils.board_visualizer import BoardVisualizer
    from repositories.task_repository import TaskRepository
    from database import Database
    
    db = Database()
    task_repo = TaskRepository(db)
    visualizer = BoardVisualizer(board_service)
    return visualizer.visualize_board(board)

def format_stats(stats: Dict) -> str:
    """Форматировать статистику"""
    text = "📊 Общая статистика\n\n"
    text += f"📋 Досок: {stats.get('boards_count', 0)}\n"
    text += f"📊 Проектов: {stats.get('projects_count', 0)}\n"
    text += f"📝 Всего задач: {stats.get('total_tasks', 0)}\n\n"
    
    tasks_by_status = stats.get('tasks_by_status', {})
    if tasks_by_status:
        text += "Задачи по статусам:\n"
        for status, count in tasks_by_status.items():
            text += f"  • {status}: {count}\n"
    
    return text

def format_project_stats(stats: Dict) -> str:
    """Форматировать статистику проекта"""
    text = f"📊 Статистика проекта: {stats.get('project_name', 'Неизвестно')}\n\n"
    text += f"📝 Всего задач: {stats.get('total_tasks', 0)}\n\n"
    
    tasks_by_column = stats.get('tasks_by_column', {})
    if tasks_by_column:
        text += "Задачи по колонкам:\n"
        for column, count in tasks_by_column.items():
            text += f"  • {column}: {count}\n"
    
    return text

def format_board_stats(stats: Dict) -> str:
    """Форматировать статистику доски"""
    text = f"📊 Статистика доски: {stats.get('board_name', 'Неизвестно')}\n\n"
    
    columns = stats.get('columns', [])
    if columns:
        text += "Колонки:\n"
        for col in columns:
            text += f"  • {col.get('column_name', 'Неизвестно')}: {col.get('tasks_count', 0)} задач\n"
    
    return text

def format_todo_list(todo_list: Dict) -> str:
    """
    Форматировать туду-лист с группировкой по времени
    
    Args:
        todo_list: Результат todo_service.get_todo_list()
    
    Returns:
        Форматированный текст туду-листа
    """
    date_str = todo_list.get("date", "")
    personal_tasks = todo_list.get("personal_tasks", [])
    work_tasks = todo_list.get("work_tasks", [])
    grouped_by_time = todo_list.get("grouped_by_time", {})
    
    text = f"📅 <b>Туду-лист на {date_str}</b>\n\n"
    
    # Группировка по времени
    if grouped_by_time:
        # Сортировка по времени
        def sort_key(x):
            if x == "без времени":
                return datetime.max.time()
            try:
                if " - " in x:
                    return datetime.strptime(x.split(" - ")[0], "%H:%M").time()
                else:
                    return datetime.strptime(x, "%H:%M").time()
            except ValueError:
                return datetime.max.time()
        
        sorted_times = sorted(grouped_by_time.keys(), key=sort_key)
        
        for time_key in sorted_times:
            if time_key == "без времени":
                continue
            
            tasks_group = grouped_by_time[time_key]
            personal = tasks_group.get("personal", [])
            work = tasks_group.get("work", [])
            
            if personal or work:
                text += f"⏰ <b>{time_key}</b>\n"
                
                # Личные задачи
                for task in personal:
                    checkbox = "☑" if task.completed else "☐"
                    text += f"  {checkbox} {task.title}\n"
                
                # Рабочие задачи
                for task in work:
                    checkbox = "☑" if task.completed_at else "☐"
                    project_info = f"{task.project_id} - " if task.project_id else ""
                    text += f"  {checkbox} {project_info}{task.title}\n"
                
                text += "\n"
        
        # Задачи без времени
        if "без времени" in grouped_by_time:
            no_time_group = grouped_by_time["без времени"]
            personal_no_time = no_time_group.get("personal", [])
            work_no_time = no_time_group.get("work", [])
            
            if personal_no_time or work_no_time:
                text += "📋 <b>Без времени</b>\n"
                
                for task in personal_no_time:
                    checkbox = "☑" if task.completed else "☐"
                    text += f"  {checkbox} {task.title}\n"
                
                for task in work_no_time:
                    checkbox = "☑" if task.completed_at else "☐"
                    project_info = f"{task.project_id} - " if task.project_id else ""
                    text += f"  {checkbox} {project_info}{task.title}\n"
                
                text += "\n"
    
    # Если нет группировки, показываем простой список
    if not grouped_by_time:
        if personal_tasks:
            text += "<b>📝 Личные задачи:</b>\n"
            for task in personal_tasks:
                checkbox = "☑" if task.completed else "☐"
                time_info = f" ({task.time_display})" if task.time_display else ""
                text += f"  {checkbox} {task.title}{time_info}\n"
            text += "\n"
        
        if work_tasks:
            text += "<b>📊 Рабочие задачи:</b>\n"
            for task in work_tasks:
                checkbox = "☑" if task.completed_at else "☐"
                project_info = f"{task.project_id} - " if task.project_id else ""
                time_info = ""
                if task.scheduled_time:
                    time_info = f" ({task.scheduled_time.strftime('%H:%M')}"
                    if task.scheduled_time_end:
                        time_info += f" - {task.scheduled_time_end.strftime('%H:%M')}"
                    time_info += ")"
                text += f"  {checkbox} {project_info}{task.title}{time_info}\n"
    
    # Если задач нет
    if not personal_tasks and not work_tasks:
        text += "📭 Задач на эту дату нет\n\n"
        text += "Используйте AI для добавления задач:\n"
        text += '<code>"Добавь на завтра задачи..."</code>'
    
    return text


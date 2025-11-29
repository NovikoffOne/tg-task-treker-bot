"""
Callbacks для работы с проектами
"""
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from repositories.project_repository import ProjectRepository
from repositories.workspace_repository import WorkspaceRepository
from services.project_service import ProjectService
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.task_repository import TaskRepository
from utils.formatters import format_project, format_project_dashboard
from utils.keyboards import project_dashboard_keyboard, main_menu_keyboard

db = Database()
project_repo = ProjectRepository(db)
board_repo = BoardRepository(db)
column_repo = ColumnRepository(db)
task_repo = TaskRepository(db)
workspace_repo = WorkspaceRepository(db)
project_service = ProjectService(project_repo, board_repo, column_repo, task_repo)

async def handle_project_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка callback для проектов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("select_project_"):
        project_id = data.split("_")[2]
        project = project_service.get_project(project_id)
        if project:
            try:
                text = format_project(project, project_service, task_repo, column_repo, board_repo)
                await query.edit_message_text(
                    text,
                    reply_markup=project_dashboard_keyboard(project_id),
                    parse_mode='HTML'
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка: {str(e)}")
    
    elif data.startswith("project_tasks_"):
        project_id = data.split("_")[2]
        tasks = task_repo.get_all_by_project(project_id)
        if tasks:
            text = f"<b>📋 Задачи проекта ({len(tasks)}):</b>\n\n"
            for task in tasks:
                column = column_repo.get_by_id(task.column_id)
                col_name = column.name if column else "Неизвестно"
                text += f"• {task.priority_emoji} <b>#{task.id}</b> {task.title}\n"
                text += f"  📌 {col_name}\n\n"
        else:
            text = "📭 Задач пока нет"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=project_dashboard_keyboard(project_id))
    
    elif data.startswith("project_stats_"):
        project_id = data.split("_")[2]
        await query.answer("Используйте команду /statsproject " + project_id)
    
    elif data.startswith("update_stage_"):
        project_id = data.split("_")[2]
        await query.edit_message_text(
            f"🔄 <b>Обновление этапа проекта</b>\n\n"
            f"Используйте команду:\n"
            f"<code>/projectdashboard {project_id}</code>\n\n"
            f"Этап обновляется автоматически на основе колонок задач.",
            parse_mode='HTML',
            reply_markup=project_dashboard_keyboard(project_id)
        )
    
    elif data == "new_project":
        await query.edit_message_text(
            "📊 <b>Создание проекта</b>\n\n"
            "Отправьте команду:\n"
            "<code>/newproject &lt;id&gt; &lt;название&gt;</code>\n\n"
            "Например: <code>/newproject 5010 Nano Banana Ai</code>\n\n"
            "Проект автоматически создаст задачи на всех досках пространства.",
            parse_mode='HTML'
        )
    
    elif data == "project_dashboards":
        await query.answer("Используйте команду /projects для списка проектов")


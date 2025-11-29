"""
Главный обработчик всех callbacks
"""
from telegram import Update
from telegram.ext import ContextTypes
from callbacks.task_callbacks import handle_task_callback
from callbacks.navigation_callbacks import handle_navigation_callback
from callbacks.workspace_callbacks import handle_workspace_callback
from callbacks.board_callbacks import handle_board_callback
from callbacks.project_callbacks import handle_project_callback

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главный обработчик callback запросов"""
    query = update.callback_query
    data = query.data
    
    try:
        # Задачи
        if data.startswith("edit_task_") or data.startswith("delete_task_") or \
           data.startswith("priority_task_") or data.startswith("set_priority_") or \
           data.startswith("confirm_delete_") or data.startswith("cancel_delete_") or \
           data.startswith("move_task_") or data.startswith("move_to_column_") or \
           data.startswith("fields_task_") or data.startswith("tags_task_") or \
           data.startswith("subtasks_task_") or data.startswith("task_"):
            await handle_task_callback(update, context)
        
        # Пространства
        elif data.startswith("select_workspace_") or data == "new_workspace" or \
             data == "workspaces_more":
            await handle_workspace_callback(update, context)
        
        # Доски
        elif data.startswith("select_board_") or data.startswith("new_task_board_") or \
             data.startswith("stats_board_") or data.startswith("columns_board_") or \
             data.startswith("refresh_board_") or data.startswith("settings_board_") or \
             data.startswith("new_column_") or data.startswith("show_board_") or \
             data.startswith("select_column_") or data.startswith("view_task_from_board_") or \
             data == "new_board" or data == "boards_stats":
            await handle_board_callback(update, context)
        
        # Проекты
        elif data.startswith("select_project_") or data.startswith("project_tasks_") or \
             data.startswith("project_stats_") or data.startswith("update_stage_") or \
             data.startswith("project_settings_") or data == "new_project" or \
             data == "project_dashboards":
            await handle_project_callback(update, context)
        
        # Навигация
        elif data == "main_menu" or data == "back_to_tasks":
            await handle_navigation_callback(update, context)
        
        else:
            await query.answer("Команда в разработке", show_alert=False)
    except Exception as e:
        await query.answer(f"Ошибка: {str(e)}", show_alert=True)


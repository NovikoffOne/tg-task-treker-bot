"""
Утилиты для создания клавиатур
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с улучшенным UI"""
    keyboard = [
        ["📁 Пространства", "📋 Доски"],
        ["📊 Проекты", "📝 Задачи"],
        ["👤 Мои задачи", "📅 Сегодня"],
        ["📅 Туду-лист", "📈 Статистика"],
        ["⚙️ Настройки", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие или введите команду")

def workspace_keyboard(workspaces: List) -> InlineKeyboardMarkup:
    """Клавиатура для выбора пространства"""
    buttons = []
    for ws in workspaces[:10]:  # Максимум 10 пространств
        buttons.append([InlineKeyboardButton(f"📁 {ws.name}", callback_data=f"select_workspace_{ws.id}")])
    if len(workspaces) > 10:
        buttons.append([InlineKeyboardButton("➡️ Еще...", callback_data="workspaces_more")])
    buttons.append([InlineKeyboardButton("➕ Создать пространство", callback_data="new_workspace")])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def boards_keyboard(boards: List) -> InlineKeyboardMarkup:
    """Клавиатура для выбора доски"""
    buttons = []
    for board in boards[:10]:
        buttons.append([InlineKeyboardButton(f"📋 {board.name}", callback_data=f"select_board_{board.id}")])
    if len(boards) > 10:
        buttons.append([InlineKeyboardButton("➡️ Еще...", callback_data="boards_more")])
    buttons.append([
        InlineKeyboardButton("➕ Создать доску", callback_data="new_board"),
        InlineKeyboardButton("📊 Статистика", callback_data="boards_stats")
    ])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def projects_keyboard(projects: List) -> InlineKeyboardMarkup:
    """Клавиатура для выбора проекта"""
    buttons = []
    for project in projects[:10]:
        buttons.append([InlineKeyboardButton(f"📊 {project.id} {project.name}", callback_data=f"select_project_{project.id}")])
    if len(projects) > 10:
        buttons.append([InlineKeyboardButton("➡️ Еще...", callback_data="projects_more")])
    buttons.append([
        InlineKeyboardButton("➕ Создать проект", callback_data="new_project"),
        InlineKeyboardButton("📈 Дашборды", callback_data="project_dashboards")
    ])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def columns_keyboard(columns: List, board_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора колонки"""
    buttons = []
    for col in columns:
        buttons.append([InlineKeyboardButton(f"📌 {col.name}", callback_data=f"select_column_{col.id}")])
    buttons.append([
        InlineKeyboardButton("➕ Добавить колонку", callback_data=f"new_column_{board_id}"),
        InlineKeyboardButton("📋 Показать доску", callback_data=f"show_board_{board_id}")
    ])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def move_task_column_keyboard(columns: List, task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для перемещения задачи в колонку"""
    buttons = []
    for col in columns:
        buttons.append([InlineKeyboardButton(f"➡️ {col.name}", callback_data=f"move_to_column_{task_id}_{col.id}")])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=f"task_{task_id}")])
    return InlineKeyboardMarkup(buttons)

def task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Кнопки действий с задачей с улучшенным UI"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_task_{task_id}"),
            InlineKeyboardButton("🔴 Приоритет", callback_data=f"priority_task_{task_id}")
        ],
        [
            InlineKeyboardButton("📎 Поля", callback_data=f"fields_task_{task_id}"),
            InlineKeyboardButton("🏷 Метки", callback_data=f"tags_task_{task_id}")
        ],
        [
            InlineKeyboardButton("➡️ Переместить", callback_data=f"move_task_{task_id}"),
            InlineKeyboardButton("📋 Подзадачи", callback_data=f"subtasks_task_{task_id}")
        ],
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_task_{task_id}"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_tasks")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def board_keyboard(board_id: int) -> InlineKeyboardMarkup:
    """Кнопки для доски с улучшенным UI"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Новая задача", callback_data=f"new_task_board_{board_id}"),
            InlineKeyboardButton("📊 Статистика", callback_data=f"stats_board_{board_id}")
        ],
        [
            InlineKeyboardButton("📌 Колонки", callback_data=f"columns_board_{board_id}"),
            InlineKeyboardButton("⚙️ Настройки", callback_data=f"settings_board_{board_id}")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_board_{board_id}"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def priority_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Кнопки выбора приоритета с улучшенным UI"""
    keyboard = [
        [
            InlineKeyboardButton("🟢 Низкий", callback_data=f"set_priority_{task_id}_0"),
            InlineKeyboardButton("🟡 Средний", callback_data=f"set_priority_{task_id}_1")
        ],
        [
            InlineKeyboardButton("🟠 Высокий", callback_data=f"set_priority_{task_id}_2"),
            InlineKeyboardButton("🔴 Критический", callback_data=f"set_priority_{task_id}_3")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data=f"task_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def project_dashboard_keyboard(project_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для дашборда проекта"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Задачи проекта", callback_data=f"project_tasks_{project_id}"),
            InlineKeyboardButton("📊 Статистика", callback_data=f"project_stats_{project_id}")
        ],
        [
            InlineKeyboardButton("🔄 Обновить этап", callback_data=f"update_stage_{project_id}"),
            InlineKeyboardButton("⚙️ Настройки", callback_data=f"project_settings_{project_id}")
        ],
        [
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def pagination_keyboard(page: int, total_pages: int, callback_prefix: str = "page") -> Optional[InlineKeyboardMarkup]:
    """Клавиатура пагинации"""
    if total_pages <= 1:
        return None
    
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{callback_prefix}_{page-1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"{callback_prefix}_{page+1}"))
    
    if buttons:
        buttons.append(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        return InlineKeyboardMarkup([buttons])
    return None

def confirm_delete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{task_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_delete_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def task_card_keyboard(task_id: int, board_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра задачи на доске"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_task_{task_id}"),
            InlineKeyboardButton("🔴 Приоритет", callback_data=f"priority_task_{task_id}")
        ],
        [
            InlineKeyboardButton("➡️ Переместить", callback_data=f"move_task_{task_id}"),
            InlineKeyboardButton("⏰ Дедлайн", callback_data=f"deadline_task_{task_id}")
        ],
    ]
    
    if board_id:
        keyboard.append([
            InlineKeyboardButton("🔙 Назад к доске", callback_data=f"show_board_{board_id}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_tasks")
        ])
    
    return InlineKeyboardMarkup(keyboard)

def todo_list_keyboard(target_date, personal_tasks=None) -> InlineKeyboardMarkup:
    """Клавиатура для туду-листа с навигацией по датам"""
    from datetime import datetime, date, timedelta
    
    # Преобразование даты если нужно
    if isinstance(target_date, str):
        target_date = datetime.fromisoformat(target_date).date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()
    
    today = datetime.now().date()
    prev_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)
    
    date_str = target_date.isoformat()
    
    keyboard = [
        [
            InlineKeyboardButton("◀️ Вчера", callback_data=f"todo_nav_prev_{prev_date.isoformat()}"),
            InlineKeyboardButton("📅 Сегодня", callback_data=f"todo_nav_today_{today.isoformat()}"),
            InlineKeyboardButton("Завтра ▶️", callback_data=f"todo_nav_next_{next_date.isoformat()}")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data=f"todo_refresh_{date_str}"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    # Добавляем кнопки для отметки задач как выполненных (только для личных задач)
    if personal_tasks:
        for task in personal_tasks[:5]:  # Максимум 5 кнопок
            if not task.completed:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {task.title[:30]}",
                        callback_data=f"todo_complete_{task.id}"
                    )
                ])
    
    return InlineKeyboardMarkup(keyboard)


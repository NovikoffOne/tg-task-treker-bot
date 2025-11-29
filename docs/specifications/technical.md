# Техническая спецификация: Telegram Task Tracker Bot

## Архитектура проекта

### Структура файлов
```
task_tracker_bot/
├── bot.py                 # Главный файл, точка входа
├── config.py             # Конфигурация и настройки
├── database.py           # Работа с базой данных
├── models.py             # Модели данных
├── handlers/             # Обработчики команд
│   ├── __init__.py
│   ├── start.py          # /start, /help, /menu
│   ├── tasks.py          # Работа с задачами
│   └── callbacks.py       # Обработка inline-кнопок
├── utils/                # Утилиты
│   ├── __init__.py
│   ├── keyboards.py       # Создание клавиатур
│   ├── formatters.py     # Форматирование сообщений
│   └── validators.py      # Валидация данных
├── data/                 # Данные (БД)
│   └── .gitkeep
├── templates/            # Шаблоны кода
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Детальная реализация компонентов

### 1. bot.py (Главный файл)

```python
"""
Главный файл для запуска бота
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler

from config import Config
from database import Database
from handlers.start import start_command, help_command, menu_command
from handlers.tasks import (
    new_task_command, process_task_title, process_task_description,
    list_tasks_command, active_tasks_command, done_tasks_command,
    edit_task_command, process_edit_task, delete_task_command,
    done_task_command
)
from handlers.callbacks import handle_callback_query

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_TITLE, WAITING_DESCRIPTION = range(2)
WAITING_EDIT_FIELD, WAITING_EDIT_VALUE = range(2, 4)

def setup_handlers(application: Application) -> None:
    """Регистрация всех обработчиков команд"""
    
    # Базовые команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Создание задачи (ConversationHandler)
    task_conv = ConversationHandler(
        entry_points=[
            CommandHandler("newtask", new_task_command),
            MessageHandler(filters.Regex("^➕ Создать задачу$"), new_task_command)
        ],
        states={
            WAITING_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_title)
            ],
            WAITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_task_description),
                CommandHandler("skip", process_task_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(task_conv)
    
    # Просмотр задач
    application.add_handler(CommandHandler("tasks", list_tasks_command))
    application.add_handler(CommandHandler("active", active_tasks_command))
    application.add_handler(CommandHandler("done", done_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^📋 Мои задачи$"), list_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^⏳ Активные$"), active_tasks_command))
    application.add_handler(MessageHandler(filters.Regex("^✅ Выполненные$"), done_tasks_command))
    
    # Редактирование задачи
    edit_conv = ConversationHandler(
        entry_points=[
            CommandHandler("edit", edit_task_command),
        ],
        states={
            WAITING_EDIT_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_task)
            ],
            WAITING_EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_task)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(edit_conv)
    
    # Действия с задачами
    application.add_handler(CommandHandler("delete", delete_task_command))
    application.add_handler(CommandHandler("done_task", done_task_command))
    
    # Обработка inline-кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query))

def main() -> None:
    """Главная функция запуска бота"""
    load_dotenv()
    
    token = Config.BOT_TOKEN
    if not token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения!")
    
    # Инициализация БД
    db = Database()
    db.init_db()
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков
    setup_handlers(application)
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
```

### 2. config.py

```python
"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/tasks.db")
    TASKS_PER_PAGE = int(os.getenv("TASKS_PER_PAGE", "5"))
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
```

### 3. models.py

```python
"""
Модели данных для таск-трекера
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    id: int
    user_id: int
    title: str
    description: Optional[str]
    status: str  # 'active' | 'completed'
    created_at: datetime
    completed_at: Optional[datetime]
    updated_at: datetime
    
    @property
    def is_completed(self) -> bool:
        return self.status == 'completed'
    
    @property
    def is_active(self) -> bool:
        return self.status == 'active'
```

### 4. database.py

```python
"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple
from contextlib import contextmanager

from models import Task
from config import Config

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self) -> None:
        """Инициализация базы данных, создание таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_user_id 
                ON tasks(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_user_status 
                ON tasks(user_id, status)
            """)
    
    def create_task(self, user_id: int, title: str, description: Optional[str] = None) -> int:
        """Создать новую задачу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (user_id, title, description, status)
                VALUES (?, ?, ?, 'active')
            """, (user_id, title, description))
            return cursor.lastrowid
    
    def get_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE id = ? AND user_id = ?
            """, (task_id, user_id))
            row = cursor.fetchone()
            if row:
                return self._row_to_task(row)
            return None
    
    def get_user_tasks(
        self, 
        user_id: int, 
        status: Optional[str] = None,
        limit: int = 5,
        offset: int = 0
    ) -> Tuple[List[Task], int]:
        """Получить задачи пользователя с пагинацией"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT COUNT(*) FROM tasks 
                    WHERE user_id = ? AND status = ?
                """, (user_id, status))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM tasks 
                    WHERE user_id = ?
                """, (user_id,))
            total = cursor.fetchone()[0]
            
            if status:
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, status, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM tasks 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
            
            rows = cursor.fetchall()
            tasks = [self._row_to_task(row) for row in rows]
            return tasks, total
    
    def update_task_status(self, task_id: int, user_id: int, status: str) -> bool:
        """Обновить статус задачи"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            completed_at = datetime.now() if status == 'completed' else None
            cursor.execute("""
                UPDATE tasks 
                SET status = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (status, completed_at, task_id, user_id))
            return cursor.rowcount > 0
    
    def update_task(self, task_id: int, user_id: int, title: Optional[str] = None, 
                   description: Optional[str] = None) -> bool:
        """Обновить задачу"""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([task_id, user_id])
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE tasks 
                SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
            """, params)
            return cursor.rowcount > 0
    
    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Удалить задачу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tasks 
                WHERE id = ? AND user_id = ?
            """, (task_id, user_id))
            return cursor.rowcount > 0
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Преобразовать строку БД в объект Task"""
        from models import Task
        return Task(
            id=row['id'],
            user_id=row['user_id'],
            title=row['title'],
            description=row['description'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] and isinstance(row['completed_at'], str) else row['completed_at'],
            updated_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at']
        )
```

### 5. utils/keyboards.py

```python
"""
Утилиты для создания клавиатур
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        ["➕ Создать задачу", "📋 Мои задачи"],
        ["⏳ Активные", "✅ Выполненные"],
        ["❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Кнопки действий с задачей"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{task_id}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{task_id}")
        ],
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{task_id}"),
            InlineKeyboardButton("📋 Все задачи", callback_data="list_tasks")
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
```

### 6. utils/formatters.py

```python
"""
Утилиты для форматирования сообщений
"""
from datetime import datetime
from typing import List
from models import Task

def format_task(task: Task) -> str:
    """Форматировать одну задачу для отображения"""
    status_emoji = "✅" if task.is_completed else "⏳"
    status_text = "Выполнено" if task.is_completed else "В работе"
    
    description = task.description if task.description else "Без описания"
    
    text = f"📋 Задача #{task.id}\n"
    text += f"Название: {task.title}\n"
    text += f"Описание: {description}\n"
    text += f"Статус: {status_emoji} {status_text}\n"
    text += f"Создано: {format_datetime(task.created_at)}"
    
    if task.completed_at:
        text += f"\nЗавершено: {format_datetime(task.completed_at)}"
    
    return text

def format_tasks_list(tasks: List[Task], page: int, total: int, total_pages: int) -> str:
    """Форматировать список задач"""
    if not tasks:
        return "📭 У вас пока нет задач."
    
    text = f"📋 Ваши задачи (страница {page}/{total_pages}, всего: {total})\n\n"
    
    for task in tasks:
        status_emoji = "✅" if task.is_completed else "⏳"
        text += f"{status_emoji} Задача #{task.id}: {task.title}\n"
        text += f"   Создано: {format_datetime(task.created_at)}\n\n"
    
    return text.strip()

def format_datetime(dt: datetime) -> str:
    """Форматировать datetime в читаемый формат"""
    return dt.strftime("%d.%m.%Y %H:%M")
```

### 7. utils/validators.py

```python
"""
Валидация данных
"""
from typing import Tuple, Optional

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 1000

def validate_title(title: str) -> Tuple[bool, Optional[str]]:
    """Валидация названия задачи"""
    title = title.strip()
    
    if len(title) < MIN_TITLE_LENGTH:
        return False, f"Название задачи слишком короткое (минимум {MIN_TITLE_LENGTH} символа)"
    
    if len(title) > MAX_TITLE_LENGTH:
        return False, f"Название задачи слишком длинное (максимум {MAX_TITLE_LENGTH} символов)"
    
    return True, None

def validate_description(description: str) -> Tuple[bool, Optional[str]]:
    """Валидация описания задачи"""
    description = description.strip()
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Описание слишком длинное (максимум {MAX_DESCRIPTION_LENGTH} символов)"
    
    return True, None

def validate_task_id(task_id_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Валидация ID задачи"""
    try:
        task_id = int(task_id_str)
        if task_id <= 0:
            return False, None, "ID задачи должен быть положительным числом"
        return True, task_id, None
    except ValueError:
        return False, None, "ID задачи должен быть числом"
```

## Обработка состояний (ConversationHandler)

### Состояния для создания задачи:
- `WAITING_TITLE` - ожидание названия
- `WAITING_DESCRIPTION` - ожидание описания

### Состояния для редактирования:
- `WAITING_EDIT_FIELD` - ожидание выбора поля (название/описание)
- `WAITING_EDIT_VALUE` - ожидание нового значения

## Обработка callback-запросов

Формат callback_data:
- `done_<task_id>` - отметить выполненной
- `edit_<task_id>` - редактировать
- `delete_<task_id>` - удалить (показать подтверждение)
- `confirm_delete_<task_id>` - подтвердить удаление
- `cancel_delete_<task_id>` - отменить удаление
- `page_<page_number>` - пагинация
- `list_tasks` - показать список задач
- `main_menu` - главное меню


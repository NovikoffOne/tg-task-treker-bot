"""
Конфигурация для pytest
"""
import pytest
import os
import tempfile
import shutil
import sys

# Добавляем путь к корню task_tracker_bot для корректных импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database

@pytest.fixture
def temp_db():
    """Создать временную БД для тестов"""
    # Создать временную директорию
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    # Создать БД
    db = Database(db_path=db_path)
    db.init_db()
    
    # Выполнить миграцию MVP 0.2
    try:
        # Выполнить миграцию напрямую
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Создать таблицы MVP 0.2
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS board_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    source_board_id INTEGER NOT NULL,
                    source_column_id INTEGER NOT NULL,
                    trigger_type TEXT NOT NULL DEFAULT 'enter',
                    target_board_id INTEGER NOT NULL,
                    target_column_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    task_title_template TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_board_id) REFERENCES boards(id) ON DELETE CASCADE,
                    FOREIGN KEY (source_column_id) REFERENCES columns(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_board_id) REFERENCES boards(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_column_id) REFERENCES columns(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_assignees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'assignee',
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    UNIQUE(task_id, user_id, role)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE(project_id, user_id, role)
                )
            """)
            
            # Добавить колонки в tasks, если их нет
            cursor.execute("PRAGMA table_info(tasks)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            if 'assignee_id' not in existing_columns:
                cursor.execute("ALTER TABLE tasks ADD COLUMN assignee_id INTEGER")
            if 'started_at' not in existing_columns:
                cursor.execute("ALTER TABLE tasks ADD COLUMN started_at TIMESTAMP")
            if 'completed_at' not in existing_columns:
                cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
            if 'deadline' not in existing_columns:
                cursor.execute("ALTER TABLE tasks ADD COLUMN deadline TIMESTAMP")
            
            conn.commit()
    except Exception as e:
        # Если миграция не удалась, продолжаем (может быть уже выполнена)
        import traceback
        print(f"Warning: Migration failed: {e}")
        print(traceback.format_exc())
    
    yield db
    
    # Очистка после тестов
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_user_id():
    """Тестовый user_id"""
    return 12345


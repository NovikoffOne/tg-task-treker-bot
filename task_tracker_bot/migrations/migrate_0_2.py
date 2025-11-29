"""
Миграция БД для MVP 0.2
Добавляет таблицы и колонки для новых функций
"""
import sqlite3
import logging
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database

logger = logging.getLogger(__name__)

def migrate():
    """Выполнить миграцию БД"""
    db = Database()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Таблица зависимостей досок
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
                CREATE INDEX IF NOT EXISTS idx_board_dependencies_workspace 
                ON board_dependencies(workspace_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_board_dependencies_source 
                ON board_dependencies(source_board_id, source_column_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_board_dependencies_enabled 
                ON board_dependencies(enabled)
            """)
            
            # 2. Таблица действий зависимостей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS board_dependency_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dependency_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_data TEXT,
                    FOREIGN KEY (dependency_id) REFERENCES board_dependencies(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_board_dependency_actions_dependency 
                ON board_dependency_actions(dependency_id)
            """)
            
            # 3. Таблица назначений задач
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
                CREATE INDEX IF NOT EXISTS idx_task_assignees_task 
                ON task_assignees(task_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_assignees_user 
                ON task_assignees(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_assignees_role 
                ON task_assignees(role)
            """)
            
            # 4. Таблица участников проекта
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
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_members_project 
                ON project_members(project_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_members_user 
                ON project_members(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_members_role 
                ON project_members(role)
            """)
            
            # 5. Добавить новые колонки в таблицу tasks
            # SQLite не поддерживает IF NOT EXISTS для ALTER TABLE
            # Используем проверку через PRAGMA table_info
            
            cursor.execute("PRAGMA table_info(tasks)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            if 'assignee_id' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN assignee_id INTEGER")
                    logger.info("✅ Добавлена колонка assignee_id")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить assignee_id: {e}")
            
            if 'started_at' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN started_at TIMESTAMP")
                    logger.info("✅ Добавлена колонка started_at")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить started_at: {e}")
            
            if 'completed_at' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
                    logger.info("✅ Добавлена колонка completed_at")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить completed_at: {e}")
            
            if 'deadline' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN deadline TIMESTAMP")
                    logger.info("✅ Добавлена колонка deadline")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить deadline: {e}")
            
            # 6. Создать индексы для новых колонок
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tasks_deadline'")
            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_tasks_deadline 
                        ON tasks(deadline)
                    """)
                    logger.info("✅ Создан индекс idx_tasks_deadline")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось создать индекс deadline: {e}")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tasks_assignee'")
            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_tasks_assignee 
                        ON tasks(assignee_id)
                    """)
                    logger.info("✅ Создан индекс idx_tasks_assignee")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось создать индекс assignee: {e}")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tasks_started'")
            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_tasks_started 
                        ON tasks(started_at)
                    """)
                    logger.info("✅ Создан индекс idx_tasks_started")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось создать индекс started: {e}")
            
            conn.commit()
            logger.info("✅ Миграция БД MVP 0.2 выполнена успешно")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = migrate()
    exit(0 if success else 1)


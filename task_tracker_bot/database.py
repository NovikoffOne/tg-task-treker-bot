"""
Модуль для работы с базой данных SQLite
Создает все таблицы согласно ARCHITECTURE.md
"""
import sqlite3
import os
from typing import Optional
from contextlib import contextmanager
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
        """Инициализация базы данных, создание всех таблиц согласно ARCHITECTURE.md"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица: workspaces
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_workspaces_user_id 
                ON workspaces(user_id)
            """)
            
            # Таблица: boards
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    UNIQUE(workspace_id, name)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_boards_workspace_id 
                ON boards(workspace_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_boards_position 
                ON boards(workspace_id, position)
            """)
            
            # Таблица: columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                    UNIQUE(board_id, name)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_columns_board_id 
                ON columns(board_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_columns_position 
                ON columns(board_id, position)
            """)
            
            # Таблица: projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    workspace_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    dashboard_stage TEXT DEFAULT 'preparation',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_workspace_id 
                ON projects(workspace_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_dashboard_stage 
                ON projects(dashboard_stage)
            """)
            
            # Таблица: tasks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    column_id INTEGER NOT NULL,
                    parent_task_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER DEFAULT 0,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
                    FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_column_id 
                ON tasks(column_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_project_id 
                ON tasks(project_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id 
                ON tasks(parent_task_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_priority 
                ON tasks(priority)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_position 
                ON tasks(column_id, position)
            """)
            
            # Таблица: task_tags
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    color TEXT DEFAULT '#3498db',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    UNIQUE(workspace_id, name)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_tags_workspace_id 
                ON task_tags(workspace_id)
            """)
            
            # Таблица: task_tag_relations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_tag_relations (
                    task_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (task_id, tag_id),
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES task_tags(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица: custom_fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    field_type TEXT NOT NULL,
                    default_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    UNIQUE(workspace_id, name)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_custom_fields_workspace_id 
                ON custom_fields(workspace_id)
            """)
            
            # Таблица: task_custom_fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_custom_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    field_id INTEGER NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
                    UNIQUE(task_id, field_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_custom_fields_task_id 
                ON task_custom_fields(task_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_custom_fields_field_id 
                ON task_custom_fields(field_id)
            """)
            
            # Таблица: project_field_sync
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_field_sync (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    field_id INTEGER NOT NULL,
                    sync_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
                    UNIQUE(project_id, field_id)
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_field_sync_project_id 
                ON project_field_sync(project_id)
            """)


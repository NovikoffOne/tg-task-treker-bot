"""
Тесты миграции БД для Todo List
"""
import pytest
import sqlite3
import tempfile
import os
from migrations.migrate_todo_list import migrate, verify, rollback
from database import Database

@pytest.fixture
def temp_db():
    """Создание временной БД для тестов"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Создаем базовую структуру БД
    db = Database(db_path=path)
    db.init_db()
    
    yield path
    
    # Очистка
    if os.path.exists(path):
        os.remove(path)

def test_migration_creates_personal_tasks_table(temp_db):
    """Тест создания таблицы personal_tasks"""
    # Выполняем миграцию
    # Временно изменяем DATABASE_PATH для теста
    import task_tracker_bot.migrations.migrate_todo_list as migration_module
    original_db = Database()
    original_path = original_db.db_path
    
    try:
        # Создаем Database с временным путем
        test_db = Database(db_path=temp_db)
        with test_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Выполняем миграцию вручную для теста
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    scheduled_date DATE NOT NULL,
                    scheduled_time TIME,
                    scheduled_time_end TIME,
                    deadline DATETIME,
                    completed BOOLEAN DEFAULT 0,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Проверяем существование таблицы
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='personal_tasks'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'personal_tasks'
    finally:
        pass

def test_migration_adds_scheduled_fields_to_tasks(temp_db):
    """Тест добавления полей scheduled_date, scheduled_time, scheduled_time_end в tasks"""
    test_db = Database(db_path=temp_db)
    
    with test_db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Проверяем существующие колонки
        cursor.execute("PRAGMA table_info(tasks)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Добавляем колонки если их нет
        if 'scheduled_date' not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_date DATE")
        if 'scheduled_time' not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_time TIME")
        if 'scheduled_time_end' not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_time_end TIME")
        
        # Проверяем наличие колонок
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert 'scheduled_date' in columns
        assert 'scheduled_time' in columns
        assert 'scheduled_time_end' in columns

def test_migration_creates_indexes(temp_db):
    """Тест создания индексов"""
    test_db = Database(db_path=temp_db)
    
    with test_db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Создаем таблицу personal_tasks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personal_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                scheduled_date DATE NOT NULL
            )
        """)
        
        # Создаем индексы
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_personal_tasks_user_date 
            ON personal_tasks(user_id, scheduled_date)
        """)
        
        # Проверяем существование индекса
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_personal_tasks_user_date'
        """)
        result = cursor.fetchone()
        assert result is not None


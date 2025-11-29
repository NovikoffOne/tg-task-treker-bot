"""
Тесты для database.py
"""
import pytest
from database import Database
import os

def test_database_initialization(temp_db):
    """Тест инициализации БД"""
    assert temp_db is not None
    assert os.path.exists(temp_db.db_path)

def test_database_tables_created(temp_db):
    """Тест создания всех таблиц"""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Проверить существование всех таблиц
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'workspaces', 'boards', 'columns', 'projects', 'tasks',
            'task_tags', 'task_tag_relations', 'custom_fields',
            'task_custom_fields', 'project_field_sync'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Таблица {table} не создана"

def test_database_connection(temp_db):
    """Тест работы с соединением"""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


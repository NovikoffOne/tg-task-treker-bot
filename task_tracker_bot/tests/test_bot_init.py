"""
Тесты инициализации бота
"""
import pytest
import os
from database import Database
from config import Config

def test_database_initialization():
    """Тест инициализации БД через Database.init_db()"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_init.db")
    
    try:
        db = Database(db_path=db_path)
        db.init_db()
        
        # Проверить, что файл создан
        assert os.path.exists(db_path)
        
        # Проверить, что таблицы созданы
        with db.get_connection() as conn:
            cursor = conn.cursor()
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
    finally:
        shutil.rmtree(temp_dir)

def test_config_defaults():
    """Тест значений по умолчанию в Config"""
    # DATABASE_PATH должен иметь значение по умолчанию
    assert Config.DATABASE_PATH is not None
    
    # TASKS_PER_PAGE должен быть числом
    assert isinstance(Config.TASKS_PER_PAGE, int)
    assert Config.TASKS_PER_PAGE > 0
    
    # TIMEZONE должен быть строкой
    assert isinstance(Config.TIMEZONE, str)
    assert len(Config.TIMEZONE) > 0


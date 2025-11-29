"""
Скрипт для очистки базы данных перед тестированием
Удаляет все данные из таблиц, сохраняя структуру
"""
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from config import Config

def clear_database():
    """Очистить все данные из базы данных"""
    db = Database()
    
    # Порядок удаления важен из-за внешних ключей
    # Удаляем в порядке зависимостей (от дочерних к родительским)
    
    tables_to_clear = [
        # Таблицы связей (удаляем первыми)
        'task_tag_relations',
        'task_custom_fields',
        'project_field_sync',
        'board_dependency_actions',
        'task_assignees',
        'project_members',
        
        # Основные таблицы данных
        'tasks',
        'task_tags',
        'custom_fields',
        'board_dependencies',
        'columns',
        'boards',
        'projects',
        'workspaces',
    ]
    
    print("Начинаю очистку базы данных...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Отключаем проверку внешних ключей для более быстрой очистки
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        try:
            for table in tables_to_clear:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    count = cursor.rowcount
                    print(f"✓ Очищена таблица {table}: удалено {count} записей")
                except Exception as e:
                    print(f"⚠ Ошибка при очистке таблицы {table}: {e}")
            
            # Включаем обратно проверку внешних ключей
            cursor.execute("PRAGMA foreign_keys = ON")
            
            print("\n✅ Очистка базы данных завершена успешно!")
            
        except Exception as e:
            print(f"\n❌ Ошибка при очистке базы данных: {e}")
            raise

if __name__ == "__main__":
    try:
        clear_database()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


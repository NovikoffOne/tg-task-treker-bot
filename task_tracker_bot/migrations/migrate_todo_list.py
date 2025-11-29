"""
Миграция БД для Todo List Feature
Добавляет таблицу personal_tasks и расширяет tasks
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
            
            # 1. Создать таблицу personal_tasks
            logger.info("Создание таблицы personal_tasks...")
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
            logger.info("✅ Таблица personal_tasks создана")
            
            # 2. Создать индексы для personal_tasks
            logger.info("Создание индексов для personal_tasks...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_personal_tasks_user_date 
                ON personal_tasks(user_id, scheduled_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_personal_tasks_deadline 
                ON personal_tasks(deadline)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_personal_tasks_completed 
                ON personal_tasks(user_id, completed)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_personal_tasks_user_completed 
                ON personal_tasks(user_id, completed, scheduled_date)
            """)
            logger.info("✅ Индексы для personal_tasks созданы")
            
            # 3. Проверить и добавить колонки в tasks
            logger.info("Проверка существующих колонок в tasks...")
            cursor.execute("PRAGMA table_info(tasks)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Добавить scheduled_date
            if 'scheduled_date' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_date DATE")
                    logger.info("✅ Добавлена колонка scheduled_date")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить scheduled_date: {e}")
            else:
                logger.info("ℹ️ Колонка scheduled_date уже существует")
            
            # Добавить scheduled_time
            if 'scheduled_time' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_time TIME")
                    logger.info("✅ Добавлена колонка scheduled_time")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить scheduled_time: {e}")
            else:
                logger.info("ℹ️ Колонка scheduled_time уже существует")
            
            # Добавить scheduled_time_end
            if 'scheduled_time_end' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN scheduled_time_end TIME")
                    logger.info("✅ Добавлена колонка scheduled_time_end")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Не удалось добавить scheduled_time_end: {e}")
            else:
                logger.info("ℹ️ Колонка scheduled_time_end уже существует")
            
            # 4. Создать индексы для tasks
            logger.info("Создание индексов для tasks...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_date 
                ON tasks(scheduled_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_project_scheduled 
                ON tasks(project_id, scheduled_date) WHERE project_id IS NOT NULL
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_datetime 
                ON tasks(scheduled_date, scheduled_time) WHERE scheduled_date IS NOT NULL
            """)
            logger.info("✅ Индексы для tasks созданы")
            
            conn.commit()
            logger.info("✅ Миграция успешно завершена")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграции: {e}", exc_info=True)
        return False

def rollback():
    """Откатить миграцию"""
    db = Database()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            logger.warning("⚠️ Начинается откат миграции...")
            
            # Удалить индексы
            cursor.execute("DROP INDEX IF EXISTS idx_tasks_scheduled_datetime")
            cursor.execute("DROP INDEX IF EXISTS idx_tasks_project_scheduled")
            cursor.execute("DROP INDEX IF EXISTS idx_tasks_scheduled_date")
            cursor.execute("DROP INDEX IF EXISTS idx_personal_tasks_user_completed")
            cursor.execute("DROP INDEX IF EXISTS idx_personal_tasks_completed")
            cursor.execute("DROP INDEX IF EXISTS idx_personal_tasks_deadline")
            cursor.execute("DROP INDEX IF EXISTS idx_personal_tasks_user_date")
            
            # Удалить таблицу personal_tasks
            cursor.execute("DROP TABLE IF EXISTS personal_tasks")
            
            # Удалить колонки из tasks
            # SQLite не поддерживает DROP COLUMN напрямую,
            # требуется пересоздание таблицы (опасная операция!)
            logger.warning("⚠️ Удаление колонок из tasks требует пересоздания таблицы")
            logger.warning("⚠️ Рекомендуется сделать резервную копию БД перед откатом")
            
            conn.commit()
            logger.info("✅ Откат миграции завершен (частично)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при откате миграции: {e}", exc_info=True)
        return False

def verify():
    """Проверить успешность миграции"""
    db = Database()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверить таблицу personal_tasks
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='personal_tasks'
            """)
            if not cursor.fetchone():
                logger.error("❌ Таблица personal_tasks не найдена")
                return False
            
            # Проверить колонки в tasks
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            required_columns = ['scheduled_date', 'scheduled_time', 'scheduled_time_end']
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                logger.warning(f"⚠️ Отсутствуют колонки: {missing_columns}")
                return False
            
            # Проверить индексы
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%scheduled%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ Найдено индексов: {len(indexes)}")
            
            logger.info("✅ Миграция проверена успешно")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке миграции: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import argparse
    parser = argparse.ArgumentParser(description='Миграция БД для Todo List Feature')
    parser.add_argument('--rollback', action='store_true', help='Откатить миграцию')
    parser.add_argument('--verify', action='store_true', help='Проверить миграцию')
    
    args = parser.parse_args()
    
    if args.rollback:
        print("⚠️ ВНИМАНИЕ: Откат миграции удалит таблицу personal_tasks!")
        confirm = input("Продолжить? (yes/no): ")
        if confirm.lower() == 'yes':
            rollback()
        else:
            print("Откат отменен")
    elif args.verify:
        verify()
    else:
        print("Выполнение миграции...")
        migrate()
        print("\nПроверка миграции...")
        verify()


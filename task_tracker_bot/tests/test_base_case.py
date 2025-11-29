"""
Автотест базового сценария работы с проектом
Запускается по тегу @start_test_baseCase в Telegram боте
"""
"""
Автотест базового сценария работы с проектом
Запускается по тегу @start_test_baseCase в Telegram боте
"""
import asyncio
import re
from typing import Optional, Dict, List, Any

# Импорты используют относительные пути от корня task_tracker_bot
# При запуске из handlers/start.py эти импорты должны работать корректно
try:
    from database import Database
    from repositories.workspace_repository import WorkspaceRepository
    from repositories.board_repository import BoardRepository
    from repositories.column_repository import ColumnRepository
    from repositories.project_repository import ProjectRepository
    from repositories.task_repository import TaskRepository
    from repositories.custom_field_repository import CustomFieldRepository
    from repositories.tag_repository import TagRepository
    from services.workspace_service import WorkspaceService
    from services.board_service import BoardService
    from services.project_service import ProjectService
    from services.task_service import TaskService
    from services.sync_service import SyncService
except ImportError:
    # Если импорты не работают, пробуем абсолютные
    import sys
    import os
    # Добавляем путь к корню task_tracker_bot
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from database import Database
    from repositories.workspace_repository import WorkspaceRepository
    from repositories.board_repository import BoardRepository
    from repositories.column_repository import ColumnRepository
    from repositories.project_repository import ProjectRepository
    from repositories.task_repository import TaskRepository
    from repositories.custom_field_repository import CustomFieldRepository
    from repositories.tag_repository import TagRepository
    from services.workspace_service import WorkspaceService
    from services.board_service import BoardService
    from services.project_service import ProjectService
    from services.task_service import TaskService
    from services.sync_service import SyncService


class BaseCaseTestRunner:
    """Класс для запуска базового теста"""
    
    def __init__(self, db: Database, user_id: int = 12345):
        self.db = db
        self.user_id = user_id
        self.workspace_id: Optional[int] = None
        self.project_id = "5001"
        self.project_name = "Pictory Ai"
        self.task_ids: Dict[str, int] = {}  # board_name -> task_id
        self.field_ids: Dict[str, int] = {}  # field_name -> field_id
        self.tag_id: Optional[int] = None
        
        # Инициализация репозиториев
        self.workspace_repo = WorkspaceRepository(db)
        self.board_repo = BoardRepository(db)
        self.column_repo = ColumnRepository(db)
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)
        self.field_repo = CustomFieldRepository(db)
        self.tag_repo = TagRepository(db)
        
        # Инициализация сервисов
        self.workspace_service = WorkspaceService(self.workspace_repo)
        self.board_service = BoardService(self.board_repo, self.column_repo)
        self.project_service = ProjectService(
            self.project_repo, self.board_repo, self.column_repo, self.task_repo
        )
        self.task_service = TaskService(self.task_repo, self.column_repo)
        self.sync_service = SyncService(self.task_repo, self.field_repo)
        
        self.test_results: List[Dict[str, Any]] = []
    
    def log_test(self, step: str, status: str, message: str = ""):
        """Логирование результата теста"""
        self.test_results.append({
            "step": step,
            "status": status,
            "message": message
        })
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {step}: {message}")
    
    def setup_workspace(self) -> bool:
        """Этап 1: Создание тестового пространства"""
        print("\n" + "="*60)
        print("ЭТАП 1: Подготовка тестового пространства")
        print("="*60)
        
        # Проверить существование пространства
        workspaces = self.workspace_repo.get_all_by_user(self.user_id)
        test_workspace = next((w for w in workspaces if w.name == "Тестовое пространство"), None)
        
        if test_workspace:
            self.workspace_id = test_workspace.id
            self.log_test("1.1", "PASSED", "Тестовое пространство уже существует")
        else:
            success, workspace_id, error = self.workspace_service.create_workspace(
                self.user_id, "Тестовое пространство"
            )
            if success:
                self.workspace_id = workspace_id
                self.log_test("1.1", "PASSED", "Тестовое пространство создано")
            else:
                self.log_test("1.1", "FAILED", f"Ошибка создания пространства: {error}")
                return False
        
        return True
    
    def setup_boards(self) -> bool:
        """Этап 1.2: Создание досок с колонками"""
        print("\n" + "="*60)
        print("ЭТАП 1.2: Создание досок с колонками")
        print("="*60)
        
        boards_config = {
            "Подготовка": [],  # Дефолтные колонки
            "Дизайн": ["Очередь", "План на неделю", "В работе", "На утверждении", "Готово"],
            "Разработка": [
                "Очередь", "План на неделю", "В работе", "Тестирование",
                "Фикс Багов", "Готово", "Отправленно AppConnect"
            ],
            "Тестирование": [
                "Очередь", "План на неделю", "В работе", "Модерация", "Реджект", "Готово"
            ],
            "Store": [
                "Очередь", "В работе", "На модерации", "Реджект", "Опубликовано",
                "Реджект 4.3", "SPAM", "BAN"
            ],
            "АСО": ["Очередь", "В работе", "Готово"],
            "Подготовка аккаунта": ["Очередь", "План на неделю", "В работе", "Готово"]
        }
        
        for board_name, columns in boards_config.items():
            # Проверить существование доски
            board = self.board_service.get_board_by_name(self.workspace_id, board_name)
            
            if board:
                self.log_test(f"1.2.{board_name}", "PASSED", f"Доска '{board_name}' уже существует")
            else:
                success, board_id, error = self.board_service.create_board(self.workspace_id, board_name)
                if not success:
                    self.log_test(f"1.2.{board_name}", "FAILED", f"Ошибка создания доски: {error}")
                    return False
                board = self.board_service.get_board(board_id)
                self.log_test(f"1.2.{board_name}", "PASSED", f"Доска '{board_name}' создана")
            
            # Создать колонки
            existing_columns = self.board_service.list_columns(board.id)
            existing_column_names = {col.name for col in existing_columns}
            
            for col_name in columns:
                if col_name not in existing_column_names:
                    success, col_id, error = self.board_service.create_column(board.id, col_name)
                    if success:
                        self.log_test(f"1.2.{board_name}.{col_name}", "PASSED", f"Колонка '{col_name}' создана")
                    else:
                        self.log_test(f"1.2.{board_name}.{col_name}", "FAILED", f"Ошибка: {error}")
                        return False
                else:
                    self.log_test(f"1.2.{board_name}.{col_name}", "PASSED", f"Колонка '{col_name}' уже существует")
        
        return True
    
    def create_project(self) -> bool:
        """Этап 2: Создание проекта"""
        print("\n" + "="*60)
        print("ЭТАП 2: Создание проекта")
        print("="*60)
        
        # Проверить существование проекта
        project = self.project_service.get_project(self.project_id)
        if project:
            self.log_test("2.1", "PASSED", f"Проект {self.project_id} уже существует")
        else:
            success, created_id, error = self.project_service.create_project(
                self.project_id, self.workspace_id, self.project_name
            )
            if success:
                self.log_test("2.1", "PASSED", f"Проект {self.project_id} создан")
            else:
                self.log_test("2.1", "FAILED", f"Ошибка создания проекта: {error}")
                return False
        
        # Получить задачи проекта
        tasks = self.task_service.list_tasks_by_project(self.project_id)
        for task in tasks:
            column = self.column_repo.get_by_id(task.column_id)
            if column:
                board = self.board_repo.get_by_id(column.board_id)
                if board:
                    self.task_ids[board.name] = task.id
        
        self.log_test("2.2", "PASSED", f"Задачи созданы на {len(self.task_ids)} досках")
        return True
    
    def get_task_by_board(self, board_name: str) -> Optional[int]:
        """Получить ID задачи по названию доски"""
        return self.task_ids.get(board_name)
    
    def get_column_id(self, board_name: str, column_name: str) -> Optional[int]:
        """Получить ID колонки по названию доски и колонки"""
        board = self.board_service.get_board_by_name(self.workspace_id, board_name)
        if not board:
            return None
        columns = self.board_service.list_columns(board.id)
        column = next((c for c in columns if c.name == column_name), None)
        return column.id if column else None
    
    def move_task(self, board_name: str, column_name: str) -> bool:
        """Переместить задачу в колонку"""
        task_id = self.get_task_by_board(board_name)
        if not task_id:
            self.log_test(f"move.{board_name}", "FAILED", f"Задача не найдена на доске {board_name}")
            return False
        
        column_id = self.get_column_id(board_name, column_name)
        if not column_id:
            self.log_test(f"move.{board_name}.{column_name}", "FAILED", f"Колонка не найдена")
            return False
        
        success, error = self.task_service.move_task(task_id, column_id)
        if success:
            self.log_test(f"move.{board_name}.{column_name}", "PASSED", f"Задача перемещена")
            return True
        else:
            self.log_test(f"move.{board_name}.{column_name}", "FAILED", f"Ошибка: {error}")
            return False
    
    def create_field(self, field_name: str, field_type: str = "url") -> bool:
        """Создать поле (если не существует)"""
        if field_name in self.field_ids:
            return True
        
        field = self.field_repo.get_by_name(self.workspace_id, field_name)
        if field:
            self.field_ids[field_name] = field.id
            return True
        
        field_id = self.field_repo.create(self.workspace_id, field_name, field_type)
        self.field_ids[field_name] = field_id
        self.log_test(f"field.{field_name}", "PASSED", f"Поле '{field_name}' создано")
        return True
    
    def add_field_to_task(self, board_name: str, field_name: str, value: str) -> bool:
        """Добавить поле к задаче"""
        task_id = self.get_task_by_board(board_name)
        if not task_id:
            self.log_test(f"addfield.{board_name}.{field_name}", "FAILED", "Задача не найдена")
            return False
        
        if field_name not in self.field_ids:
            self.log_test(f"addfield.{board_name}.{field_name}", "FAILED", "Поле не создано")
            return False
        
        field_id = self.field_ids[field_name]
        
        # Синхронизация включается автоматически в sync_service.sync_field_to_project
        # при первом добавлении поля к задаче проекта
        success, error = self.sync_service.sync_field_to_project(task_id, field_id, value)
        if success:
            self.log_test(f"addfield.{board_name}.{field_name}", "PASSED", f"Поле добавлено: {value[:50]}...")
            return True
        else:
            self.log_test(f"addfield.{board_name}.{field_name}", "FAILED", f"Ошибка: {error}")
            return False
    
    def check_task_fields(self, board_name: str, expected_fields: Dict[str, str]) -> bool:
        """Проверить наличие полей у задачи"""
        task_id = self.get_task_by_board(board_name)
        if not task_id:
            self.log_test(f"check.{board_name}", "FAILED", "Задача не найдена")
            return False
        
        task_fields = self.field_repo.get_task_fields(task_id)
        all_present = True
        
        for field_name, expected_value in expected_fields.items():
            if field_name not in self.field_ids:
                self.log_test(f"check.{board_name}.{field_name}", "FAILED", "Поле не создано")
                all_present = False
                continue
            
            field_id = self.field_ids[field_name]
            actual_value = task_fields.get(field_id)
            
            if actual_value == expected_value:
                self.log_test(f"check.{board_name}.{field_name}", "PASSED", f"Поле найдено: {expected_value[:50]}...")
            else:
                self.log_test(f"check.{board_name}.{field_name}", "FAILED", 
                            f"Ожидалось: {expected_value[:50]}..., получено: {actual_value}")
                all_present = False
        
        return all_present
    
    def create_tag(self, tag_name: str) -> bool:
        """Создать метку (если не существует)"""
        if self.tag_id:
            return True
        
        tag = self.tag_repo.get_by_name(self.workspace_id, tag_name)
        if tag:
            self.tag_id = tag.id
            return True
        
        self.tag_id = self.tag_repo.create(self.workspace_id, tag_name, "#3498db")
        self.log_test(f"tag.{tag_name}", "PASSED", f"Метка '{tag_name}' создана")
        return True
    
    def add_tag_to_task(self, board_name: str, tag_name: str) -> bool:
        """Добавить метку к задаче"""
        task_id = self.get_task_by_board(board_name)
        if not task_id:
            self.log_test(f"addtag.{board_name}", "FAILED", "Задача не найдена")
            return False
        
        if not self.tag_id:
            self.log_test(f"addtag.{board_name}", "FAILED", "Метка не создана")
            return False
        
        success = self.tag_repo.add_to_task(task_id, self.tag_id)
        if success:
            self.log_test(f"addtag.{board_name}", "PASSED", f"Метка '{tag_name}' добавлена")
            return True
        else:
            self.log_test(f"addtag.{board_name}", "FAILED", "Ошибка добавления метки")
            return False
    
    def check_task_tag(self, board_name: str, tag_name: str) -> bool:
        """Проверить наличие метки у задачи"""
        task_id = self.get_task_by_board(board_name)
        if not task_id:
            self.log_test(f"checktag.{board_name}", "FAILED", "Задача не найдена")
            return False
        
        tags = self.tag_repo.get_task_tags(task_id)
        tag_names = [tag.name for tag in tags]
        
        if tag_name in tag_names:
            self.log_test(f"checktag.{board_name}", "PASSED", f"Метка '{tag_name}' найдена")
            return True
        else:
            self.log_test(f"checktag.{board_name}", "FAILED", 
                        f"Метка '{tag_name}' не найдена. Найдены: {tag_names}")
            return False
    
    def run_test(self) -> bool:
        """Запуск полного теста"""
        print("\n" + "="*60)
        print("ЗАПУСК БАЗОВОГО ТЕСТА")
        print("="*60)
        
        # Этап 1: Подготовка
        if not self.setup_workspace():
            return False
        
        if not self.setup_boards():
            return False
        
        # Этап 2: Создание проекта
        if not self.create_project():
            return False
        
        # Этап 3: Работа с задачей Подготовки
        print("\n" + "="*60)
        print("ЭТАП 3: Работа с задачей Подготовки")
        print("="*60)
        
        if not self.move_task("Подготовка", "Готово"):
            return False
        
        if not self.create_field("ТЗ"):
            return False
        
        if not self.add_field_to_task(
            "Подготовка", "ТЗ",
            "https://docs.google.com/document/d/1HLqpFj26FUiLpawMCZlLD4NmSe8g7Pi2yw87Ag8SfSg/edit?usp=sharing"
        ):
            return False
        
        # Этап 4: Работа с задачей Дизайна
        print("\n" + "="*60)
        print("ЭТАП 4: Работа с задачей Дизайна")
        print("="*60)
        
        if not self.move_task("Дизайн", "План на неделю"):
            return False
        if not self.move_task("Дизайн", "В работе"):
            return False
        
        if not self.create_field("Figma"):
            return False
        
        if not self.add_field_to_task(
            "Дизайн", "Figma",
            "https://www.figma.com/design/fABhWomOv8FslEVlFsFJ1J/Krea.ai-App?node-id=15-198&p=f&t=IQpjhigMUbqBue5Q-0"
        ):
            return False
        
        if not self.move_task("Дизайн", "На утверждении"):
            return False
        
        # Этап 5: Проверка эпика проекта
        print("\n" + "="*60)
        print("ЭТАП 5: Проверка эпика проекта")
        print("="*60)
        
        expected_fields = {
            "ТЗ": "https://docs.google.com/document/d/1HLqpFj26FUiLpawMCZlLD4NmSe8g7Pi2yw87Ag8SfSg/edit?usp=sharing",
            "Figma": "https://www.figma.com/design/fABhWomOv8FslEVlFsFJ1J/Krea.ai-App?node-id=15-198&p=f&t=IQpjhigMUbqBue5Q-0"
        }
        
        # Проверить на любой задаче проекта (синхронизация)
        if not self.check_task_fields("Дизайн", expected_fields):
            return False
        
        # Этап 6: Работа с задачей Разработки
        print("\n" + "="*60)
        print("ЭТАП 6: Работа с задачей Разработки")
        print("="*60)
        
        expected_fields_all = {
            "ТЗ": "https://docs.google.com/document/d/1HLqpFj26FUiLpawMCZlLD4NmSe8g7Pi2yw87Ag8SfSg/edit?usp=sharing",
            "Figma": "https://www.figma.com/design/fABhWomOv8FslEVlFsFJ1J/Krea.ai-App?node-id=15-198&p=f&t=IQpjhigMUbqBue5Q-0"
        }
        
        if not self.check_task_fields("Разработка", expected_fields_all):
            return False
        
        if not self.move_task("Разработка", "План на неделю"):
            return False
        if not self.move_task("Разработка", "В работе"):
            return False
        
        if not self.create_field("GitHub"):
            return False
        
        if not self.add_field_to_task("Разработка", "GitHub", "https://github.com/"):
            return False
        
        if not self.move_task("Разработка", "Тестирование"):
            return False
        
        # Этап 7: Работа с задачей Тестирования
        print("\n" + "="*60)
        print("ЭТАП 7: Работа с задачей Тестирования")
        print("="*60)
        
        expected_fields_testing = {
            "ТЗ": "https://docs.google.com/document/d/1HLqpFj26FUiLpawMCZlLD4NmSe8g7Pi2yw87Ag8SfSg/edit?usp=sharing",
            "Figma": "https://www.figma.com/design/fABhWomOv8FslEVlFsFJ1J/Krea.ai-App?node-id=15-198&p=f&t=IQpjhigMUbqBue5Q-0",
            "GitHub": "https://github.com/"
        }
        
        if not self.check_task_fields("Тестирование", expected_fields_testing):
            return False
        
        if not self.move_task("Тестирование", "В работе"):
            return False
        
        if not self.create_field("Баг-репорт"):
            return False
        
        if not self.add_field_to_task(
            "Тестирование", "Баг-репорт",
            "https://drive.google.com/drive/folders/1H-PawR5k6T24MQ_HnkloaXP1eGnnQImd?hl=ru"
        ):
            return False
        
        if not self.move_task("Тестирование", "Реджект"):
            return False
        
        # Этап 8: Возврат к задаче Разработки
        print("\n" + "="*60)
        print("ЭТАП 8: Возврат к задаче Разработки")
        print("="*60)
        
        expected_fields_dev = {
            "ТЗ": "https://docs.google.com/document/d/1HLqpFj26FUiLpawMCZlLD4NmSe8g7Pi2yw87Ag8SfSg/edit?usp=sharing",
            "Figma": "https://www.figma.com/design/fABhWomOv8FslEVlFsFJ1J/Krea.ai-App?node-id=15-198&p=f&t=IQpjhigMUbqBue5Q-0",
            "GitHub": "https://github.com/",
            "Баг-репорт": "https://drive.google.com/drive/folders/1H-PawR5k6T24MQ_HnkloaXP1eGnnQImd?hl=ru"
        }
        
        if not self.check_task_fields("Разработка", expected_fields_dev):
            return False
        
        # Проверить колонку задачи Разработки
        task_id = self.get_task_by_board("Разработка")
        if task_id:
            task = self.task_service.get_task(task_id)
            column = self.column_repo.get_by_id(task.column_id)
            if column and column.name != "Фикс Багов":
                if not self.move_task("Разработка", "Фикс Багов"):
                    return False
        
        if not self.move_task("Разработка", "Готово"):
            return False
        if not self.move_task("Разработка", "Отправленно AppConnect"):
            return False
        
        # Этап 9: Работа с задачей Store
        print("\n" + "="*60)
        print("ЭТАП 9: Работа с задачей Store")
        print("="*60)
        
        if not self.move_task("Store", "В работе"):
            return False
        if not self.move_task("Store", "На модерации"):
            return False
        if not self.move_task("Store", "Реджект"):
            return False
        if not self.move_task("Store", "Опубликовано"):
            return False
        
        if not self.create_tag("И1"):
            return False
        
        if not self.add_tag_to_task("Store", "И1"):
            return False
        
        # Этап 10: Финальная проверка
        print("\n" + "="*60)
        print("ЭТАП 10: Финальная проверка")
        print("="*60)
        
        if not self.check_task_fields("Store", expected_fields_dev):
            return False
        
        if not self.check_task_tag("Store", "И1"):
            return False
        
        # Итоговый отчет
        self.print_summary()
        return True
    
    def print_summary(self):
        """Вывести итоговый отчет"""
        print("\n" + "="*60)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        
        for result in self.test_results:
            icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{icon} {result['step']}: {result['message']}")
        
        print("\n" + "-"*60)
        print(f"Всего шагов: {len(self.test_results)}")
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Провалено: {failed}")
        print("="*60)


def run_base_case_test(db_path: str = None, user_id: int = 12345) -> bool:
    """
    Запуск базового теста
    
    Args:
        db_path: Путь к БД (если None, используется Config.DATABASE_PATH)
        user_id: ID пользователя для теста
    
    Returns:
        True если все тесты пройдены, False иначе
    """
    from config import Config
    from database import Database
    
    if db_path is None:
        db_path = Config.DATABASE_PATH
    
    db = Database(db_path=db_path)
    db.init_db()
    
    runner = BaseCaseTestRunner(db, user_id)
    return runner.run_test()


if __name__ == "__main__":
    # Запуск теста
    success = run_base_case_test()
    exit(0 if success else 1)


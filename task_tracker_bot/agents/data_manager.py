"""
ADM (Agent Data Manager) - работа с базой данных через сервисы
"""

import sys
import os
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent

# Добавляем путь к корню проекта для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from services.project_service import ProjectService
from services.task_service import TaskService
from services.board_service import BoardService
from services.statistics_service import StatisticsService
from repositories.custom_field_repository import CustomFieldRepository
from repositories.project_repository import ProjectRepository
from repositories.task_repository import TaskRepository
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from repositories.personal_task_repository import PersonalTaskRepository
from database import Database


class DataManagerAgent(BaseAgent):
    """Agent Data Manager - единственная точка доступа к БД через сервисы"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, 
                 db: Optional[Database] = None):
        """
        Args:
            api_key: API ключ io.net
            model: Модель для использования
            db: Экземпляр Database для работы с БД
        """
        super().__init__(api_key, model)
        self.db = db or Database()
        
        # Инициализация репозиториев
        self.project_repo = ProjectRepository(self.db)
        self.task_repo = TaskRepository(self.db)
        self.board_repo = BoardRepository(self.db)
        self.column_repo = ColumnRepository(self.db)
        self.field_repo = CustomFieldRepository(self.db)
        self.personal_task_repo = PersonalTaskRepository(self.db)
        
        # Инициализация сервисов
        self.project_service = ProjectService(
            self.project_repo, self.board_repo, self.column_repo, self.task_repo
        )
        self.task_service = TaskService(self.task_repo, self.column_repo)
        self.board_service = BoardService(self.board_repo, self.column_repo)
        self.stats_service = StatisticsService(
            self.task_repo, self.project_repo, self.board_repo, None, self.column_repo
        )
        
        # Инициализация TodoService для работы с туду-листом
        from services.todo_service import TodoService
        from utils.date_parser import DateParser
        from utils.task_classifier import TaskClassifier
        
        date_parser = DateParser()
        task_classifier = TaskClassifier(self.project_repo)
        self.todo_service = TodoService(
            self.personal_task_repo,
            self.task_repo,
            self.project_repo,
            self.column_repo,
            self.board_repo,
            date_parser,
            task_classifier
        )
    
    def get_system_prompt(self) -> str:
        return """Ты Agent Data Manager (ADM) системы PMAssist.

Твоя задача:
1. Предоставлять доступ к данным через сервисы
2. Обеспечивать консистентность данных
3. Изолировать логику работы с данными

НОВЫЙ ФУНКЦИОНАЛ - Todo List:
4. Работать с таблицей personal_tasks для личных задач
5. Поддерживать поля scheduled_date, scheduled_time, scheduled_time_end в tasks
6. Создавать задачи с датами выполнения

Доступные операции:
- create_project, get_project, update_project
- create_task, get_task, update_task, delete_task
- create_personal_task, get_personal_tasks_by_date, mark_personal_task_completed  // НОВОЕ
- create_board, get_board
- create_column, get_column
- И другие операции с БД

Формат ответа (JSON):
{
  "status": "success|error",
  "message": "...",
  "data": {...}
}

Важно:
- Всегда проверяй существование связанных сущностей (project_id, column_id)
- Валидируй формат данных перед записью
- Возвращай понятные сообщения об ошибках

Все операции выполняются через сервисы, не напрямую с БД."""
    
    def get_next_project_id(self, workspace_id: int) -> Dict[str, Any]:
        """
        Получить следующий свободный ID проекта
        
        Args:
            workspace_id: ID пространства
            
        Returns:
            Результат с следующим ID проекта
        """
        try:
            projects = self.project_service.list_projects(workspace_id)
            
            # Найти максимальный числовой ID
            max_id = 0
            for project in projects:
                try:
                    project_num = int(project.id)
                    if project_num > max_id:
                        max_id = project_num
                except ValueError:
                    continue
            
            next_id = str(max_id + 1)
            
            return {
                "status": "success",
                "next_project_id": next_id,
                "message": f"Следующий свободный ID проекта: {next_id}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при получении следующего ID проекта: {str(e)}"
            }
    
    def create_project(self, project_id: str, workspace_id: int, name: str) -> Dict[str, Any]:
        """
        Создать проект через ProjectService
        
        Args:
            project_id: ID проекта
            workspace_id: ID пространства
            name: Название проекта
            
        Returns:
            Результат создания проекта
        """
        try:
            success, created_id, error = self.project_service.create_project(
                project_id, workspace_id, name
            )
            
            if success:
                project = self.project_service.get_project(created_id)
                return {
                    "status": "success",
                    "message": f"Проект {created_id} создан успешно",
                    "data": {
                        "id": created_id,
                        "name": name,
                        "workspace_id": workspace_id
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": error or "Ошибка при создании проекта"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при создании проекта: {str(e)}"
            }
    
    def add_project_link(self, project_id: str, link_type: str, url: str, 
                        workspace_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Добавить ссылку к проекту через custom_fields
        
        Args:
            project_id: ID проекта
            link_type: Тип ссылки (ТЗ, Референс, Figma и т.д.)
            url: URL ссылки
            workspace_id: ID пространства (если не указан, получается из проекта)
            
        Returns:
            Результат добавления ссылки
        """
        try:
            # Получить проект для определения workspace_id
            project = self.project_service.get_project(project_id)
            if not project:
                return {
                    "status": "error",
                    "message": f"Проект {project_id} не найден"
                }
            
            if not workspace_id:
                workspace_id = project.workspace_id
            
            # Получить или создать поле для ссылки
            field_name = f"Ссылка {link_type}"
            field = self.field_repo.get_by_name(workspace_id, field_name)
            
            if not field:
                # Создать поле типа url
                field_id = self.field_repo.create(workspace_id, field_name, "url")
                field = self.field_repo.get_by_id(field_id)
            
            # Получить задачи проекта
            tasks = self.task_service.list_tasks_by_project(project_id)
            
            if not tasks:
                return {
                    "status": "error",
                    "message": f"У проекта {project_id} нет задач для добавления ссылки"
                }
            
            # Добавить ссылку к первой задаче проекта (или ко всем задачам)
            # Обычно ссылки добавляются к задаче на доске "Подготовка"
            added_to_tasks = []
            for task in tasks:
                # Проверяем, что задача на нужной доске (можно добавить фильтр)
                self.field_repo.set_task_field(task.id, field.id, url)
                added_to_tasks.append(task.id)
            
            return {
                "status": "success",
                "message": f"Ссылка {link_type} добавлена к проекту {project_id}",
                "data": {
                    "project_id": project_id,
                    "link_type": link_type,
                    "url": url,
                    "field_id": field.id,
                    "tasks_updated": added_to_tasks
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при добавлении ссылки: {str(e)}"
            }
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить проект
        
        Args:
            project_id: ID проекта
            
        Returns:
            Данные проекта или None
        """
        try:
            project = self.project_service.get_project(project_id)
            if project:
                return {
                    "id": project.id,
                    "name": project.name,
                    "workspace_id": project.workspace_id,
                    "dashboard_stage": project.dashboard_stage
                }
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении проекта: {e}")
            return None
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить задачу
        
        Args:
            task_id: ID задачи
            
        Returns:
            Данные задачи или None
        """
        try:
            task = self.task_service.get_task(task_id)
            if task:
                column = self.column_repo.get_by_id(task.column_id)
                board = None
                if column:
                    board = self.board_repo.get_by_id(column.board_id)
                
                return {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "project_id": task.project_id,
                    "column_id": task.column_id,
                    "board_id": board.id if board else None,
                    "board_name": board.name if board else None,
                    "board_type": None,  # Можно добавить поле типа доски
                    "status": "done" if task.completed_at else ("in_progress" if task.started_at else "queued"),
                    "priority": task.priority
                }
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении задачи: {e}")
            return None
    
    def update_task(self, task_id: int, status: Optional[str] = None, 
                   **kwargs) -> Dict[str, Any]:
        """
        Обновить задачу
        
        Args:
            task_id: ID задачи
            status: Статус задачи (done, in_progress, queued)
            **kwargs: Другие параметры для обновления
            
        Returns:
            Результат обновления
        """
        try:
            task = self.task_service.get_task(task_id)
            if not task:
                return {
                    "status": "error",
                    "message": f"Задача {task_id} не найдена"
                }
            
            # Если указан статус, нужно переместить в соответствующую колонку
            if status == "done":
                # Найти колонку "Готово" на доске задачи
                column = self.column_repo.get_by_id(task.column_id)
                if column:
                    board = self.board_repo.get_by_id(column.board_id)
                    if board:
                        # Найти колонку "Готово"
                        done_column = self.column_repo.get_by_name(board.id, "Готово")
                        if done_column:
                            success, error = self.task_service.move_task(task_id, done_column.id)
                            if success:
                                return {
                                    "status": "success",
                                    "message": f"Задача {task_id} перемещена в Готово"
                                }
                            else:
                                return {
                                    "status": "error",
                                    "message": error or "Ошибка при перемещении задачи"
                                }
            
            # Обновление других полей
            success, error = self.task_service.update_task(task_id, **kwargs)
            if success:
                return {
                    "status": "success",
                    "message": f"Задача {task_id} обновлена"
                }
            else:
                return {
                    "status": "error",
                    "message": error or "Ошибка при обновлении задачи"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при обновлении задачи: {str(e)}"
            }
    
    def get_tasks_by_board_name(self, board_name: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получить задачи по названию доски
        
        Args:
            board_name: Название доски
            project_id: ID проекта (опционально, для фильтрации)
            
        Returns:
            Список задач
        """
        try:
            tasks = []
            
            # Если указан project_id, получить задачи проекта
            if project_id:
                project_tasks = self.task_service.list_tasks_by_project(project_id)
                for task in project_tasks:
                    column = self.column_repo.get_by_id(task.column_id)
                    if column:
                        board = self.board_repo.get_by_id(column.board_id)
                        if board and board.name.lower() == board_name.lower():
                            tasks.append({
                                "id": task.id,
                                "title": task.title,
                                "board_name": board.name,
                                "column_id": task.column_id
                            })
            else:
                # Получить все задачи со всех досок с таким именем
                # Это требует workspace_id, поэтому лучше использовать project_id
                pass
            
            return tasks
        except Exception as e:
            self.logger.error(f"Ошибка при получении задач по доске: {e}")
            return []
    
    def get_project_boards(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Получить доски проекта
        
        Args:
            project_id: ID проекта
            
        Returns:
            Список досок
        """
        try:
            project = self.project_service.get_project(project_id)
            if not project:
                return []
            
            boards = self.board_service.list_boards(project.workspace_id)
            return [
                {
                    "id": board.id,
                    "name": board.name,
                    "type": None,  # Можно добавить поле типа доски
                    "workspace_id": board.workspace_id
                }
                for board in boards
            ]
        except Exception as e:
            self.logger.error(f"Ошибка при получении досок проекта: {e}")
            return []
    
    def get_task_links(self, task_id: int) -> List[Dict[str, Any]]:
        """
        Получить ссылки задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Список ссылок
        """
        try:
            task = self.task_service.get_task(task_id)
            if not task:
                return []
            
            # Получить workspace_id из задачи
            workspace_id = None
            if task.project_id:
                project = self.project_service.get_project(task.project_id)
                if project:
                    workspace_id = project.workspace_id
            else:
                column = self.column_repo.get_by_id(task.column_id)
                if column:
                    board = self.board_repo.get_by_id(column.board_id)
                    if board:
                        workspace_id = board.workspace_id
            
            if not workspace_id:
                return []
            
            # Получить все поля типа url для задачи
            task_fields = self.field_repo.get_task_fields(task_id)
            links = []
            
            for field_id, value in task_fields.items():
                field = self.field_repo.get_by_id(field_id)
                if field and field.field_type == "url":
                    # Извлечь тип ссылки из названия поля
                    link_type = field.name.replace("Ссылка ", "")
                    links.append({
                        "type": link_type,
                        "url": value,
                        "field_id": field_id
                    })
            
            return links
        except Exception as e:
            self.logger.error(f"Ошибка при получении ссылок задачи: {e}")
            return []
    
    def create_personal_task(
        self,
        user_id: int,
        title: str,
        scheduled_date,
        scheduled_time=None,
        scheduled_time_end=None,
        deadline=None,
        description=None
    ) -> Dict[str, Any]:
        """
        Создать личную задачу
        
        Returns:
            {
                "status": "success",
                "message": "Личная задача создана",
                "data": {"id": 1, "title": "..."}
            }
        """
        try:
            from datetime import date, time, datetime
            
            # Преобразование строк в объекты даты/времени если нужно
            if isinstance(scheduled_date, str):
                scheduled_date = datetime.fromisoformat(scheduled_date).date()
            if scheduled_time and isinstance(scheduled_time, str):
                scheduled_time = datetime.strptime(scheduled_time, "%H:%M").time()
            if scheduled_time_end and isinstance(scheduled_time_end, str):
                scheduled_time_end = datetime.strptime(scheduled_time_end, "%H:%M").time()
            if deadline and isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            
            task_id = self.personal_task_repo.create(
                user_id=user_id,
                title=title,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                scheduled_time_end=scheduled_time_end,
                deadline=deadline,
                description=description
            )
            
            return {
                "status": "success",
                "message": "Личная задача создана",
                "data": {"id": task_id, "title": title}
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при создании личной задачи: {str(e)}"
            }
    
    def get_personal_tasks_by_date(
        self,
        user_id: int,
        target_date
    ) -> Dict[str, Any]:
        """
        Получить личные задачи на указанную дату
        
        Returns:
            {
                "status": "success",
                "data": [PersonalTask, ...]
            }
        """
        try:
            from datetime import date, datetime
            
            if isinstance(target_date, str):
                target_date = datetime.fromisoformat(target_date).date()
            
            tasks = self.personal_task_repo.get_by_date(user_id, target_date)
            
            return {
                "status": "success",
                "data": tasks
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при получении задач: {str(e)}"
            }
    
    def mark_personal_task_completed(
        self,
        task_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Отметить личную задачу как выполненную
        
        Returns:
            {
                "status": "success",
                "message": "Задача отмечена как выполненная"
            }
        """
        try:
            success = self.personal_task_repo.mark_completed(task_id, user_id)
            if success:
                return {
                    "status": "success",
                    "message": "Задача отмечена как выполненная"
                }
            else:
                return {
                    "status": "error",
                    "message": "Задача не найдена или уже выполнена"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при отметке задачи: {str(e)}"
            }
    
    def create_todo_batch(
        self,
        workspace_id: int,
        user_id: int,
        tasks: List[Dict[str, Any]],
        default_date=None
    ) -> Dict[str, Any]:
        """
        Создать пакет задач через TodoService
        
        Args:
            workspace_id: ID пространства
            user_id: ID пользователя
            tasks: Список задач из entities.tasks
            default_date: Дата по умолчанию
        
        Returns:
            Результат создания пакета задач
        """
        try:
            from datetime import date, datetime
            
            # Преобразование default_date если нужно
            if default_date and isinstance(default_date, str):
                default_date = datetime.fromisoformat(default_date).date()
            
            # Преобразование списка задач в текст для парсинга
            tasks_text = "\n".join([
                f"{i+1}. {task.get('text', '')}" 
                for i, task in enumerate(tasks)
            ])
            
            result = self.todo_service.create_todo_batch(
                tasks_text=tasks_text,
                workspace_id=workspace_id,
                user_id=user_id,
                default_date=default_date
            )
            
            return {
                "status": result["status"],
                "message": f"Создано {len(result['personal_tasks_created'])} личных и {len(result['work_tasks_created'])} рабочих задач",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при создании пакета задач: {str(e)}"
            }
    
    def create_task(
        self,
        column_id: int,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        scheduled_date=None,
        scheduled_time=None,
        scheduled_time_end=None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создать задачу с поддержкой scheduled_date, scheduled_time
        
        Returns:
            Результат создания задачи
        """
        try:
            from datetime import date, time, datetime
            
            # Преобразование строк в объекты даты/времени если нужно
            if scheduled_date and isinstance(scheduled_date, str):
                scheduled_date = datetime.fromisoformat(scheduled_date).date()
            if scheduled_time and isinstance(scheduled_time, str):
                scheduled_time = datetime.strptime(scheduled_time, "%H:%M").time()
            if scheduled_time_end and isinstance(scheduled_time_end, str):
                scheduled_time_end = datetime.strptime(scheduled_time_end, "%H:%M").time()
            
            success, task_id, error = self.task_service.create_task(
                column_id=column_id,
                title=title,
                description=description,
                project_id=project_id,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                scheduled_time_end=scheduled_time_end,
                **kwargs
            )
            
            if success:
                return {
                    "status": "success",
                    "message": f"Задача создана",
                    "data": {"id": task_id, "title": title}
                }
            else:
                return {
                    "status": "error",
                    "message": error or "Ошибка при создании задачи"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при создании задачи: {str(e)}"
            }


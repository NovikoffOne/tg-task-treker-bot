"""
Сервис для работы с Todo List
"""
import re
import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional
from repositories.personal_task_repository import PersonalTaskRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from utils.date_parser import DateParser
from utils.task_classifier import TaskClassifier

logger = logging.getLogger(__name__)

class TodoService:
    """Сервис для работы с туду-листом"""
    
    def __init__(
        self,
        personal_task_repo: PersonalTaskRepository,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        column_repo: ColumnRepository,
        board_repo: BoardRepository,
        date_parser: DateParser,
        task_classifier: TaskClassifier
    ):
        self.personal_task_repo = personal_task_repo
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.column_repo = column_repo
        self.board_repo = board_repo
        self.date_parser = date_parser
        self.task_classifier = task_classifier
    
    def create_todo_batch(
        self,
        tasks_text: str,
        workspace_id: int,
        user_id: int,
        default_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Создает пакет задач из текста
        
        Args:
            tasks_text: Текст с задачами (нумерованный список)
            workspace_id: ID пространства
            user_id: ID пользователя
            default_date: Дата по умолчанию (если не указана в задаче)
        
        Returns:
            {
                "status": "success",
                "personal_tasks_created": [...],
                "work_tasks_created": [...],
                "errors": [...]
            }
        """
        if not default_date:
            default_date = datetime.now().date()
        
        logger.info(
            f"Создание пакета задач: workspace_id={workspace_id}, "
            f"user_id={user_id}, default_date={default_date}, "
            f"tasks_text_length={len(tasks_text)}"
        )
        
        personal_tasks_created = []
        work_tasks_created = []
        errors = []
        
        # Разбиение текста на отдельные задачи
        tasks_list = self._parse_task_list(tasks_text)
        logger.debug(f"Распарсено задач из текста: {len(tasks_list)}")
        
        for idx, task_text in enumerate(tasks_list, 1):
            try:
                logger.debug(f"Обработка задачи {idx}/{len(tasks_list)}: '{task_text}'")
                
                # Извлечение даты и времени из задачи
                datetime_info = self.date_parser.parse_datetime_from_task(
                    task_text,
                    default_date
                )
                
                task_date = datetime_info["date"]
                task_time = datetime_info["time"]
                task_time_end = datetime_info["time_end"]
                cleaned_text = datetime_info["remaining_text"]
                
                logger.debug(
                    f"Извлечено из задачи: date={task_date}, "
                    f"time={task_time}, time_end={task_time_end}, "
                    f"cleaned_text='{cleaned_text}'"
                )
                
                # Классификация задачи
                classification = self.task_classifier.classify_task(
                    cleaned_text,
                    workspace_id
                )
                
                logger.debug(
                    f"Классификация задачи: type={classification.get('type')}, "
                    f"title='{classification.get('title')}', "
                    f"project_id={classification.get('project_id')}"
                )
                
                if classification["type"] == "personal":
                    # Создание личной задачи
                    logger.info(f"Создание личной задачи: '{classification['title']}' на {task_date}")
                    
                    # Обработка множественного времени
                    times = self._extract_multiple_times(task_text)
                    
                    if times:
                        logger.debug(f"Обнаружено множественное время: {times}, создаем {len(times)} задач")
                        # Создаем отдельные задачи для каждого времени
                        for t in times:
                            task_id = self.personal_task_repo.create(
                                user_id=user_id,
                                title=classification["title"],
                                scheduled_date=task_date,
                                scheduled_time=t,
                                description=classification.get("description")
                            )
                            logger.info(f"Создана личная задача: id={task_id}, title='{classification['title']}', date={task_date}, time={t}")
                            personal_tasks_created.append({
                                "id": task_id,
                                "title": classification["title"],
                                "date": task_date.isoformat(),
                                "time": t.isoformat()
                            })
                    else:
                        # Одна задача с временем или без
                        task_id = self.personal_task_repo.create(
                            user_id=user_id,
                            title=classification["title"],
                            scheduled_date=task_date,
                            scheduled_time=task_time,
                            scheduled_time_end=task_time_end,
                            description=classification.get("description")
                        )
                        logger.info(
                            f"Создана личная задача: id={task_id}, title='{classification['title']}', "
                            f"date={task_date}, time={task_time}, time_end={task_time_end}"
                        )
                        personal_tasks_created.append({
                            "id": task_id,
                            "title": classification["title"],
                            "date": task_date.isoformat(),
                            "time": task_time.isoformat() if task_time else None,
                            "time_end": task_time_end.isoformat() if task_time_end else None
                        })
                
                elif classification["type"] == "work":
                    # Создание рабочей задачи
                    project_id = classification["project_id"]
                    logger.info(f"Создание рабочей задачи: '{classification['title']}' для проекта {project_id} на {task_date}")
                    
                    # Получаем проект
                    project = self.project_repo.get_by_id(project_id)
                    if not project:
                        error_msg = f"Проект {project_id} не найден"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
                    
                    # Получаем первую колонку первой доски workspace
                    # Используем подход из ProjectService - ищем доску "Подготовка" или первую доску
                    # Ищем доску "Подготовка"
                    preparation_board = self.board_repo.get_by_name(workspace_id, "Подготовка")
                    if not preparation_board:
                        # Если нет доски "Подготовка", берем первую доску
                        boards = self.board_repo.get_all_by_workspace(workspace_id)
                        if not boards:
                            errors.append(f"Не найдены доски для workspace {workspace_id}")
                            continue
                        preparation_board = boards[0]
                    
                    # Получаем первую колонку доски
                    first_column = self.column_repo.get_first_by_board(preparation_board.id)
                    if not first_column:
                        errors.append(f"Не найдены колонки для доски {preparation_board.id}")
                        continue
                    
                    column_id = first_column.id
                    
                    task_id = self.task_repo.create(
                        column_id=column_id,
                        title=classification["title"],
                        description=classification.get("description"),
                        project_id=project_id,
                        scheduled_date=task_date,
                        scheduled_time=task_time,
                        scheduled_time_end=task_time_end
                    )
                    
                    logger.info(
                        f"Создана рабочая задача: id={task_id}, title='{classification['title']}', "
                        f"project_id={project_id}, column_id={column_id}, "
                        f"date={task_date}, time={task_time}"
                    )
                    
                    work_tasks_created.append({
                        "id": task_id,
                        "title": classification["title"],
                        "project_id": project_id,
                        "date": task_date.isoformat(),
                        "time": task_time.isoformat() if task_time else None
                    })
            
            except Exception as e:
                error_msg = f"Ошибка при создании задачи '{task_text}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        result = {
            "status": "success" if not errors else "partial",
            "personal_tasks_created": personal_tasks_created,
            "work_tasks_created": work_tasks_created,
            "errors": errors
        }
        
        logger.info(
            f"Пакет задач создан: status={result['status']}, "
            f"личных={len(personal_tasks_created)}, "
            f"рабочих={len(work_tasks_created)}, "
            f"ошибок={len(errors)}"
        )
        
        return result
    
    def get_todo_list(
        self,
        user_id: int,
        target_date: date,
        include_work_tasks: bool = True
    ) -> Dict[str, Any]:
        """
        Получает туду-лист на указанную дату
        
        Args:
            user_id: ID пользователя
            target_date: Дата для отображения
            include_work_tasks: Включать ли рабочие задачи
        
        Returns:
            {
                "date": "29.11.2025",
                "personal_tasks": [...],
                "work_tasks": [...],
                "grouped_by_time": {...}
            }
        """
        # Получение личных задач
        personal_tasks = self.personal_task_repo.get_by_date(user_id, target_date)
        
        # Получение рабочих задач (если нужно)
        work_tasks = []
        if include_work_tasks:
            # Получаем все задачи с scheduled_date на эту дату
            # Фильтруем только те, которые связаны с проектами пользователя
            work_tasks = self.task_repo.get_by_scheduled_date(target_date)
        
        # Группировка по времени
        grouped_by_time = self._group_tasks_by_time(personal_tasks, work_tasks)
        
        return {
            "date": target_date.strftime("%d.%m.%Y"),
            "personal_tasks": personal_tasks,
            "work_tasks": work_tasks,
            "grouped_by_time": grouped_by_time
        }
    
    def mark_personal_task_completed(
        self,
        task_id: int,
        user_id: int
    ) -> tuple[bool, Optional[str]]:
        """
        Отметить личную задачу как выполненную
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            success = self.personal_task_repo.mark_completed(task_id, user_id)
            if success:
                return (True, None)
            else:
                return (False, "Задача не найдена или уже выполнена")
        except Exception as e:
            logger.error(f"Ошибка при отметке задачи {task_id}: {e}", exc_info=True)
            return (False, str(e))
    
    def _parse_task_list(self, tasks_text: str) -> List[str]:
        """Разбить текст на отдельные задачи"""
        tasks = []
        
        logger.debug(f"Парсинг списка задач из текста длиной {len(tasks_text)} символов")
        
        # Разбиение по нумерации (1., 2., и т.д.)
        lines = tasks_text.split('\n')
        current_task = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Проверка на начало новой задачи (цифра с точкой)
            if re.match(r'^\d+[\.\)]\s*', line):
                if current_task:
                    tasks.append(' '.join(current_task))
                current_task = [re.sub(r'^\d+[\.\)]\s*', '', line)]
            else:
                current_task.append(line)
        
        if current_task:
            tasks.append(' '.join(current_task))
        
        logger.debug(f"Распарсено {len(tasks)} задач из текста")
        return tasks
    
    def _extract_multiple_times(self, text: str) -> List[time]:
        """Извлечь множественное время из текста (например, "10:00 и 19:00")"""
        times = []
        
        # Паттерн для поиска времени
        time_pattern = r'(\d{1,2}):(\d{2})'
        matches = re.findall(time_pattern, text)
        
        # Проверка на наличие слова "и" между временами
        if ' и ' in text.lower() or ', ' in text:
            for match in matches:
                hour = int(match[0])
                minute = int(match[1])
                if 0 <= hour < 24 and 0 <= minute < 60:
                    times.append(time(hour, minute))
        
        return times if len(times) > 1 else []
    
    def _group_tasks_by_time(
        self,
        personal_tasks: List,
        work_tasks: List
    ) -> Dict[str, List]:
        """Группировка задач по времени"""
        grouped = {}
        
        # Группировка личных задач
        for task in personal_tasks:
            time_key = task.time_display if task.time_display else "без времени"
            if time_key not in grouped:
                grouped[time_key] = {"personal": [], "work": []}
            grouped[time_key]["personal"].append(task)
        
        # Группировка рабочих задач
        for task in work_tasks:
            if task.scheduled_time:
                time_key = task.scheduled_time.strftime("%H:%M")
                if task.scheduled_time_end:
                    time_key += f" - {task.scheduled_time_end.strftime('%H:%M')}"
            else:
                time_key = "без времени"
            
            if time_key not in grouped:
                grouped[time_key] = {"personal": [], "work": []}
            grouped[time_key]["work"].append(task)
        
        return grouped


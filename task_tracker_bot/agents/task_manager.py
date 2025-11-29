"""
ATM (Agent Task Manager) - управление задачами и проектами
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TaskManagerAgent(BaseAgent):
    """Управление задачами - создание, модерация, валидация"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, data_manager=None):
        """
        Args:
            api_key: API ключ io.net
            model: Модель для использования
            data_manager: Экземпляр DataManagerAgent для работы с БД
        """
        super().__init__(api_key, model)
        self.data_manager = data_manager
    
    def get_system_prompt(self) -> str:
        return """Ты Agent Task Manager (ATM) системы PMAssist.

Твоя задача:
1. Создавать и обновлять задачи и проекты
2. Проверять наличие обязательных данных перед созданием
3. Валидировать корректность данных
4. Отправлять уведомления о дедлайнах

НОВЫЙ ФУНКЦИОНАЛ - Todo List:
5. Создавать пакеты задач (личные + рабочие)
6. Определять тип задач по наличию project_id
7. Использовать DateParser для извлечения дат и времени
8. Использовать TaskClassifier для определения типа задачи

Все операции с БД выполняй через ADM (Agent Data Manager).

Правила:
- При создании проекта автоматически создавай стандартные доски:
  Backend, Design, Dev, Test, Accountant, ASO
- Проверяй, что у задачи назначены все необходимые роли
- При закрытии задачи на доске "Подготовка" создавай задачу на доске "Дизайн"

НОВЫЕ ПРАВИЛА для Todo List:
- Личные задачи (без project_id) → создавать через ADM.create_personal_task
- Рабочие задачи (с project_id) → создавать через ADM.create_task с project_id и scheduled_date
- Если в задаче указано несколько времен ("10:00 и 19:00") → создавать отдельные задачи
- Если указан диапазон времени ("11:10 - 12:00") → сохранять time_start и time_end

Формат ответа (JSON):
{
  "status": "success|error",
  "message": "...",
  "data": {
    "personal_tasks_created": [{"id": 1, "title": "..."}],
    "work_tasks_created": [{"id": 2, "title": "...", "project_id": "5001"}],
    "errors": []
  }
}"""
    
    def create_project(
        self,
        workspace_id: int,
        project_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает новый проект
        
        Args:
            workspace_id: ID пространства (workspace)
            project_id: ID проекта (например, "5005")
            name: Название проекта
            description: Описание проекта (не используется пока)
        
        Returns:
            Результат создания проекта
        """
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        # Создание проекта через ADM
        result = self.data_manager.create_project(
            project_id=project_id,
            workspace_id=workspace_id,
            name=name
        )
        
        return result
    
    def add_link_to_project(
        self,
        project_id: str,
        link_type: str,
        url: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Добавляет ссылку к проекту
        
        Args:
            project_id: ID проекта
            link_type: Тип ссылки (ТЗ, Референс, Figma, и т.д.)
            url: URL ссылки
            name: Название ссылки (опционально)
        
        Returns:
            Результат добавления ссылки
        """
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        return self.data_manager.add_project_link(
            project_id=project_id,
            link_type=link_type,
            url=url,
            name=name or link_type
        )
    
    def close_task_on_board(
        self,
        board_name: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Закрывает задачу на указанной доске (переводит в статус "Готово")
        
        Args:
            board_name: Название доски (например, "Подготовка")
            project_id: ID проекта (если нужно найти задачу)
            task_id: ID задачи (если известен)
        
        Returns:
            Результат закрытия задачи
        """
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        # Поиск задачи через ADM
        if not task_id:
            tasks = self.data_manager.get_tasks_by_board_name(board_name, project_id)
            if not tasks or len(tasks) == 0:
                return {
                    "status": "error",
                    "message": f"Задачи на доске '{board_name}' не найдены"
                }
            task_id = tasks[0].get("id")
        
        # Преобразование task_id в int если это строка
        if isinstance(task_id, str):
            try:
                task_id = int(task_id)
            except ValueError:
                return {
                    "status": "error",
                    "message": f"Некорректный ID задачи: {task_id}"
                }
        
        # Обновление статуса задачи
        return self.data_manager.update_task(
            task_id=task_id,
            status="done"
        )
    
    def create_todo_batch(
        self,
        workspace_id: int,
        user_id: int,
        tasks: List[Dict[str, Any]],
        default_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Создает пакет задач (личные + рабочие)
        
        Args:
            workspace_id: ID пространства
            user_id: ID пользователя
            tasks: Список задач из entities.tasks
            default_date: Дата по умолчанию
        
        Returns:
            {
                "status": "success",
                "message": "...",
                "data": {
                    "personal_tasks_created": [...],
                    "work_tasks_created": [...],
                    "errors": [...]
                }
            }
        """
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        logger.info(
            f"TaskManagerAgent.create_todo_batch вызван: "
            f"workspace_id={workspace_id}, user_id={user_id}, "
            f"tasks_count={len(tasks)}, default_date={default_date}"
        )
        
        # Используем TodoService через data_manager
        result = self.data_manager.create_todo_batch(
            workspace_id=workspace_id,
            user_id=user_id,
            tasks=tasks,
            default_date=default_date
        )
        
        logger.info(
            f"TaskManagerAgent.create_todo_batch завершен: "
            f"status={result.get('status')}, "
            f"personal_tasks={len(result.get('data', {}).get('personal_tasks_created', []))}, "
            f"work_tasks={len(result.get('data', {}).get('work_tasks_created', []))}, "
            f"errors={len(result.get('data', {}).get('errors', []))}"
        )
        
        return result


"""
ACM (Agent Control Manager) - проверка корректности данных и бизнес-логики
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent


class ControlManagerAgent(BaseAgent):
    """Контроль корректности данных и валидация бизнес-правил"""
    
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
        return """Ты Agent Control Manager (ACM) системы PMAssist.

Твоя задача:
1. Проверять корректность данных после операций
2. Валидировать бизнес-правила и флоу
3. Проверять целостность данных

Правила проверки:
- После закрытия задачи на доске "Подготовка" должна появиться задача на доске "Дизайн"
- При переносе задачи на доске "Дизайн" в "На утверждении" должна быть ссылка на Figma
- У задачи должны быть назначены все необходимые роли (PM, дизайнер, разработчик)
- Проект должен иметь все обязательные доски
- Ссылки должны быть валидными URL

Формат ответа (JSON):
{
  "status": "valid|invalid",
  "errors": ["ошибка1", "ошибка2", ...],
  "warnings": ["предупреждение1", ...],
  "checked_items": [...]
}"""
    
    def validate_changes(
        self,
        operation_type: str,
        entity_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Проверяет корректность изменений после операции
        
        Args:
            operation_type: Тип операции (create_project, close_task, update_task, ...)
            entity_id: ID сущности (project_id, task_id, ...)
            context: Дополнительный контекст
        
        Returns:
            Результат валидации
        """
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        # Получение данных для проверки
        if operation_type == "create_project":
            return self._validate_project(entity_id, context)
        elif operation_type == "close_task":
            return self._validate_task_closed(entity_id, context)
        elif operation_type == "update_task":
            return self._validate_task_updated(entity_id, context)
        else:
            return {
                "status": "valid",
                "errors": [],
                "warnings": [f"Тип операции {operation_type} не требует специальной валидации"]
            }
    
    def _validate_project(self, project_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация проекта"""
        errors = []
        warnings = []
        
        # Получение данных проекта через ADM
        project = self.data_manager.get_project(project_id)
        if not project:
            return {
                "status": "invalid",
                "errors": [f"Проект {project_id} не найден"],
                "warnings": []
            }
        
        # Проверка наличия стандартных досок
        boards = self.data_manager.get_project_boards(project_id)
        required_boards = ["backend", "design", "dev", "test", "accountant", "aso"]
        existing_board_types = [b.get("type") for b in boards]
        
        for board_type in required_boards:
            if board_type not in existing_board_types:
                errors.append(f"Отсутствует доска типа '{board_type}'")
        
        return {
            "status": "valid" if not errors else "invalid",
            "errors": errors,
            "warnings": warnings,
            "checked_items": ["boards", "project_data"]
        }
    
    def _validate_task_closed(self, entity_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация закрытия задачи"""
        errors = []
        warnings = []
        
        # Преобразование entity_id в int
        try:
            task_id = int(entity_id)
        except ValueError:
            return {
                "status": "invalid",
                "errors": [f"Некорректный ID задачи: {entity_id}"],
                "warnings": []
            }
        
        task = self.data_manager.get_task(task_id)
        if not task:
            return {
                "status": "invalid",
                "errors": [f"Задача {task_id} не найдена"],
                "warnings": []
            }
        
        board_name = task.get("board_name", "")
        
        # Если закрыта задача на доске "Подготовка", должна появиться задача на доске "Дизайн"
        if "подготовка" in board_name.lower() or "preparation" in board_name.lower():
            project_id = task.get("project_id")
            if project_id:
                design_tasks = self.data_manager.get_tasks_by_board_name("Design", project_id)
                if not design_tasks or len(design_tasks) == 0:
                    errors.append("После закрытия задачи на доске 'Подготовка' должна появиться задача на доске 'Дизайн'")
        
        return {
            "status": "valid" if not errors else "invalid",
            "errors": errors,
            "warnings": warnings,
            "checked_items": ["task_status", "board_transitions"]
        }
    
    def _validate_task_updated(self, entity_id: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация обновления задачи"""
        errors = []
        warnings = []
        
        # Преобразование entity_id в int
        try:
            task_id = int(entity_id)
        except ValueError:
            return {
                "status": "invalid",
                "errors": [f"Некорректный ID задачи: {entity_id}"],
                "warnings": []
            }
        
        task = self.data_manager.get_task(task_id)
        if not task:
            return {
                "status": "invalid",
                "errors": [f"Задача {task_id} не найдена"],
                "warnings": []
            }
        
        board_name = task.get("board_name", "")
        status = task.get("status")
        
        # Если задача на доске "Дизайн" переведена в "На утверждении", должна быть ссылка на Figma
        if "дизайн" in board_name.lower() or "design" in board_name.lower():
            if status == "pending_approval" or "утвержден" in str(status).lower():
                links = self.data_manager.get_task_links(task_id)
                figma_links = [l for l in links if "figma" in l.get("type", "").lower()]
                
                if not figma_links:
                    errors.append("При переводе задачи на доске 'Дизайн' в 'На утверждении' должна быть ссылка на Figma")
        
        return {
            "status": "valid" if not errors else "invalid",
            "errors": errors,
            "warnings": warnings,
            "checked_items": ["task_fields", "links", "assignments"]
        }


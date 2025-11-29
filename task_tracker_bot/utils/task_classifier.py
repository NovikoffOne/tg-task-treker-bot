"""
Классификатор задач для определения типа (личная/рабочая)
"""
import re
import logging
from typing import Dict, Any, Optional
from repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)

class TaskClassifier:
    """Определение типа задачи по наличию project_id"""
    
    # Паттерны для project_id
    PROJECT_ID_PATTERNS = [
        r'^(\d{4,5})\s*[-–:]\s*(.+)',  # "5001 - текст" или "5001: текст"
        r'^(\d{4,5})\s+(.+)',  # "5001 текст"
    ]
    
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo
    
    def classify_task(
        self,
        task_text: str,
        workspace_id: int
    ) -> Dict[str, Any]:
        """
        Определяет тип задачи и извлекает project_id если есть
        
        Args:
            task_text: Текст задачи
            workspace_id: ID пространства
        
        Returns:
            {
                "type": "personal" | "work",
                "project_id": str | None,
                "title": str,  # Очищенный заголовок
                "description": str | None
            }
        """
        result = {
            "type": "personal",
            "project_id": None,
            "title": task_text.strip(),
            "description": None
        }
        
        # Поиск project_id в начале строки
        for pattern in self.PROJECT_ID_PATTERNS:
            match = re.match(pattern, task_text.strip())
            if match:
                project_id = match.group(1)
                remaining_text = match.group(2).strip()
                
                # Проверка существования проекта
                try:
                    project = self.project_repo.get_by_id(project_id)
                    if project and project.workspace_id == workspace_id:
                        result["type"] = "work"
                        result["project_id"] = project_id
                        result["title"] = remaining_text
                        logger.debug(f"Найден project_id: {project_id}, тип: work")
                        return result
                    else:
                        logger.debug(f"Проект {project_id} не найден или не принадлежит workspace {workspace_id}")
                except Exception as e:
                    logger.warning(f"Ошибка при проверке проекта {project_id}: {e}")
        
        # Если project_id не найден или проект не существует - личная задача
        result["title"] = task_text.strip()
        logger.debug(f"Тип задачи: personal")
        return result


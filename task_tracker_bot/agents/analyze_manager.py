"""
AAM (Agent Analyze Manager) - аналитика, отчеты, бизнес-анализ
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class AnalyzeManagerAgent(BaseAgent):
    """Аналитика и отчеты - быстрый доступ к данным для аналитических запросов"""
    
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
        return """Ты Agent Analyze Manager (AAM) системы PMAssist.

Твоя задача:
1. Отвечать на вопросы о метриках и статистике
2. Генерировать отчеты и графики
3. Анализировать узкие места в процессах

Используй ADM для получения данных из БД.
Форматируй ответы в удобном для пользователя виде.

Примеры запросов:
- "Сколько сейчас задач у нас в работе?"
- "Покажи график эффективности сотрудников разработки"
- "Сколько задач выполнено в этом месяце?"
- "Где у нас узкое горлышко?"

Формат ответа:
- Текстовый ответ с метриками
- Рекомендации по улучшению (если применимо)
- Данные для построения графиков (если запрошено)"""
    
    def analyze_query(self, query: str, workspace_id: int, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Анализирует запрос пользователя и возвращает метрики/отчет
        
        Args:
            query: Запрос пользователя
            workspace_id: ID пространства
            context: Дополнительный контекст
        
        Returns:
            Результат анализа с метриками
        """
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        prompt = f"""Проанализируй следующий запрос пользователя и предоставь метрики:

Запрос: {query}
Пространство: {workspace_id}

Используй данные из БД через ADM для получения актуальной информации.
Форматируй ответ в удобном для пользователя виде."""
        
        result = self.process(prompt, context)
        
        # Здесь можно добавить дополнительную обработку результата
        # Например, форматирование для графиков, вычисление метрик и т.д.
        
        return result
    
    def get_tasks_in_progress(self, workspace_id: int) -> Dict[str, Any]:
        """Получает количество задач в работе"""
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        # Реальная логика получения задач через ADM
        return {
            "metric": "tasks_in_progress",
            "value": 0,
            "message": "Задач в работе: 0"
        }
    
    def get_employee_efficiency(self, workspace_id: int, department: Optional[str] = None) -> Dict[str, Any]:
        """Получает метрики эффективности сотрудников"""
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        # Реальная логика получения метрик через ADM
        return {
            "metric": "employee_efficiency",
            "data": [],
            "message": "Метрики эффективности сотрудников"
        }
    
    def find_bottlenecks(self, workspace_id: int) -> Dict[str, Any]:
        """Находит узкие места в процессах"""
        if not self.data_manager:
            raise ValueError("DataManager не установлен")
        
        # Реальная логика анализа узких мест через ADM
        return {
            "metric": "bottlenecks",
            "bottlenecks": [],
            "message": "Анализ узких мест"
        }


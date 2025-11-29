"""
Оркестратор - главный координатор системы агентов
"""

import time
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

# Добавляем путь к корню проекта для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config


class OrchestratorAgent(BaseAgent):
    """Оркестратор анализирует запросы и координирует работу других агентов"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Инициализация оркестратора с кэшем
        
        Args:
            api_key: API ключ io.net
            model: Модель для использования
        """
        super().__init__(api_key, model)
        self.cache: Dict[str, tuple] = {}  # {normalized_message: (result, timestamp)}
        self.cache_ttl = Config.ORCHESTRATOR_CACHE_TTL
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _normalize_message(self, message: str) -> str:
        """
        Нормализует сообщение для использования в качестве ключа кэша
        
        Args:
            message: Исходное сообщение
            
        Returns:
            Нормализованное сообщение
        """
        # Приводим к нижнему регистру и убираем лишние пробелы
        normalized = " ".join(message.lower().split())
        return normalized
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """
        Проверяет, действителен ли кэш
        
        Args:
            timestamp: Временная метка записи в кэше
            
        Returns:
            True если кэш действителен, False иначе
        """
        return (time.time() - timestamp) < self.cache_ttl
    
    def clear_cache(self) -> None:
        """Очищает кэш оркестратора"""
        self.cache.clear()
        self.logger.info("Кэш оркестратора очищен")
    
    def get_system_prompt(self) -> str:
        return """Ты Оркестратор системы управления задачами PMAssist. 

Твоя задача:
1. Анализировать запросы пользователя
2. Извлекать сущности: проекты, задачи, действия, ссылки, даты, время
3. Составлять план выполнения из подзадач
4. Координировать работу специализированных агентов

Доступные агенты:
- ATM (Agent Task Manager): создание и управление задачами/проектами
- ADM (Agent Data Manager): работа с базой данных
- ACM (Agent Control Manager): проверка корректности данных
- AAM (Agent Analyze Manager): аналитика и отчеты

НОВЫЙ ФУНКЦИОНАЛ - Todo List:
- Распознавать intent "add_todo_batch" для пакетного добавления задач
- Извлекать дату из запроса: "на завтра", "на 03.12", "на сегодня"
- Разбивать нумерованный список задач на отдельные элементы
- Определять тип каждой задачи (личная/рабочая) по наличию project_id

Формат ответа (JSON):
{
  "intent": "create_project|update_task|query_data|close_task|add_todo_batch|...",
  "entities": {
    "project_id": "...",  // может быть "id+" для следующего свободного ID
    "project_name": "...",
    "task_id": "...",
    "board_name": "...",
    "date": "2025-11-30",  // НОВОЕ: дата для задач
    "tasks": [  // НОВОЕ: список задач для пакетного добавления
      {
        "text": "Выгул Феры в 10:00 и 19:00",
        "date": "2025-11-30",
        "times": ["10:00", "19:00"]
      },
      {
        "text": "5001 - Протестировать приложение",
        "date": "2025-11-30",
        "project_id": "5001"
      }
    ],
    "actions": ["create", "update", "close", ...],
    "links": [{"type": "ТЗ|Референс|Figma|...", "url": "..."}]
  },
  "plan": [
    {"agent": "ADM|ATM|ACM|AAM", "action": "...", "params": {...}},
    ...
  ]
}

Важно:
- Если project_id = "id+", нужно сначала получить следующий свободный ID через ADM
- Все операции с БД выполняются через ADM
- После изменений всегда проверяй через ACM
- План должен быть последовательным и логичным
- Для add_todo_batch используй ATM.create_todo_batch"""
    
    def analyze_request(self, user_message: str) -> Dict[str, Any]:
        """
        Анализирует запрос пользователя и составляет план с кэшированием
        
        Args:
            user_message: Сообщение от пользователя
        
        Returns:
            Результат анализа с планом выполнения
        """
        # Нормализуем сообщение для кэша
        normalized = self._normalize_message(user_message)
        
        # Проверяем кэш
        if normalized in self.cache:
            cached_result, timestamp = self.cache[normalized]
            if self._is_cache_valid(timestamp):
                self.logger.info(f"Кэш попадание для запроса: {user_message[:50]}...")
                return cached_result
            else:
                # Кэш устарел, удаляем
                del self.cache[normalized]
                self.logger.debug(f"Кэш устарел для запроса: {user_message[:50]}...")
        
        # Кэш промах или устарел - выполняем запрос
        self.logger.debug(f"Кэш промах для запроса: {user_message[:50]}...")
        prompt = f"""Проанализируй следующий запрос пользователя и составь план выполнения:

Запрос: {user_message}

ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста, markdown разметки или комментариев.

Формат ответа (строго JSON):
{{
  "intent": "create_project|update_task|query_data|close_task|add_todo_batch|...",
  "entities": {{
    "project_id": "...",
    "project_name": "...",
    "task_id": "...",
    "board_name": "...",
    "date": "2025-11-30",
    "tasks": [...]
  }},
  "plan": [
    {{"agent": "ADM|ATM|ACM|AAM", "action": "...", "params": {{...}}}},
    ...
  ]
}}"""
        
        result = self.process(prompt)
        
        # Сохраняем в кэш
        self.cache[normalized] = (result, time.time())
        
        # Очищаем устаревшие записи (опционально, для экономии памяти)
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if not self._is_cache_valid(timestamp)
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.logger.debug(f"Очищено {len(expired_keys)} устаревших записей из кэша")
        
        return result
    
    def execute_plan(
        self,
        plan: List[Dict[str, Any]],
        agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Выполняет план, координируя работу агентов
        
        Args:
            plan: План выполнения от analyze_request
            agents: Словарь с экземплярами агентов
        
        Returns:
            Результат выполнения плана
        """
        results = []
        
        for step in plan:
            agent_name = step.get("agent")
            action = step.get("action")
            params = step.get("params", {})
            
            if agent_name not in agents:
                raise ValueError(f"Агент {agent_name} не найден")
            
            agent = agents[agent_name]
            
            # Выполнение действия через агента
            if hasattr(agent, action):
                result = getattr(agent, action)(**params)
            else:
                result = agent.process(f"Выполни действие: {action}", params)
            
            results.append({
                "step": step,
                "result": result
            })
        
        return {
            "status": "completed",
            "results": results
        }


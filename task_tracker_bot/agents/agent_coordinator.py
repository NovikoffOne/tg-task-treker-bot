"""
Agent Coordinator - координатор всех агентов системы
"""

import time
import logging
import sys
import os
from typing import Dict, Any, Optional
from .orchestrator import OrchestratorAgent
from .task_manager import TaskManagerAgent
from .control_manager import ControlManagerAgent
from .data_manager import DataManagerAgent
from .analyze_manager import AnalyzeManagerAgent

# Добавляем путь к корню проекта для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from database import Database


class AgentCoordinator:
    """Координатор всех агентов системы"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, db: Optional[Database] = None):
        """
        Инициализация координатора и всех агентов
        
        Args:
            api_key: API ключ io.net
            model: Модель для использования
            db: Экземпляр Database
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Инициализация БД
        self.db = db or Database()
        
        # Инициализация ADM (Data Manager) - первый, так как другие зависят от него
        self.adm = DataManagerAgent(api_key=api_key, model=model, db=self.db)
        
        # Инициализация остальных агентов
        self.orchestrator = OrchestratorAgent(api_key=api_key, model=model)
        self.atm = TaskManagerAgent(api_key=api_key, model=model, data_manager=self.adm)
        self.acm = ControlManagerAgent(api_key=api_key, model=model, data_manager=self.adm)
        self.aam = AnalyzeManagerAgent(api_key=api_key, model=model, data_manager=self.adm)
        
        # Словарь агентов для удобного доступа
        self.agents = {
            "ADM": self.adm,
            "ATM": self.atm,
            "ACM": self.acm,
            "AAM": self.aam,
            "Orchestrator": self.orchestrator
        }
        
        self.logger.info("AgentCoordinator инициализирован со всеми агентами")
    
    def process_user_message(
        self,
        user_message: str,
        workspace_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Обработать сообщение пользователя через систему агентов
        
        Args:
            user_message: Сообщение пользователя
            workspace_id: ID пространства
            user_id: ID пользователя (опционально)
            
        Returns:
            Результат обработки с ответом для пользователя
        """
        overall_start_time = time.time()
        try:
            self.logger.info(
                f"Обработка сообщения пользователя: workspace_id={workspace_id}, "
                f"user_id={user_id}, message='{user_message[:100]}...'"
            )
            
            # Проверка наличия дат в запросе
            date_keywords = ["сегодня", "завтра", "послезавтра", "вчера"]
            has_date = any(keyword in user_message.lower() for keyword in date_keywords)
            if has_date:
                self.logger.debug(f"Обнаружены ключевые слова дат в запросе: {user_message}")
            
            # Шаг 1: Оркестратор анализирует запрос и составляет план
            analysis_start_time = time.time()
            analysis_result = self.orchestrator.analyze_request(user_message)
            analysis_time = (time.time() - analysis_start_time) * 1000
            self.logger.info(f"Анализ запроса выполнен за {analysis_time:.2f}ms")
            
            # Извлечение плана из результата
            if isinstance(analysis_result, dict):
                plan = analysis_result.get("plan", [])
                intent = analysis_result.get("intent", "unknown")
                entities = analysis_result.get("entities", {})
                
                # Логирование результата анализа для отладки
                self.logger.debug(f"Результат анализа: intent={intent}, plan_length={len(plan) if plan else 0}")
                if not plan:
                    self.logger.warning(f"План пуст! Результат анализа: {str(analysis_result)[:500]}")
                
                # Логирование извлеченных дат из entities
                if "date" in entities or "default_date" in entities:
                    extracted_date = entities.get("date") or entities.get("default_date")
                    self.logger.info(f"Извлечена дата из запроса: {extracted_date}")
            else:
                # Если результат не JSON, пытаемся создать простой план
                plan = []
                intent = "unknown"
                entities = {}
                self.logger.warning(f"Оркестратор вернул не-JSON результат: {type(analysis_result)}. Содержимое: {str(analysis_result)[:500]}")
            
            if not plan:
                return {
                    "status": "error",
                    "message": "Не удалось составить план выполнения. Попробуйте переформулировать запрос.",
                    "raw_response": str(analysis_result)
                }
            
            # Шаг 2: Выполнение плана
            execution_results = []
            context = {"workspace_id": workspace_id, "user_id": user_id, "entities": entities}
            
            for step in plan:
                agent_name = step.get("agent", "")
                action = step.get("action", "")
                params = step.get("params", {})
                
                # Добавление контекста к параметрам (только workspace_id и user_id)
                # Остальные параметры передаются только если указаны в плане
                if "workspace_id" not in params:
                    params["workspace_id"] = context.get("workspace_id")
                if "user_id" not in params and context.get("user_id"):
                    params["user_id"] = context.get("user_id")
                # entities передаются только если нужны
                if "entities" in context and "entities" not in params:
                    params["entities"] = context.get("entities")
                
                step_start_time = time.time()
                self.logger.info(f"Выполнение шага: {agent_name}.{action}")
                
                try:
                    if agent_name not in self.agents:
                        step_time = (time.time() - step_start_time) * 1000
                        execution_results.append({
                            "step": step,
                            "status": "error",
                            "message": f"Агент {agent_name} не найден",
                            "execution_time_ms": step_time,
                            "agent_name": agent_name,
                            "action": action
                        })
                        continue
                    
                    agent = self.agents[agent_name]
                    
                    # Выполнение действия
                    if hasattr(agent, action):
                        method = getattr(agent, action)
                        # Получаем сигнатуру метода и фильтруем параметры
                        import inspect
                        sig = inspect.signature(method)
                        method_params = {k: v for k, v in params.items() if k in sig.parameters}
                        result = method(**method_params)
                    else:
                        # Если метод не найден, используем process
                        result = agent.process(f"Выполни действие: {action}", params)
                    
                    step_time = (time.time() - step_start_time) * 1000
                    self.logger.info(
                        f"Шаг {agent_name}.{action} выполнен за {step_time:.2f}ms"
                    )
                    
                    # Логирование результатов создания задач
                    if action == "create_todo_batch" and isinstance(result, dict):
                        data = result.get("data", {})
                        personal_tasks = data.get("personal_tasks_created", [])
                        work_tasks = data.get("work_tasks_created", [])
                        errors = data.get("errors", [])
                        
                        self.logger.info(
                            f"Создано задач через {agent_name}.{action}: "
                            f"личных={len(personal_tasks)}, рабочих={len(work_tasks)}, ошибок={len(errors)}"
                        )
                        
                        # Логирование деталей созданных задач
                        if personal_tasks:
                            for task in personal_tasks[:5]:  # Логируем первые 5
                                self.logger.debug(
                                    f"Создана личная задача: id={task.get('id')}, "
                                    f"title='{task.get('title')}', date={task.get('date')}"
                                )
                        
                        if work_tasks:
                            for task in work_tasks[:5]:  # Логируем первые 5
                                self.logger.debug(
                                    f"Создана рабочая задача: id={task.get('id')}, "
                                    f"title='{task.get('title')}', project_id={task.get('project_id')}, "
                                    f"date={task.get('date')}"
                                )
                    
                    execution_results.append({
                        "step": step,
                        "status": "success",
                        "result": result,
                        "execution_time_ms": step_time,
                        "agent_name": agent_name,
                        "action": action
                    })
                    
                    # Обновление контекста для следующих шагов
                    if isinstance(result, dict) and "data" in result:
                        context.update(result["data"])
                    
                except Exception as e:
                    step_time = (time.time() - step_start_time) * 1000
                    self.logger.error(
                        f"Ошибка при выполнении шага {agent_name}.{action} "
                        f"(время: {step_time:.2f}ms): {e}"
                    )
                    execution_results.append({
                        "step": step,
                        "status": "error",
                        "message": str(e),
                        "execution_time_ms": step_time,
                        "agent_name": agent_name,
                        "action": action
                    })
                    # Прерываем выполнение при критической ошибке
                    break
            
            # Шаг 3: Проверка корректности через ACM (если были изменения)
            validation_result = None
            if intent in ["create_project", "close_task", "update_task"]:
                validation_start_time = time.time()
                try:
                    # Определяем entity_id из результатов выполнения
                    entity_id = None
                    for result in execution_results:
                        if result.get("status") == "success":
                            result_data = result.get("result", {})
                            if isinstance(result_data, dict):
                                data = result_data.get("data", {})
                                entity_id = data.get("id") or data.get("project_id") or data.get("task_id")
                                if entity_id:
                                    break
                    
                    if entity_id:
                        validation_result = self.acm.validate_changes(
                            operation_type=intent,
                            entity_id=str(entity_id),
                            context=context
                        )
                    validation_time = (time.time() - validation_start_time) * 1000
                    self.logger.info(f"Валидация выполнена за {validation_time:.2f}ms")
                except Exception as e:
                    validation_time = (time.time() - validation_start_time) * 1000
                    self.logger.warning(f"Ошибка при валидации (время: {validation_time:.2f}ms): {e}")
            
            # Шаг 4: Формирование ответа пользователю
            success_count = sum(1 for r in execution_results if r.get("status") == "success")
            error_count = sum(1 for r in execution_results if r.get("status") == "error")
            
            # Извлечение сообщений из результатов
            messages = []
            created_tasks_summary = {"personal": 0, "work": 0}
            
            for result in execution_results:
                if result.get("status") == "success":
                    result_data = result.get("result", {})
                    if isinstance(result_data, dict):
                        msg = result_data.get("message", "")
                        if msg:
                            messages.append(msg)
                        
                        # Подсчет созданных задач
                        data = result_data.get("data", {})
                        if "personal_tasks_created" in data:
                            created_tasks_summary["personal"] += len(data["personal_tasks_created"])
                        if "work_tasks_created" in data:
                            created_tasks_summary["work"] += len(data["work_tasks_created"])
            
            # Логирование итогового количества созданных задач
            if created_tasks_summary["personal"] > 0 or created_tasks_summary["work"] > 0:
                self.logger.info(
                    f"Итого создано задач: личных={created_tasks_summary['personal']}, "
                    f"рабочих={created_tasks_summary['work']}"
                )
            
            # Формирование итогового сообщения
            if error_count == 0:
                status = "success"
                message = "\n".join(messages) if messages else "Операция выполнена успешно"
            else:
                status = "partial_success" if success_count > 0 else "error"
                error_messages = [
                    r.get("message", "Неизвестная ошибка")
                    for r in execution_results
                    if r.get("status") == "error"
                ]
                message = "Выполнено с ошибками:\n" + "\n".join(error_messages)
            
            overall_time = (time.time() - overall_start_time) * 1000
            
            # Вычисляем общее время выполнения шагов
            total_steps_time = sum(
                r.get("execution_time_ms", 0) for r in execution_results
            )
            
            self.logger.info(
                f"Обработка сообщения завершена за {overall_time:.2f}ms "
                f"(анализ: {analysis_time:.2f}ms, шаги: {total_steps_time:.2f}ms)"
            )
            
            response = {
                "status": status,
                "message": message,
                "intent": intent,
                "execution_results": execution_results,
                "validation": validation_result,
                "metrics": {
                    "total_time_ms": overall_time,
                    "analysis_time_ms": analysis_time,
                    "steps_time_ms": total_steps_time,
                    "steps_count": len(execution_results)
                }
            }
            
            # Добавление данных из последнего успешного результата
            for result in reversed(execution_results):
                if result.get("status") == "success":
                    result_data = result.get("result", {})
                    if isinstance(result_data, dict) and "data" in result_data:
                        response["data"] = result_data["data"]
                        break
            
            return response
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при обработке сообщения: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Произошла ошибка при обработке запроса: {str(e)}"
            }
    
    def format_response_for_telegram(self, response: Dict[str, Any]) -> str:
        """
        Форматирует ответ для отправки в Telegram
        
        Args:
            response: Результат process_user_message
            
        Returns:
            Форматированное сообщение для Telegram
        """
        status = response.get("status", "unknown")
        message = response.get("message", "")
        
        # Добавление эмодзи в зависимости от статуса
        if status == "success":
            prefix = "✅ "
        elif status == "partial_success":
            prefix = "⚠️ "
        elif status == "error":
            prefix = "❌ "
        else:
            prefix = "ℹ️ "
        
        formatted = prefix + message
        
        # Добавление данных, если есть
        if "data" in response:
            data = response["data"]
            if isinstance(data, dict):
                # Обработка результатов создания пакета задач
                if "personal_tasks_created" in data or "work_tasks_created" in data:
                    personal_count = len(data.get("personal_tasks_created", []))
                    work_count = len(data.get("work_tasks_created", []))
                    errors = data.get("errors", [])
                    
                    if personal_count > 0 or work_count > 0:
                        formatted += f"\n\n📝 Создано задач:"
                        if personal_count > 0:
                            formatted += f"\n• Личных: {personal_count}"
                        if work_count > 0:
                            formatted += f"\n• Рабочих: {work_count}"
                    
                    if errors:
                        formatted += f"\n\n⚠️ Ошибки ({len(errors)}):"
                        for error in errors[:5]:  # Показываем максимум 5 ошибок
                            formatted += f"\n• {error}"
                elif "id" in data:
                    formatted += f"\n\nID: {data['id']}"
                elif "name" in data:
                    formatted += f"\nНазвание: {data['name']}"
        
        # Добавление предупреждений из валидации
        validation = response.get("validation")
        if validation and isinstance(validation, dict):
            warnings = validation.get("warnings", [])
            if warnings:
                formatted += "\n\n⚠️ Предупреждения:"
                for warning in warnings:
                    formatted += f"\n• {warning}"
        
        return formatted


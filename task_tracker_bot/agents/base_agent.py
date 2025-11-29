"""
Базовый класс для всех AI-агентов
"""

import os
import json
import time
import requests
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from functools import wraps
from config import Config


class BaseAgent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Инициализация агента
        
        Args:
            api_key: API ключ io.net (если None, берется из Config или файла)
            model: Модель для использования (если None, берется из Config)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Загрузка API ключа
        self.api_key = api_key or Config.IO_NET_API_KEY
        if not self.api_key:
            # Попытка загрузить из файла tg_aitt_service
            try:
                key_path = os.path.join(os.path.dirname(__file__), "..", "tg_aitt_service", "io_net_api_key.txt")
                if os.path.exists(key_path):
                    with open(key_path, "r") as f:
                        self.api_key = f.read().strip()
                        self.logger.info("API ключ загружен из файла")
            except Exception as e:
                self.logger.warning(f"Не удалось загрузить API ключ из файла: {e}")
        
        if not self.api_key:
            raise ValueError("IO_NET_API_KEY не найден. Установите переменную окружения IO_NET_API_KEY или создайте task_tracker_bot/tg_aitt_service/io_net_api_key.txt")
        
        self.model = model or Config.IO_NET_MODEL
        self.api_url = Config.IO_NET_API_URL
        self.temperature = Config.IO_NET_TEMPERATURE
        self.max_tokens = Config.IO_NET_MAX_TOKENS
        self.timeout = Config.IO_NET_TIMEOUT
        self.retry_count = Config.IO_NET_RETRY_COUNT
        self.retry_delay = Config.IO_NET_RETRY_DELAY
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Возвращает системный промпт для агента"""
        pass
    
    def call_api_with_retry(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Вызов io.net AI API с retry логикой и экспоненциальной задержкой
        
        Args:
            user_prompt: Промпт пользователя
            context: Контекст для агента (опционально)
        
        Returns:
            Ответ от API
        
        Raises:
            Exception: Если все попытки retry не удались
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": user_prompt}
        ]
        
        if context:
            messages.append({
                "role": "assistant",
                "content": json.dumps(context, ensure_ascii=False)
            })
        
        last_exception = None
        
        for attempt in range(self.retry_count):
            try:
                start_time = time.time()
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                elapsed_time = (time.time() - start_time) * 1000
                self.logger.info(f"API вызов успешен за {elapsed_time:.2f}ms (попытка {attempt + 1})")
                return response.json()
            
            except requests.exceptions.Timeout as e:
                last_exception = e
                elapsed_time = (time.time() - start_time) * 1000
                self.logger.warning(
                    f"Таймаут при вызове io.net API (попытка {attempt + 1}/{self.retry_count}), "
                    f"время: {elapsed_time:.2f}ms"
                )
                if attempt < self.retry_count - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Экспоненциальная задержка
                    self.logger.info(f"Повтор через {delay:.2f} секунд...")
                    time.sleep(delay)
            
            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else None
                self.logger.warning(
                    f"HTTP ошибка при вызове io.net API: {status_code} "
                    f"(попытка {attempt + 1}/{self.retry_count})"
                )
                # Retry только для 5xx ошибок
                if status_code and 500 <= status_code < 600:
                    if attempt < self.retry_count - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        self.logger.info(f"Повтор через {delay:.2f} секунд...")
                        time.sleep(delay)
                    else:
                        break
                else:
                    # Для других HTTP ошибок не делаем retry
                    break
            
            except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                last_exception = e
                self.logger.warning(
                    f"Ошибка соединения при вызове io.net API: {str(e)} "
                    f"(попытка {attempt + 1}/{self.retry_count})"
                )
                if attempt < self.retry_count - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.info(f"Повтор через {delay:.2f} секунд...")
                    time.sleep(delay)
        
        # Все попытки исчерпаны
        if isinstance(last_exception, requests.exceptions.Timeout):
            error_msg = f"Таймаут при вызове io.net API после {self.retry_count} попыток. Попробуйте позже."
        elif isinstance(last_exception, requests.exceptions.HTTPError):
            status_code = last_exception.response.status_code if last_exception.response else None
            error_msg = f"Ошибка API io.net: {status_code} после {self.retry_count} попыток."
        else:
            error_msg = f"Ошибка при вызове io.net API после {self.retry_count} попыток: {str(last_exception)}"
        
        self.logger.error(error_msg)
        raise Exception(error_msg)
    
    def call_api(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Вызов io.net AI API с retry логикой
        
        Args:
            user_prompt: Промпт пользователя
            context: Контекст для агента (опционально)
        
        Returns:
            Ответ от API
        """
        return self.call_api_with_retry(user_prompt, context)
    
    def process(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Обработка запроса агентом с измерением времени выполнения
        
        Args:
            prompt: Промпт для обработки
            context: Контекст (опционально)
        
        Returns:
            Результат обработки
        """
        start_time = time.time()
        try:
            response = self.call_api(prompt, context)
            
            # Извлечение ответа из структуры io.net API
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                
                # Проверка на пустой ответ
                if not content or not content.strip():
                    self.logger.error(f"{self.__class__.__name__} получил пустой ответ от API")
                    raise Exception("API вернул пустой ответ")
                
                # Логирование raw ответа для отладки
                self.logger.debug(f"{self.__class__.__name__} получил ответ от API (первые 500 символов): {content[:500]}")
                
                # Попытка извлечь JSON из markdown блоков (```json ... ```)
                json_content = content.strip()
                if "```json" in json_content:
                    start = json_content.find("```json") + 7
                    end = json_content.find("```", start)
                    if end != -1:
                        json_content = json_content[start:end].strip()
                        self.logger.debug(f"Извлечен JSON из markdown блока")
                elif "```" in json_content:
                    # Попытка извлечь JSON из обычного markdown блока
                    start = json_content.find("```") + 3
                    end = json_content.find("```", start)
                    if end != -1:
                        json_content = json_content[start:end].strip()
                        self.logger.debug(f"Извлечен JSON из markdown блока (без json тега)")
                
                # Попытка распарсить JSON
                try:
                    result = json.loads(json_content)
                    self.logger.debug(f"{self.__class__.__name__} успешно распарсил JSON")
                except json.JSONDecodeError as e:
                    self.logger.warning(f"{self.__class__.__name__} не удалось распарсить JSON: {e}. Raw content: {json_content[:500]}")
                    # Попытка найти JSON в тексте
                    import re
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_content, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            self.logger.info(f"{self.__class__.__name__} успешно распарсил JSON из текста")
                        except:
                            result = {"response": content}
                    else:
                        result = {"response": content}
                
                elapsed_time = (time.time() - start_time) * 1000
                self.logger.info(f"{self.__class__.__name__}.process() выполнен за {elapsed_time:.2f}ms")
                return result
            
            raise Exception("Неожиданный формат ответа от API")
        except Exception as e:
            elapsed_time = (time.time() - start_time) * 1000
            self.logger.error(f"{self.__class__.__name__}.process() завершился с ошибкой за {elapsed_time:.2f}ms: {e}")
            raise



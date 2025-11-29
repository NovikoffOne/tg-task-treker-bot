"""
Тестирование бота через Telegram MCP
Использует MCP сервер для отправки команд боту и проверки ответов
"""
import asyncio
import time
from typing import Optional, List, Dict, Any


class TelegramMCPTester:
    """
    Класс для тестирования Telegram бота через MCP сервер
    """
    
    def __init__(self, bot_username: str, delay_between_messages: float = 1.0):
        """
        Инициализация тестера
        
        Args:
            bot_username: Username бота (например, 'my_task_tracker_bot')
            delay_between_messages: Задержка между сообщениями в секундах
        """
        self.bot_username = bot_username
        self.delay = delay_between_messages
        self.chat_id: Optional[str] = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def find_bot_chat(self) -> bool:
        """
        Находит чат с ботом по username
        
        Returns:
            True если чат найден, False иначе
        """
        try:
            # Получаем список чатов
            chats = await self._mcp_call("mcp_telegram-mcp_list_chats", {
                "chat_type": "user",
                "limit": 100
            })
            
            # Ищем бота по username
            for chat in chats.get("chats", []):
                if chat.get("username") == self.bot_username:
                    self.chat_id = chat.get("id")
                    print(f"✅ Найден чат с ботом: {self.chat_id}")
                    return True
            
            # Если не нашли, пробуем найти через get_direct_chat_by_contact
            try:
                chat_info = await self._mcp_call("mcp_telegram-mcp_get_direct_chat_by_contact", {
                    "contact_query": self.bot_username
                })
                if chat_info and chat_info.get("id"):
                    self.chat_id = chat_info.get("id")
                    print(f"✅ Найден чат с ботом через contact: {self.chat_id}")
                    return True
            except Exception as e:
                print(f"⚠️ Не удалось найти через contact: {e}")
            
            print(f"❌ Чат с ботом {self.bot_username} не найден")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка при поиске чата: {e}")
            return False
    
    async def _mcp_call(self, function_name: str, params: Dict[str, Any]) -> Any:
        """
        Вспомогательный метод для вызова MCP функций
        В реальном использовании это будет вызываться через MCP сервер
        """
        # Это заглушка - в реальности будет использоваться MCP сервер
        # Для тестирования можно использовать прямые вызовы функций
        raise NotImplementedError("Используйте MCP сервер для вызова функций")
    
    async def send_command(self, command: str, wait_for_response: bool = True) -> Optional[str]:
        """
        Отправляет команду боту и возвращает ответ
        
        Args:
            command: Команда для отправки (например, '/start')
            wait_for_response: Ждать ли ответа от бота
            
        Returns:
            Текст ответа бота или None
        """
        if not self.chat_id:
            print("❌ Чат с ботом не найден. Вызовите find_bot_chat() сначала")
            return None
        
        try:
            # Отправляем команду
            await self._mcp_call("mcp_telegram-mcp_send_message", {
                "chat_id": self.chat_id,
                "message": command
            })
            
            print(f"📤 Отправлено: {command}")
            
            if wait_for_response:
                # Ждем ответа
                await asyncio.sleep(self.delay)
                
                # Получаем последние сообщения
                messages = await self._mcp_call("mcp_telegram-mcp_get_messages", {
                    "chat_id": self.chat_id,
                    "page": 1,
                    "page_size": 5
                })
                
                # Находим ответ бота (последнее сообщение от бота)
                bot_messages = [
                    msg for msg in messages.get("messages", [])
                    if msg.get("from_id") != "me"  # Сообщение не от нас
                ]
                
                if bot_messages:
                    latest_message = bot_messages[0]
                    response_text = latest_message.get("text", "")
                    print(f"📥 Получено: {response_text[:100]}...")
                    return response_text
                else:
                    print("⚠️ Ответ от бота не получен")
                    return None
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка при отправке команды: {e}")
            return None
    
    async def test_command(self, command: str, expected_keywords: List[str] = None) -> bool:
        """
        Тестирует команду и проверяет наличие ключевых слов в ответе
        
        Args:
            command: Команда для тестирования
            expected_keywords: Список ключевых слов, которые должны быть в ответе
            
        Returns:
            True если тест пройден, False иначе
        """
        response = await self.send_command(command)
        
        if not response:
            self.test_results.append({
                "command": command,
                "status": "FAILED",
                "reason": "Нет ответа от бота"
            })
            return False
        
        # Проверяем наличие ключевых слов
        if expected_keywords:
            found_keywords = [kw for kw in expected_keywords if kw.lower() in response.lower()]
            if not found_keywords:
                self.test_results.append({
                    "command": command,
                    "status": "FAILED",
                    "reason": f"Не найдены ключевые слова: {expected_keywords}",
                    "response": response[:200]
                })
                return False
        
        self.test_results.append({
            "command": command,
            "status": "PASSED",
            "response_length": len(response)
        })
        return True
    
    def print_results(self):
        """Выводит результаты тестирования"""
        print("\n" + "="*60)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['command']}")
            if result["status"] == "FAILED":
                print(f"   Причина: {result.get('reason', 'Неизвестно')}")
                if "response" in result:
                    print(f"   Ответ: {result['response']}")
        
        print("\n" + "-"*60)
        print(f"Всего тестов: {len(self.test_results)}")
        print(f"✅ Пройдено: {passed}")
        print(f"❌ Провалено: {failed}")
        print("="*60)


# Пример использования через MCP сервер
async def run_tests_via_mcp(bot_username: str):
    """
    Запуск тестов через MCP сервер
    
    Использование:
        1. Убедитесь, что бот запущен и работает
        2. Узнайте username вашего бота (например, 'my_task_tracker_bot')
        3. Запустите эту функцию через MCP сервер
    """
    tester = TelegramMCPTester(bot_username, delay_between_messages=2.0)
    
    # Находим чат с ботом
    if not await tester.find_bot_chat():
        print("❌ Не удалось найти чат с ботом. Проверьте username бота.")
        return
    
    print("\n🚀 Начинаем тестирование...\n")
    
    # Базовые команды
    await tester.test_command("/start", ["привет", "меню", "start"])
    await asyncio.sleep(1)
    
    await tester.test_command("/help", ["команды", "help", "справка"])
    await asyncio.sleep(1)
    
    await tester.test_command("/menu", ["меню", "menu"])
    await asyncio.sleep(1)
    
    # Пространства
    await tester.test_command("/workspaces", ["пространств", "workspace"])
    await asyncio.sleep(1)
    
    # Доски
    await tester.test_command("/boards", ["доск", "board"])
    await asyncio.sleep(1)
    
    # Проекты
    await tester.test_command("/projects", ["проект", "project"])
    await asyncio.sleep(1)
    
    # Статистика
    await tester.test_command("/stats", ["статистик", "stat"])
    await asyncio.sleep(1)
    
    # Выводим результаты
    tester.print_results()


if __name__ == "__main__":
    # Пример запуска (требует настройки MCP сервера)
    print("Для использования этого скрипта необходимо:")
    print("1. Настроить Telegram MCP сервер")
    print("2. Узнать username вашего бота")
    print("3. Запустить бота")
    print("4. Использовать функцию run_tests_via_mcp() через MCP")
    print("\nСм. TELEGRAM_MCP_TESTING.md для подробной инструкции")


"""
Скрипт для ручного тестирования MVP 0.2 через Telegram MCP
"""
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, List
import json

# Импорт функций Telegram MCP (будут использоваться через MCP сервер)
# В реальном использовании эти функции будут доступны через MCP сервер

class MCPTester:
    """Класс для тестирования бота через Telegram MCP"""
    
    def __init__(self, bot_username: str):
        self.bot_username = bot_username
        self.chat_id: Optional[int] = None
        self.results: List[Dict] = []
        self.test_data: Dict = {}
        
    async def find_bot_chat(self) -> bool:
        """Найти чат с ботом"""
        # В реальном использовании будет вызываться через MCP:
        # chat = mcp_telegram-mcp_get_direct_chat_by_contact(contact_query=self.bot_username)
        # self.chat_id = chat["id"]
        # return self.chat_id is not None
        
        # Заглушка для документации
        print(f"[INFO] Поиск чата с ботом: {self.bot_username}")
        print("[INFO] В реальном использовании будет вызвана функция MCP:")
        print(f"  mcp_telegram-mcp_get_direct_chat_by_contact(contact_query='{self.bot_username}')")
        return True
    
    async def send_message(self, message: str, wait_time: float = 2.0) -> Optional[str]:
        """Отправить сообщение боту и получить ответ"""
        if not self.chat_id:
            print("[ERROR] Чат с ботом не найден")
            return None
        
        print(f"[SEND] {message}")
        
        # В реальном использовании будет вызываться через MCP:
        # mcp_telegram-mcp_send_message(chat_id=self.chat_id, message=message)
        # await asyncio.sleep(wait_time)
        # messages = mcp_telegram-mcp_get_messages(chat_id=self.chat_id, page=1, page_size=5)
        # bot_messages = [m for m in messages["messages"] if m["from_id"] != "me"]
        # if bot_messages:
        #     response = bot_messages[0]["text"]
        #     print(f"[RECV] {response}")
        #     return response
        
        # Заглушка для документации
        await asyncio.sleep(wait_time)
        print(f"[RECV] [Ожидается ответ от бота]")
        return None
    
    def check_keywords(self, response: str, keywords: List[str]) -> bool:
        """Проверить наличие ключевых слов в ответе"""
        if not response:
            return False
        response_lower = response.lower()
        return any(kw.lower() in response_lower for kw in keywords)
    
    def record_test_result(self, test_name: str, success: bool, 
                          expected: str, actual: str, notes: str = ""):
        """Записать результат теста"""
        result = {
            'test_name': test_name,
            'success': success,
            'expected': expected,
            'actual': actual,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if notes:
            print(f"  Примечание: {notes}")
    
    async def test_basic_commands(self):
        """Группа 1: Базовые команды MVP 0.2"""
        print("\n=== Группа 1: Базовые команды ===")
        
        # Тест 1.1: Команда /mytasks (без задач)
        print("\n[TEST 1.1] Команда /mytasks (без задач)")
        response = await self.send_message("/mytasks")
        if response:
            success = self.check_keywords(response, ["нет", "назначен", "задач"])
            self.record_test_result(
                "1.1 /mytasks (без задач)",
                success,
                "Сообщение с словами: нет, назначен, задач",
                response[:100] if response else "Нет ответа"
            )
        
        # Тест 1.2: Команда /today (без задач)
        print("\n[TEST 1.2] Команда /today (без задач)")
        response = await self.send_message("/today")
        if response:
            success = self.check_keywords(response, ["нет", "сегодня", "дедлайн"])
            self.record_test_result(
                "1.2 /today (без задач)",
                success,
                "Сообщение с словами: нет, сегодня, дедлайн",
                response[:100] if response else "Нет ответа"
            )
    
    async def test_structure_creation(self):
        """Группа 2: Создание структуры для тестирования"""
        print("\n=== Группа 2: Создание структуры ===")
        
        # Тест 2.1: Создание тестового пространства
        print("\n[TEST 2.1] Создание тестового пространства")
        response = await self.send_message("/newworkspace Тестовое пространство MVP02")
        if response:
            success = self.check_keywords(response, ["создан", "успешно", "пространств"])
            self.record_test_result(
                "2.1 Создание workspace",
                success,
                "Сообщение об успешном создании пространства",
                response[:100] if response else "Нет ответа"
            )
        
        # Тест 2.2: Создание досок
        print("\n[TEST 2.2] Создание досок")
        boards = ["Подготовка", "Дизайн", "Разработка", "Тестирование"]
        for board in boards:
            response = await self.send_message(f"/newboard {board}")
            if response:
                success = self.check_keywords(response, ["создан", "доск"])
                self.record_test_result(
                    f"2.2 Создание доски '{board}'",
                    success,
                    "Сообщение об успешном создании доски",
                    response[:100] if response else "Нет ответа"
                )
        
        # Тест 2.3: Добавление колонок
        print("\n[TEST 2.3] Добавление колонок")
        columns_config = [
            ("Дизайн", ["Очередь", "План на неделю", "В работе", "На утверждении", "Готово"]),
            ("Разработка", ["Очередь", "План на неделю", "В работе", "Тестирование", "Фикс Багов", "Готово"]),
        ]
        
        for board_name, columns in columns_config:
            for column_name in columns:
                response = await self.send_message(f"/addcolumn {board_name} {column_name}")
                if response:
                    success = self.check_keywords(response, ["создан", "колонк"])
                    self.record_test_result(
                        f"2.3 Создание колонки '{column_name}' в '{board_name}'",
                        success,
                        "Сообщение об успешном создании колонки",
                        response[:100] if response else "Нет ответа"
                    )
        
        # Тест 2.4: Создание проекта
        print("\n[TEST 2.4] Создание проекта")
        response = await self.send_message("/newproject 5001 Pictory Ai")
        if response:
            success = "5001" in response and self.check_keywords(response, ["создан", "проект"])
            self.record_test_result(
                "2.4 Создание проекта 5001",
                success,
                "Сообщение о создании проекта с ID 5001",
                response[:100] if response else "Нет ответа"
            )
            # Сохранить информацию о проекте
            self.test_data['project_id'] = '5001'
    
    async def test_dependencies(self):
        """Группа 3: Тестирование зависимостей досок"""
        print("\n=== Группа 3: Зависимости досок ===")
        
        # Тест 3.1: Создание зависимости "Подготовка -> Дизайн"
        print("\n[TEST 3.1] Создание зависимости Подготовка -> Дизайн")
        response = await self.send_message(
            '/newdependency "Подготовка->Дизайн" Подготовка Готово Дизайн Очередь create_task "{project_id} {project_name} Дизайн"'
        )
        if response:
            success = self.check_keywords(response, ["создан", "зависимость"])
            self.record_test_result(
                "3.1 Создание зависимости Подготовка->Дизайн",
                success,
                "Сообщение об успешном создании зависимости",
                response[:100] if response else "Нет ответа"
            )
        
        # Тест 3.2: Проверка работы зависимости
        print("\n[TEST 3.2] Проверка работы зависимости")
        # Сначала нужно найти задачу проекта на доске Подготовка
        response = await self.send_message("/board Подготовка")
        if response and "5001" in response:
            # Найти ID задачи (упрощенно - в реальности нужно парсить)
            # Предполагаем, что задача есть и нужно переместить её
            # response = await self.send_message("/movetask <task_id> Готово")
            # Затем проверить доску Дизайн
            # response = await self.send_message("/board Дизайн")
            # success = "5001" in response and "Pictory Ai Дизайн" in response
            self.record_test_result(
                "3.2 Проверка работы зависимости",
                False,  # Помечаем как требующий ручной проверки
                "Задача автоматически создана на доске Дизайн",
                "Требуется ручная проверка",
                "Необходимо найти task_id и выполнить перемещение"
            )
    
    async def test_assignments(self):
        """Группа 4: Тестирование участников проекта"""
        print("\n=== Группа 4: Участники проекта ===")
        
        # Тест 4.1: Автоматическое назначение при перемещении
        print("\n[TEST 4.1] Автоматическое назначение при перемещении")
        # Требуется найти task_id и переместить в "В работе"
        # response = await self.send_message("/movetask <task_id> В работе")
        # response = await self.send_message("/mytasks")
        # success = "<task_id>" in response
        self.record_test_result(
            "4.1 Автоматическое назначение",
            False,
            "Задача появилась в /mytasks",
            "Требуется ручная проверка",
            "Необходимо найти task_id и выполнить перемещение"
        )
    
    async def test_deadlines(self):
        """Группа 5: Тестирование дедлайнов"""
        print("\n=== Группа 5: Дедлайны ===")
        
        # Тест 5.1: Установка дедлайна
        print("\n[TEST 5.1] Установка дедлайна")
        # Требуется найти task_id
        # today = datetime.now().strftime("%d.%m.%Y")
        # response = await self.send_message(f"/deadline <task_id> {today}")
        # success = "дедлайн" in response.lower() and today in response
        self.record_test_result(
            "5.1 Установка дедлайна",
            False,
            "Дедлайн установлен успешно",
            "Требуется ручная проверка",
            "Необходимо найти task_id"
        )
        
        # Тест 5.2: Проверка команды /today
        print("\n[TEST 5.2] Проверка команды /today")
        response = await self.send_message("/today")
        if response:
            # Проверка будет зависеть от того, установлен ли дедлайн
            self.record_test_result(
                "5.2 Команда /today",
                True,  # Команда работает, даже если нет задач
                "Команда выполняется без ошибок",
                response[:100] if response else "Нет ответа"
            )
    
    async def test_board_view(self):
        """Группа 6: Тестирование просмотра задачи на доске"""
        print("\n=== Группа 6: Просмотр задачи на доске ===")
        
        # Тест 6.1: Просмотр доски
        print("\n[TEST 6.1] Просмотр доски")
        response = await self.send_message("/board Разработка")
        if response:
            success = len(response) > 0  # Просто проверяем, что есть ответ
            self.record_test_result(
                "6.1 Просмотр доски",
                success,
                "Доска отображается корректно",
                response[:100] if response else "Нет ответа"
            )
    
    async def test_board_list(self):
        """Группа 7: Тестирование отображения доски в виде списка"""
        print("\n=== Группа 7: Отображение доски списком ===")
        
        # Тест 7.1: Команда /boardlist
        print("\n[TEST 7.1] Команда /boardlist")
        response = await self.send_message("/boardlist Разработка")
        if response:
            success = "Очередь:" in response or "В работе:" in response or "Разработка" in response
            self.record_test_result(
                "7.1 Команда /boardlist",
                success,
                "Доска отображается в виде списка",
                response[:100] if response else "Нет ответа"
            )
    
    async def test_date_tracking(self):
        """Группа 8: Тестирование автоматического трекинга дат"""
        print("\n=== Группа 8: Автоматический трекинг дат ===")
        
        # Тест 8.1: Автоматическая запись started_at
        print("\n[TEST 8.1] Автоматическая запись started_at")
        # Требуется найти task_id и переместить в "В работе"
        # Затем проверить через /task <task_id>
        self.record_test_result(
            "8.1 Автоматическая запись started_at",
            False,
            "В карточке задачи есть дата 'Начато'",
            "Требуется ручная проверка",
            "Необходимо найти task_id и выполнить перемещение"
        )
    
    async def run_all_tests(self):
        """Запустить все тесты"""
        print("=" * 60)
        print("НАЧАЛО ТЕСТИРОВАНИЯ MVP 0.2 ЧЕРЕЗ TELEGRAM MCP")
        print("=" * 60)
        
        # Инициализация
        if not await self.find_bot_chat():
            print("[ERROR] Не удалось найти чат с ботом")
            return
        
        # Отправить /start для инициализации
        await self.send_message("/start", wait_time=2.0)
        
        # Запустить группы тестов
        await self.test_basic_commands()
        await self.test_structure_creation()
        await self.test_dependencies()
        await self.test_assignments()
        await self.test_deadlines()
        await self.test_board_view()
        await self.test_board_list()
        await self.test_date_tracking()
        
        # Вывести итоги
        self.print_summary()
    
    def print_summary(self):
        """Вывести итоговую сводку"""
        print("\n" + "=" * 60)
        print("ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"\nВсего тестов: {total}")
        print(f"Пройдено: {passed}")
        print(f"Провалено: {failed}")
        if total > 0:
            print(f"Процент успеха: {passed/total*100:.1f}%")
        
        print("\nДетальные результаты:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}")
            if not result['success']:
                print(f"   Ожидалось: {result['expected']}")
                print(f"   Получено: {result['actual']}")
                if result['notes']:
                    print(f"   Примечание: {result['notes']}")
    
    def save_results(self, filename: str = "mcp_test_results.md"):
        """Сохранить результаты в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Результаты тестирования MVP 0.2 через Telegram MCP\n\n")
            f.write(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Бот:** {self.bot_username}\n\n")
            
            total = len(self.results)
            passed = sum(1 for r in self.results if r['success'])
            failed = total - passed
            
            f.write("## Итоги\n\n")
            f.write(f"- Всего тестов: {total}\n")
            f.write(f"- Пройдено: {passed}\n")
            f.write(f"- Провалено: {failed}\n")
            if total > 0:
                f.write(f"- Процент успеха: {passed/total*100:.1f}%\n\n")
            
            f.write("## Детальные результаты\n\n")
            for result in self.results:
                status = "✅" if result['success'] else "❌"
                f.write(f"### {status} {result['test_name']}\n\n")
                f.write(f"- **Ожидалось:** {result['expected']}\n")
                f.write(f"- **Получено:** {result['actual']}\n")
                if result['notes']:
                    f.write(f"- **Примечание:** {result['notes']}\n")
                f.write(f"- **Время:** {result['timestamp']}\n\n")
            
            # Найденные проблемы
            failed_results = [r for r in self.results if not r['success']]
            if failed_results:
                f.write("## Найденные проблемы\n\n")
                for i, result in enumerate(failed_results, 1):
                    f.write(f"{i}. **{result['test_name']}**\n")
                    f.write(f"   - Ожидалось: {result['expected']}\n")
                    f.write(f"   - Получено: {result['actual']}\n")
                    if result['notes']:
                        f.write(f"   - Примечание: {result['notes']}\n")
                    f.write("\n")

async def main():
    """Главная функция"""
    # Указать username бота
    bot_username = "your_bot_username"  # Заменить на реальный username
    
    tester = MCPTester(bot_username)
    await tester.run_all_tests()
    tester.save_results("task_tracker_bot/tests/mcp_test_results.md")

if __name__ == "__main__":
    print("""
    ВНИМАНИЕ: Этот скрипт требует настройки Telegram MCP сервера.
    
    Для использования:
    1. Убедитесь, что Telegram MCP сервер настроен и работает
    2. Замените 'your_bot_username' на реальный username вашего бота
    3. Раскомментируйте реальные вызовы MCP функций в методах класса
    4. Запустите скрипт: python test_mvp_0_2_mcp_manual.py
    
    Скрипт создан как шаблон для ручного тестирования через MCP.
    """)
    
    # Раскомментировать для реального запуска:
    # asyncio.run(main())


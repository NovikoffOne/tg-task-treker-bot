# Тестирование бота через Telegram MCP

Это руководство описывает, как тестировать Telegram бота самостоятельно с использованием Telegram MCP сервера.

## Что нужно для тестирования

### 1. Запущенный бот
Убедитесь, что ваш бот запущен и работает:
```bash
cd task_tracker_bot
python bot.py
```

### 2. Username бота
Узнайте username вашего бота. Он указан при создании через @BotFather и выглядит как `my_task_tracker_bot`.

### 3. Telegram MCP сервер
Убедитесь, что Telegram MCP сервер настроен и работает. Он должен быть доступен через Cursor AI.

### 4. Доступ к вашему Telegram аккаунту
MCP сервер должен иметь доступ к вашему Telegram аккаунту для отправки и получения сообщений.

## Быстрый старт

### Шаг 1: Найдите чат с ботом

Сначала нужно найти чат с вашим ботом. Используйте MCP функцию для получения списка чатов:

```python
# Через MCP сервер
chats = mcp_telegram-mcp_list_chats(chat_type="user", limit=100)
```

Или найдите бота напрямую:

```python
chat = mcp_telegram-mcp_get_direct_chat_by_contact(contact_query="your_bot_username")
chat_id = chat["id"]
```

### Шаг 2: Отправьте команду боту

```python
# Отправка команды /start
mcp_telegram-mcp_send_message(
    chat_id=chat_id,
    message="/start"
)
```

### Шаг 3: Получите ответ

```python
# Получение последних сообщений
messages = mcp_telegram-mcp_get_messages(
    chat_id=chat_id,
    page=1,
    page_size=5
)

# Найдите последнее сообщение от бота
bot_messages = [msg for msg in messages["messages"] if msg["from_id"] != "me"]
if bot_messages:
    response = bot_messages[0]["text"]
    print(response)
```

## Примеры тестирования через Cursor AI

### Тест 1: Проверка команды /start

```
Отправь команду /start боту my_task_tracker_bot и покажи его ответ
```

### Тест 2: Создание пространства

```
Отправь команду /newworkspace Тестовое пространство боту my_task_tracker_bot
```

### Тест 3: Проверка списка пространств

```
Отправь команду /workspaces боту my_task_tracker_bot и покажи ответ
```

## Автоматизированное тестирование

Используйте скрипт `tests/test_telegram_mcp.py` для автоматизированного тестирования:

```python
from tests.test_telegram_mcp import TelegramMCPTester

# Создаем тестер
tester = TelegramMCPTester(bot_username="your_bot_username")

# Находим чат
await tester.find_bot_chat()

# Запускаем тесты
await tester.test_command("/start", ["привет", "меню"])
await tester.test_command("/help", ["команды", "справка"])

# Выводим результаты
tester.print_results()
```

## Тестовые сценарии

### Базовые команды

1. **/start** - должен показать приветствие и меню
   - Ожидаемые ключевые слова: "привет", "меню", "start"

2. **/help** - должен показать справку по командам
   - Ожидаемые ключевые слова: "команды", "help", "справка"

3. **/menu** - должен показать главное меню
   - Ожидаемые ключевые слова: "меню", "menu"

### Пространства

4. **/workspaces** - должен показать список пространств
   - Ожидаемые ключевые слова: "пространств", "workspace"

5. **/newworkspace Тест** - должен создать новое пространство
   - Ожидаемые ключевые слова: "создан", "создано", "успешно"

6. **/delworkspace Тест** - должен удалить пространство
   - Ожидаемые ключевые слова: "удален", "удалено", "успешно"

### Доски

7. **/boards** - должен показать список досок
   - Ожидаемые ключевые слова: "доск", "board"

8. **/newboard Тестовая доска** - должен создать новую доску
   - Ожидаемые ключевые слова: "создан", "создано", "успешно"

9. **/board Тестовая доска** - должен показать доску
   - Ожидаемые ключевые слова: "доск", "колонк", "column"

### Проекты

10. **/projects** - должен показать список проектов
    - Ожидаемые ключевые слова: "проект", "project"

11. **/newproject 1001 Тестовый проект** - должен создать проект
    - Ожидаемые ключевые слова: "создан", "создано", "успешно"

12. **/project 1001** - должен показать проект
    - Ожидаемые ключевые слова: "проект", "задач", "task"

### Задачи

13. **/newtask** - должен начать процесс создания задачи
    - Ожидаемые ключевые слова: "доск", "board", "выбери"

14. **/task 1** - должен показать задачу
    - Ожидаемые ключевые слова: "задач", "task", "приоритет"

### Статистика

15. **/stats** - должен показать общую статистику
    - Ожидаемые ключевые слова: "статистик", "stat", "всего"

## Использование через Cursor AI

### Простой способ

Просто попросите Cursor AI:

```
Протестируй команду /start у бота my_task_tracker_bot через Telegram MCP
```

Cursor AI автоматически:
1. Найдет чат с ботом
2. Отправит команду
3. Получит ответ
4. Покажет результат

### Комплексное тестирование

```
Протестируй следующие команды у бота my_task_tracker_bot:
1. /start
2. /newworkspace Тест
3. /workspaces
4. /newboard Тестовая доска
5. /boards

Покажи результаты каждого теста
```

## Проверка результатов

После каждого теста проверьте:

1. **Бот ответил?** - есть ли ответ от бота
2. **Правильный ответ?** - содержит ли ответ ожидаемые ключевые слова
3. **Нет ошибок?** - нет ли сообщений об ошибках в ответе
4. **Корректный формат?** - правильно ли отформатирован ответ (кнопки, текст)

## Отладка

### Бот не отвечает

1. Проверьте, что бот запущен: `ps aux | grep bot.py`
2. Проверьте логи бота: `tail -f bot.log`
3. Проверьте токен в `.env` файле

### Чат не найден

1. Убедитесь, что вы отправили `/start` боту вручную хотя бы раз
2. Проверьте правильность username бота
3. Попробуйте найти бота через `mcp_telegram-mcp_search_contacts`

### Ошибки MCP

1. Проверьте, что MCP сервер запущен
2. Проверьте настройки Telegram MCP в Cursor
3. Убедитесь, что у MCP есть доступ к вашему Telegram аккаунту

## Полезные команды MCP

- `mcp_telegram-mcp_list_chats` - список всех чатов
- `mcp_telegram-mcp_get_chat` - информация о конкретном чате
- `mcp_telegram-mcp_send_message` - отправить сообщение
- `mcp_telegram-mcp_get_messages` - получить сообщения из чата
- `mcp_telegram-mcp_get_direct_chat_by_contact` - найти чат по username
- `mcp_telegram-mcp_search_contacts` - поиск контактов

## Пример полного теста

```python
# 1. Найти бота
chat = mcp_telegram-mcp_get_direct_chat_by_contact("my_task_tracker_bot")
chat_id = chat["id"]

# 2. Отправить /start
mcp_telegram-mcp_send_message(chat_id=chat_id, message="/start")

# 3. Подождать ответ
time.sleep(2)

# 4. Получить ответ
messages = mcp_telegram-mcp_get_messages(chat_id=chat_id, page=1, page_size=5)
bot_response = [m for m in messages["messages"] if m["from_id"] != "me"][0]

# 5. Проверить результат
assert "привет" in bot_response["text"].lower() or "меню" in bot_response["text"].lower()
print("✅ Тест пройден!")
```

## Дополнительные ресурсы

- [Документация Telegram MCP](https://github.com/your-repo/telegram-mcp)
- [Документация python-telegram-bot](https://python-telegram-bot.org/)
- [Руководство по тестированию](TESTING.md)


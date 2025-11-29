# Устранение проблем с тестом @start_test_baseCase

## Проблема: Команда не работает

Если команда `/start_test_basecase` не отвечает, выполните следующие шаги:

### 1. Перезапустите бота

**Важно:** После любых изменений в коде бота его нужно перезапустить!

```bash
# Остановите бота (Ctrl+C или kill процесс)
# Затем запустите заново:
cd /Users/ivanavgust/Documents/Proger/tg-task-treker-bot
source venv/bin/activate  # если используете venv
python task_tracker_bot/bot.py
```

### 2. Проверьте логи бота

При запуске бота вы должны увидеть в логах:
```
Обработчик тега @start_test_basecase зарегистрирован
```

Если этой строки нет, значит есть ошибка при регистрации обработчика.

### 3. Проверьте, что команда зарегистрирована

В логах при запуске бота должна быть строка:
```
КОМАНДА start_test_basecase ПОЛУЧЕНА!
```

### 4. Попробуйте разные варианты команды

1. `/start_test_basecase` - команда напрямую
2. `@start_test_basecase` - тег в тексте
3. `start_test_basecase` - просто текст

### 5. Проверьте импорты

Убедитесь, что файл `tests/test_base_case.py` существует и содержит класс `BaseCaseTestRunner`.

### 6. Проверьте права доступа к БД

Убедитесь, что бот имеет права на запись в базу данных.

### 7. Временное решение: простая команда для проверки

Если ничего не помогает, добавьте простую команду для проверки:

```python
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Бот работает!")
```

И зарегистрируйте её:
```python
application.add_handler(CommandHandler("test", test_command))
```

Если `/test` работает, а `/start_test_basecase` нет, значит проблема в обработчике теста.

## Отладка

### Включите подробное логирование

В `bot.py` измените уровень логирования:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Вместо INFO
)
```

### Проверьте обработчик команды

В `handlers/start.py` функция `start_test_basecase_command` должна:
1. Получать update
2. Отправлять ответ пользователю
3. Логировать действия

Если вы видите в логах "КОМАНДА start_test_basecase ПОЛУЧЕНА!", но ответ не приходит, значит проблема в выполнении теста.

## Частые ошибки

### Ошибка импорта модулей
```
ModuleNotFoundError: No module named 'tests'
```
**Решение:** Проверьте пути импорта в `handlers/start.py`

### Ошибка базы данных
```
sqlite3.OperationalError: database is locked
```
**Решение:** Закройте другие процессы, использующие БД

### Ошибка выполнения теста
```
AttributeError: 'NoneType' object has no attribute 'id'
```
**Решение:** Проверьте, что workspace_id не None перед использованием

## Контакты

Если проблема не решена, проверьте:
1. Логи бота (`bot.log` или консольный вывод)
2. Структуру файлов проекта
3. Версии зависимостей в `requirements.txt`


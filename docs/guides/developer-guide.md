# Руководство разработчика

> **Дата создания:** 2025-01-28  
> **Обновлено:** 2025-01-28

Практическое руководство по разработке и расширению Task Tracker Bot.

## Введение

Это руководство поможет разработчикам понять структуру проекта, архитектуру и процесс разработки.

## Структура проекта

```
task_tracker_bot/
├── bot.py                 # Главный файл, точка входа
├── config.py              # Конфигурация
├── database.py            # Инициализация БД
├── models/                # Модели данных
│   ├── workspace.py
│   ├── board.py
│   ├── column.py
│   ├── project.py
│   ├── task.py
│   └── ...
├── repositories/          # Репозитории (Data Access)
│   ├── workspace_repository.py
│   ├── board_repository.py
│   └── ...
├── services/              # Бизнес-логика
│   ├── workspace_service.py
│   ├── board_service.py
│   ├── project_service.py
│   ├── task_service.py
│   └── ...
├── handlers/              # Обработчики команд
│   ├── start.py
│   ├── workspace.py
│   ├── board.py
│   ├── project.py
│   └── ...
├── callbacks/             # Обработка callback-запросов
│   ├── workspace_callbacks.py
│   ├── board_callbacks.py
│   └── ...
├── utils/                 # Утилиты
│   ├── keyboards.py
│   ├── formatters.py
│   ├── validators.py
│   └── board_visualizer.py
├── agents/                # AI-агенты
│   ├── agent_coordinator.py
│   ├── orchestrator.py
│   └── ...
└── tests/                 # Тесты
    ├── test_repositories.py
    ├── test_services.py
    └── ...
```

## Архитектура

### Многослойная архитектура

```
Telegram Bot API
    ↓
Bot Layer (Handlers, Callbacks)
    ↓
Business Logic Layer (Services)
    ↓
Data Access Layer (Repositories)
    ↓
Database (SQLite)
```

### Слои

#### 1. Bot Layer
- **Handlers** - обработчики команд Telegram (`/start`, `/workspaces` и т.д.)
- **Callbacks** - обработка inline-кнопок и callback-запросов
- **Middlewares** - промежуточное ПО для обработки запросов

#### 2. Business Logic Layer
- **Services** - бизнес-логика приложения
- Валидация данных
- Обработка бизнес-правил
- Координация работы репозиториев

#### 3. Data Access Layer
- **Repositories** - абстракция доступа к данным
- Работа с базой данных
- Преобразование данных между БД и моделями

#### 4. Database Layer
- SQLite база данных
- Таблицы и индексы
- Миграции

## Разработка новых функций

### Шаг 1: Планирование
1. Определите требования к функции
2. Изучите существующие паттерны
3. Спланируйте изменения в БД (если нужны)

### Шаг 2: Модель данных
Если нужна новая сущность:
1. Создайте модель в `models/`
2. Создайте таблицу в БД (миграция)
3. Создайте репозиторий в `repositories/`

### Шаг 3: Бизнес-логика
1. Создайте или обновите сервис в `services/`
2. Реализуйте бизнес-логику
3. Добавьте валидацию

### Шаг 4: Handlers
1. Создайте или обновите handler в `handlers/`
2. Зарегистрируйте команду в `bot.py`
3. Добавьте обработку ошибок

### Шаг 5: Тесты
1. Напишите unit тесты для репозитория
2. Напишите unit тесты для сервиса
3. Напишите интеграционные тесты для handler

### Шаг 6: Документация
1. Обновите документацию
2. Добавьте примеры использования
3. Обновите README при необходимости

## Пример: Добавление новой команды

### Пример: Команда `/mytasks`

#### 1. Обновить TaskRepository
```python
# repositories/task_repository.py
def get_tasks_by_assignee(self, user_id: int, workspace_id: int) -> List[Task]:
    # Реализация
```

#### 2. Обновить TaskService
```python
# services/task_service.py
def get_user_tasks(self, user_id: int, workspace_id: int) -> List[Task]:
    return self.task_repository.get_tasks_by_assignee(user_id, workspace_id)
```

#### 3. Создать Handler
```python
# handlers/task.py
async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    workspace_id = get_current_workspace(user_id)
    
    tasks = task_service.get_user_tasks(user_id, workspace_id)
    # Форматирование и отправка
```

#### 4. Зарегистрировать в bot.py
```python
# bot.py
application.add_handler(CommandHandler("mytasks", mytasks_command))
```

#### 5. Написать тесты
```python
# tests/test_task_service.py
def test_get_user_tasks():
    # Тест
```

## Тестирование

### Unit тесты
```bash
pytest task_tracker_bot/tests/test_repositories.py -v
pytest task_tracker_bot/tests/test_services.py -v
```

### Интеграционные тесты
```bash
pytest task_tracker_bot/tests/test_integration.py -v
```

### Все тесты
```bash
pytest task_tracker_bot/tests/ -v
```

### С покрытием
```bash
pytest task_tracker_bot/tests/ --cov=task_tracker_bot --cov-report=html
```

## Стандарты кодирования

### Стиль кода
- Следуйте PEP 8
- Используйте type hints
- Пишите docstrings для функций и классов

### Именование
- Классы: `PascalCase`
- Функции и переменные: `snake_case`
- Константы: `UPPER_SNAKE_CASE`

### Структура файлов
- Один класс на файл (если возможно)
- Логическое группирование функций
- Импорты в начале файла

## Работа с базой данных

### Миграции
1. Создайте SQL файл в `migrations/`
2. Создайте Python скрипт для миграции
3. Протестируйте миграцию

### Запросы
- Используйте параметризованные запросы
- Всегда проверяйте существование ресурсов
- Используйте транзакции для множественных операций

## Обработка ошибок

### Валидация
- Валидируйте все входные данные
- Проверяйте существование ресурсов
- Проверяйте права доступа

### Сообщения об ошибках
- Понятные сообщения для пользователя
- Логирование ошибок для разработчиков
- Не раскрывайте внутренние детали

## Дополнительные ресурсы

- [Архитектура системы](../architecture/system-overview.md) - архитектурное описание
- [Правила разработки](../development/rules.md) - стандарты кодирования
- [Техническая спецификация](../specifications/technical.md) - технические детали
- [Тестирование](../testing/README.md) - руководство по тестированию


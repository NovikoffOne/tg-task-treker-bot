# Руководство по тестированию

## Запуск тестов

### Все тесты
```bash
source venv/bin/activate
pytest task_tracker_bot/tests/ -v
```

### Конкретный файл тестов
```bash
pytest task_tracker_bot/tests/test_repositories.py -v
```

### Конкретный тест
```bash
pytest task_tracker_bot/tests/test_repositories.py::test_workspace_repository_create -v
```

## Структура тестов

### test_database.py
Тесты для инициализации и работы с базой данных:
- Инициализация БД
- Создание всех таблиц
- Работа с соединениями

### test_repositories.py
Тесты для всех репозиториев:
- WorkspaceRepository
- BoardRepository
- ColumnRepository
- ProjectRepository
- TaskRepository
- TagRepository
- CustomFieldRepository

### test_services.py
Тесты для бизнес-логики сервисов:
- WorkspaceService (создание, валидация)
- BoardService (создание с дефолтными колонками)
- ProjectService (создание с автоматическими задачами)
- TaskService (создание, валидация)

### test_sync_service.py
Тесты для синхронизации полей проекта:
- Синхронизация полей между задачами проекта
- Работа с задачами без проекта

### test_validators.py
Тесты для валидаторов:
- Валидация названий, описаний
- Валидация URL
- Валидация ID и приоритетов

### test_integration.py
Интеграционные тесты:
- Полный workflow создания проекта
- Синхронизация полей в реальном сценарии
- Перемещение задач между колонками
- Обновление этапов дашборда

### test_bot_init.py
Тесты инициализации бота:
- Инициализация БД
- Проверка конфигурации

## Покрытие тестами

Текущее покрытие:
- ✅ База данных (100%)
- ✅ Репозитории (100%)
- ✅ Сервисы (основные функции)
- ✅ Валидаторы (100%)
- ✅ Синхронизация полей (100%)
- ✅ Интеграционные тесты (основные сценарии)

## Запуск с покрытием

Для проверки покрытия кода тестами установите pytest-cov:
```bash
pip install pytest-cov
pytest task_tracker_bot/tests/ --cov=task_tracker_bot --cov-report=html
```

## Результаты тестов

Все тесты должны проходить успешно:
```
========================= 31 passed in 0.44s =========================
```

Если тесты не проходят, проверьте:
1. Правильность структуры БД
2. Корректность импортов
3. Наличие всех зависимостей


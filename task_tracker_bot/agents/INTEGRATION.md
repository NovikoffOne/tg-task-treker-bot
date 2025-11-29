# Руководство по интеграции AI-агентов в Telegram бот

## Обзор

Система AI-агентов интегрирована в Telegram бот через гибридный подход:
- Существующие команды остаются без изменений
- Добавлен AI-режим для обработки естественных запросов

## Использование в Telegram боте

### Активация AI-режима

Пользователь может активировать AI-режим командой `/ai` или просто начать писать естественные запросы.

### Примеры запросов

```
Создай новый проект id+ Polaroid Photo
Добавь туда тз https://docs.google.com/document/d/1szVadGJBKWQdSpH-tYz_dGEsuh9VqdAvDQ0PWFgkF7g/edit
Добавь реф: https://apps.apple.com/us/app/polaroid/id1421833880
Закрой задачу на доске Подготовка в готово
Сколько задач у нас в работе?
Покажи график эффективности сотрудников
Где у нас узкое горлышко?
```

## Архитектура интеграции

```
Telegram Bot Message
    ↓
AI Handler (handlers/ai_handler.py)
    ↓
AgentCoordinator (agents/agent_coordinator.py)
    ↓
OrchestratorAgent (анализ запроса, составление плана)
    ↓
┌───────────┬───────────┬───────────┐
│    ATM    │    ADM    │    AAM     │
│  (Task    │  (Data    │ (Analyze   │
│ Manager)  │ Manager)  │ Manager)   │
└───────────┴───────────┴───────────┘
    ↓
ACM (Control Manager) - проверка корректности
    ↓
Форматированный ответ для Telegram
```

## Компоненты

### 1. AI Handler (`handlers/ai_handler.py`)

Обрабатывает естественные запросы пользователей:
- Определяет, является ли сообщение естественным запросом (не командой)
- Получает workspace пользователя
- Передает запрос в AgentCoordinator
- Форматирует ответ для Telegram

**Основные функции:**
- `ai_command()` - команда `/ai` для активации AI-режима
- `handle_ai_message()` - обработчик естественных запросов

### 2. Agent Coordinator (`agents/agent_coordinator.py`)

Координирует работу всех агентов:
- Инициализирует все агенты с правильными зависимостями
- Обрабатывает запросы через Оркестратор
- Выполняет план выполнения
- Проверяет корректность через ACM
- Форматирует ответы для Telegram

**Основные методы:**
- `process_user_message()` - обработка сообщения пользователя
- `format_response_for_telegram()` - форматирование ответа

### 3. Агенты

#### OrchestratorAgent
Анализирует запросы и составляет план выполнения.

#### TaskManagerAgent (ATM)
Управление задачами и проектами:
- Создание проектов
- Добавление ссылок к проектам
- Закрытие задач

#### DataManagerAgent (ADM)
Единственная точка доступа к БД через сервисы:
- Работа с проектами
- Работа с задачами
- Работа с досками
- Получение данных для анализа

#### ControlManagerAgent (ACM)
Проверка корректности данных и бизнес-правил:
- Валидация проектов
- Валидация задач
- Проверка бизнес-правил

#### AnalyzeManagerAgent (AAM)
Аналитика и отчеты:
- Метрики задач
- Эффективность сотрудников
- Поиск узких мест

## Настройка

### Переменные окружения

```bash
# Обязательные
IO_NET_API_KEY=io-v2-...

# Опциональные (есть значения по умолчанию)
IO_NET_MODEL=deepseek-ai/DeepSeek-R1-0528
IO_NET_TEMPERATURE=0.3
IO_NET_MAX_TOKENS=2000
IO_NET_API_URL=https://api.intelligence.io.solutions/api/v1/chat/completions
```

### Конфигурация через Config

Все настройки доступны через `config.Config`:
- `Config.IO_NET_API_KEY`
- `Config.IO_NET_MODEL`
- `Config.IO_NET_TEMPERATURE`
- `Config.IO_NET_MAX_TOKENS`
- `Config.IO_NET_API_URL`

## Примеры использования

### Пример 1: Создание проекта

```python
from agents.agent_coordinator import AgentCoordinator
from database import Database

coordinator = AgentCoordinator(db=Database())

result = coordinator.process_user_message(
    user_message="Создай новый проект id+ Polaroid Photo",
    workspace_id=1,
    user_id=123456
)

print(coordinator.format_response_for_telegram(result))
```

### Пример 2: Добавление ссылки

```python
result = coordinator.process_user_message(
    user_message="Добавь тз https://docs.google.com/... к проекту 5005",
    workspace_id=1,
    user_id=123456
)
```

### Пример 3: Аналитика

```python
result = coordinator.process_user_message(
    user_message="Сколько задач у нас в работе?",
    workspace_id=1,
    user_id=123456
)
```

## Обработка ошибок

Система обрабатывает следующие типы ошибок:
- Ошибки API io.net (таймауты, HTTP ошибки)
- Ошибки БД (не найдены данные, ошибки валидации)
- Ошибки бизнес-логики (некорректные параметры)

Все ошибки логируются и возвращаются пользователю в понятном формате.

## Логирование

Все действия агентов логируются через стандартный модуль `logging`:
- Уровень INFO для успешных операций
- Уровень ERROR для ошибок
- Уровень WARNING для предупреждений

## Тестирование

Тесты находятся в `tests/test_agents.py`:
- Unit тесты для каждого агента
- Интеграционные тесты для AgentCoordinator
- Моки для API и БД

Запуск тестов:
```bash
pytest tests/test_agents.py -v
```

## Расширение функциональности

### Добавление нового агента

1. Создайте класс агента, наследующийся от `BaseAgent`
2. Реализуйте метод `get_system_prompt()`
3. Добавьте агент в `AgentCoordinator.__init__()`
4. Обновите `OrchestratorAgent.get_system_prompt()` для включения нового агента

### Добавление новых действий

1. Добавьте метод в соответствующий агент
2. Обновите промпт Оркестратора для распознавания нового действия
3. Добавьте тесты для нового функционала

## Troubleshooting

### Проблема: API ключ не найден

**Решение:** Убедитесь, что:
- Файл `task_tracker_bot/tg_aitt_service/io_net_api_key.txt` существует и содержит ключ
- Или установлена переменная окружения `IO_NET_API_KEY`

### Проблема: Агенты не работают

**Решение:** Проверьте:
- Логи на наличие ошибок API
- Правильность endpoint URL
- Доступность io.net API

### Проблема: Неправильные результаты

**Решение:**
- Проверьте промпты агентов
- Убедитесь, что модель поддерживает JSON формат ответов
- Проверьте логи выполнения плана


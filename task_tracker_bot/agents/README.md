# Система AI-агентов для Task Tracker Bot

## Описание

Система из 5 специализированных AI-агентов на базе io.net AI API для автоматизации работы с задачами и проектами в Telegram боте.

## Быстрый старт

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
   Убедитесь, что `requests` установлен.

2. **Настройте API ключ io.net:**
   
   API ключ должен быть сохранен в файле `task_tracker_bot/tg_aitt_service/io_net_api_key.txt`
   или установлен через переменную окружения:
   ```bash
   export IO_NET_API_KEY="io-v2-..."
   ```
   
   Также можно настроить через `.env` файл:
   ```bash
   IO_NET_API_KEY=io-v2-...
   IO_NET_MODEL=deepseek-ai/DeepSeek-R1-0528
   IO_NET_TEMPERATURE=0.3
   IO_NET_MAX_TOKENS=2000
   IO_NET_API_URL=https://api.intelligence.io.solutions/api/v1/chat/completions
   ```

3. **Используйте в коде:**
   ```python
   from agents.agent_coordinator import AgentCoordinator
   from database import Database
   
   db = Database()
   coordinator = AgentCoordinator(db=db)
   
   result = coordinator.process_user_message(
       user_message="Создай новый проект id+ Polaroid Photo",
       workspace_id=1,
       user_id=123456
   )
   
   # Форматировать ответ для Telegram
   response_text = coordinator.format_response_for_telegram(result)
   ```

## Архитектура

Система состоит из 5 агентов:

1. **Оркестратор** - анализирует запросы и координирует работу
2. **ATM (Task Manager)** - управление задачами и проектами
3. **ACM (Control Manager)** - проверка корректности данных
4. **ADM (Data Manager)** - работа с базой данных
5. **AAM (Analyze Manager)** - аналитика и отчеты

Подробнее см. `ARCHITECTURE.md`

## Документация

- `ARCHITECTURE.md` - подробное описание архитектуры агентов
- `INTEGRATION.md` - руководство по интеграции с ботом (см. ниже)
- `README.md` - этот файл

## Примеры использования

### В Telegram боте

Просто напишите естественный запрос:
```
Создай новый проект id+ Polaroid Photo
Добавь тз https://docs.google.com/... к проекту 5005
Закрой задачу на доске Подготовка
```

### Программно

```python
from agents.agent_coordinator import AgentCoordinator
from database import Database

coordinator = AgentCoordinator(db=Database())
result = coordinator.process_user_message(
    user_message="Создай проект id+ Test",
    workspace_id=1,
    user_id=123456
)
```

## Модель по умолчанию

Используется **deepseek-ai/DeepSeek-R1-0528** - экономичная модель (~7B параметров) с отличным пониманием JSON и структурированных данных.

Альтернатива: `Llama-4-Maverick-17B-128E-Instruct-FP8` для большей точности.

## Интеграция

Система интегрирована в Telegram бот через:
- Команду `/ai` для активации AI-режима
- Автоматическую обработку естественных запросов

Подробнее см. `INTEGRATION.md`



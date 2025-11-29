# Архитектура системы

> **Дата создания:** 2025-01-28  
> **Обновлено:** 2025-01-28

Этот раздел содержит документацию по архитектуре Task Tracker Bot.

## Обзор

Task Tracker Bot построен на многослойной архитектуре с четким разделением ответственности:

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

## Документация

### Основная архитектура
- [Системная архитектура](system-overview.md) - общая архитектура системы, модели данных, потоки данных
- [Схема базы данных](database-schema.md) - структура базы данных, таблицы, связи
- [Структура кода](code-structure.md) - организация файлов и модулей проекта

### Архитектура агентов
- [Обзор агентов](agents/README.md) - система AI-агентов
- [Архитектура агентов](agents/overview.md) - детальное описание архитектуры
- [Интеграция агентов](../guides/agents/integration.md) - как интегрировать агентов

## Ключевые компоненты

### 1. Bot Layer
- **Handlers** - обработчики команд Telegram
- **Callbacks** - обработка inline-кнопок и callback-запросов
- **Middlewares** - промежуточное ПО для обработки запросов

### 2. Business Logic Layer
- **WorkspaceService** - управление пространствами
- **BoardService** - управление досками и колонками
- **ProjectService** - управление проектами
- **TaskService** - управление задачами
- **SyncService** - синхронизация полей проекта
- **StatisticsService** - статистика и аналитика

### 3. Data Access Layer
- **Repositories** - абстракция доступа к данным
- **Models** - модели данных
- **Database** - работа с SQLite

### 4. AI Agents Layer
- **AgentCoordinator** - координация работы агентов
- **OrchestratorAgent** - анализ запросов
- **TaskManagerAgent** - управление задачами
- **DataManagerAgent** - работа с БД
- **ControlManagerAgent** - проверка данных
- **AnalyzeManagerAgent** - аналитика

## Модель данных

### Иерархия сущностей

```
User (Telegram User)
  └── Workspace (Пространство)
      ├── Board (Доска)
      │   └── Column (Колонка)
      │       └── Task (Задача)
      │           ├── Tag (Метка)
      │           ├── CustomField (Поле)
      │           └── Priority (Приоритет)
      └── Project (Проект)
          └── Tasks (Задачи на разных досках)
              └── SyncFields (Синхронизация полей)
```

## Потоки данных

### Создание проекта
1. User → `/newproject`
2. Handler → ProjectService
3. ProjectService → ProjectRepository (создание проекта)
4. ProjectService → TaskService (создание задач на досках)
5. TaskService → TaskRepository (создание задач)
6. Response → User

### Синхронизация полей
1. User → `/addfield`
2. Handler → TaskService
3. TaskService → SyncService (проверка проекта)
4. SyncService → TaskRepository (обновление всех задач проекта)
5. Response → User

## Производительность

- Использование индексов для часто запрашиваемых полей
- Оптимизация запросов к БД
- Кэширование структуры досок (если применимо)
- Транзакции для операций изменения нескольких таблиц

## Масштабируемость

Текущая архитектура поддерживает:
- Множество пространств на пользователя
- Множество досок в пространстве
- Множество колонок в доске
- Множество задач в колонке
- Множество проектов

Для больших объемов данных можно:
- Добавить пагинацию для списков
- Оптимизировать запросы
- Рассмотреть миграцию на PostgreSQL

## Дополнительные ресурсы

- [Техническая спецификация](../specifications/technical.md) - технические детали реализации
- [Руководство разработчика](../guides/developer-guide.md) - практическое руководство
- [Правила разработки](../development/rules.md) - стандарты кодирования


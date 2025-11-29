# Архитектура: Advanced Telegram Task Tracker Bot

> **Дата создания:** 2025-01-28  
> **Обновлено:** 2025-01-29

## Общая архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot API                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Bot Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Handlers   │  │  Callbacks   │  │  Middleware  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Workspaces  │  │   Boards     │  │  Projects    │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Tasks      │  │  Statistics  │  │  Sync        │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Workspace   │  │   Board      │  │  Project     │      │
│  │   Repository │  │  Repository │  │  Repository  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Task       │  │   Field      │  │  Tag        │      │
│  │  Repository  │  │  Repository  │  │ Repository  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (SQLite)                         │
│  workspaces │ boards │ columns │ projects │ tasks │ ...     │
└─────────────────────────────────────────────────────────────┘
```

## Модель данных

### Иерархия сущностей

```
User (Telegram User)
  └── Workspace (Пространство: Работа/Дом/Спорт)
      └── Board (Доска: Дизайн/Разработка/Тестирование)
          └── Column (Колонка: Очередь/В работе/Готово)
              └── Task (Задача)
                  ├── SubTask (Подзадача)
                  ├── Tag (Метка)
                  ├── CustomField (Динамическое поле)
                  └── Priority (Приоритет)
      
      └── Project (Проект: 5010 Nano Banana Ai)
          ├── Dashboard (Дашборд с этапами)
          └── Tasks (Задачи проекта на разных досках)
              └── SyncFields (Синхронизация полей)
```

### Схема базы данных

#### Таблица: workspaces
```sql
CREATE TABLE workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

CREATE INDEX idx_workspaces_user_id ON workspaces(user_id);
```

#### Таблица: boards
```sql
CREATE TABLE boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(workspace_id, name)
);

CREATE INDEX idx_boards_workspace_id ON boards(workspace_id);
CREATE INDEX idx_boards_position ON boards(workspace_id, position);
```

#### Таблица: columns
```sql
CREATE TABLE columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
    UNIQUE(board_id, name)
);

CREATE INDEX idx_columns_board_id ON columns(board_id);
CREATE INDEX idx_columns_position ON columns(board_id, position);
```

#### Таблица: projects
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,  -- Настраиваемый ID (например, "5010")
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    dashboard_stage TEXT DEFAULT 'preparation',  -- Текущий этап дашборда
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX idx_projects_workspace_id ON projects(workspace_id);
CREATE INDEX idx_projects_dashboard_stage ON projects(dashboard_stage);
```

#### Таблица: tasks
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,  -- NULL если задача не связана с проектом
    column_id INTEGER NOT NULL,
    parent_task_id INTEGER,  -- NULL если это не подзадача
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 0,  -- 0=низкий, 1=средний, 2=высокий, 3=критический
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_tasks_column_id ON tasks(column_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_position ON tasks(column_id, position);
```

#### Таблица: task_tags
```sql
CREATE TABLE task_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#3498db',  -- HEX цвет
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(workspace_id, name)
);

CREATE INDEX idx_task_tags_workspace_id ON task_tags(workspace_id);
```

#### Таблица: task_tag_relations
```sql
CREATE TABLE task_tag_relations (
    task_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES task_tags(id) ON DELETE CASCADE
);
```

#### Таблица: custom_fields
```sql
CREATE TABLE custom_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    field_type TEXT NOT NULL,  -- 'text', 'url', 'number', 'date', 'select'
    default_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(workspace_id, name)
);

CREATE INDEX idx_custom_fields_workspace_id ON custom_fields(workspace_id);
```

#### Таблица: task_custom_fields
```sql
CREATE TABLE task_custom_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
    UNIQUE(task_id, field_id)
);

CREATE INDEX idx_task_custom_fields_task_id ON task_custom_fields(task_id);
CREATE INDEX idx_task_custom_fields_field_id ON task_custom_fields(field_id);
```

#### Таблица: project_field_sync
```sql
CREATE TABLE project_field_sync (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    field_id INTEGER NOT NULL,
    sync_enabled BOOLEAN DEFAULT 1,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
    UNIQUE(project_id, field_id)
);

CREATE INDEX idx_project_field_sync_project_id ON project_field_sync(project_id);
```

## Структура проекта

```
task_tracker_bot/
├── bot.py                      # Главный файл
├── config.py                   # Конфигурация
├── database.py                 # Инициализация БД
├── models/                     # Модели данных
│   ├── __init__.py
│   ├── workspace.py
│   ├── board.py
│   ├── column.py
│   ├── project.py
│   ├── task.py
│   ├── personal_task.py        # НОВОЕ: Модель личных задач
│   ├── tag.py
│   └── custom_field.py
├── repositories/               # Репозитории (Data Access)
│   ├── __init__.py
│   ├── workspace_repository.py
│   ├── board_repository.py
│   ├── column_repository.py
│   ├── project_repository.py
│   ├── task_repository.py
│   ├── personal_task_repository.py  # НОВОЕ: Репозиторий личных задач
│   ├── tag_repository.py
│   └── custom_field_repository.py
├── services/                  # Бизнес-логика
│   ├── __init__.py
│   ├── workspace_service.py
│   ├── board_service.py
│   ├── project_service.py
│   ├── task_service.py
│   ├── todo_service.py         # НОВОЕ: Сервис туду-листа
│   ├── sync_service.py        # Синхронизация полей проекта
│   └── statistics_service.py
├── handlers/                  # Обработчики команд
│   ├── __init__.py
│   ├── start.py
│   ├── workspace.py
│   ├── board.py
│   ├── project.py
│   ├── task.py
│   ├── field.py
│   ├── tag.py
│   └── statistics.py
├── callbacks/                 # Обработка callback-запросов
│   ├── __init__.py
│   ├── workspace_callbacks.py
│   ├── board_callbacks.py
│   ├── project_callbacks.py
│   ├── task_callbacks.py
│   └── navigation_callbacks.py
├── utils/                     # Утилиты
│   ├── __init__.py
│   ├── keyboards.py
│   ├── formatters.py
│   ├── validators.py
│   ├── date_parser.py         # НОВОЕ: Парсер дат и времени
│   ├── task_classifier.py     # НОВОЕ: Классификатор задач
│   └── board_visualizer.py   # Визуализация досок
└── data/                      # База данных
    └── tasks.db
```

## Ключевые компоненты

### 1. Workspace Service
**Ответственность:** Управление пространствами
- Создание/удаление/переименование пространств
- Валидация уникальности имен
- Управление досками в пространстве

### 2. Board Service
**Ответственность:** Управление досками и колонками
- Создание/удаление досок
- Управление колонками (создание, удаление, изменение порядка)
- Валидация структуры доски

### 3. Project Service
**Ответственность:** Управление проектами
- Создание проекта с настраиваемым ID
- Управление дашбордом проекта (этапы)
- Автоматическое создание задач проекта на досках
- Отслеживание прогресса проекта

### 4. Task Service
**Ответственность:** Управление задачами
- Создание/редактирование/удаление задач
- Управление подзадачами
- Перемещение задач между колонками
- Управление приоритетами
- Привязка задач к проектам

### 5. Sync Service
**Ответственность:** Синхронизация полей проекта
- При добавлении поля в задачу проекта → синхронизация с другими задачами проекта
- Отслеживание изменений полей
- Обновление связанных задач

### 6. Statistics Service
**Ответственность:** Статистика
- Статистика по проектам
- Статистика по доскам
- Статистика по задачам
- Прогресс проектов

### 7. Board Visualizer
**Ответственность:** Визуализация досок
- Генерация текстового представления доски
- Отображение задач в колонках
- Показ приоритетов, меток, статусов

### 8. Todo Service
**Ответственность:** Управление туду-листом
- Пакетное создание задач (личные + рабочие)
- Получение туду-листа на указанную дату
- Группировка задач по времени выполнения
- Отметка задач как выполненных

### 9. Date Parser
**Ответственность:** Парсинг дат и времени
- Извлечение дат из естественного языка ("завтра", "03.12")
- Парсинг времени ("10:00", "11:10 - 12:00")
- Определение относительных дат
- Валидация и нормализация данных

### 10. Task Classifier
**Ответственность:** Определение типа задач
- Классификация задач на личные и рабочие
- Извлечение project_id из текста задачи
- Проверка существования проектов
- Очистка заголовков задач

## Потоки данных

### Создание проекта
```
User: /newproject 5010 Nano Banana Ai
  ↓
Project Service: Создать проект
  ↓
Database: INSERT INTO projects
  ↓
Task Service: Создать задачи на досках
  - "5010 Nano Banana Ai Дизайн" → доска "Дизайн"
  - "5010 Nano Banana Ai Разработка" → доска "Разработка"
  - "5010 Nano Banana Ai Тестирование" → доска "Тестирование"
  ↓
Database: INSERT INTO tasks (с project_id)
  ↓
Ответ пользователю: Проект создан, задачи созданы
```

### Добавление поля в задачу проекта
```
User: /add figma https://figma.com/...
  ↓
Task Service: Добавить поле к задаче
  ↓
Database: INSERT/UPDATE task_custom_fields
  ↓
Sync Service: Найти все задачи проекта
  ↓
Sync Service: Добавить поле ко всем задачам проекта
  ↓
Database: INSERT/UPDATE task_custom_fields для всех задач
  ↓
Ответ пользователю: Поле добавлено и синхронизировано
```

### Перемещение задачи между колонками
```
User: [Перетаскивает задачу или использует команду]
  ↓
Task Service: Обновить column_id и position
  ↓
Database: UPDATE tasks SET column_id=?, position=?
  ↓
Если задача проекта → обновить дашборд проекта
  ↓
Ответ пользователю: Задача перемещена
```

## Дашборд проекта

Этапы дашборда (dashboard_stage):
- `preparation` - Подготовка
- `design` - Дизайн
- `development` - Разработка
- `testing` - Тестирование
- `submission` - На отправку
- `moderation` - Модерация
- `rejected` - Реджект
- `published` - Опубликовано

Автоматическое определение этапа на основе колонок задач:
- Если задача в колонке "Готово" доски "Дизайн" → stage = "design"
- Если задача в колонке "Готово" доски "Разработка" → stage = "development"
- И т.д.

## Приоритеты задач

Уровни приоритета:
- `0` - Низкий (Low)
- `1` - Средний (Medium)
- `2` - Высокий (High)
- `3` - Критический (Critical)

Отображение:
- 🔴 Критический
- 🟠 Высокий
- 🟡 Средний
- 🟢 Низкий

## Метки (Tags)

- Метки создаются на уровне пространства
- Метки можно назначать задачам
- Метки имеют цвета для визуального различия
- Метки можно фильтровать

## Динамические поля

Типы полей:
- `text` - Текст
- `url` - Ссылка (Figma, Git, и т.д.)
- `number` - Число
- `date` - Дата
- `select` - Выбор из списка

Поля создаются на уровне пространства и могут использоваться во всех задачах пространства.

## Визуализация досок

Формат отображения доски:
```
📋 Доска: Дизайн

┌─────────────┬─────────────┬─────────────┐
│   Очередь   │  В работе    │   Готово    │
├─────────────┼─────────────┼─────────────┤
│ 🔴 #1 Task1 │ 🟠 #2 Task2  │ ✅ #3 Task3 │
│ 🟡 #4 Task4 │             │             │
└─────────────┴─────────────┴─────────────┘
```

Или текстовый формат для Telegram:
```
📋 Доска: Дизайн

📌 Колонка: Очередь
  🔴 #1 Task1 [High]
  🟡 #4 Task4 [Medium]

📌 Колонка: В работе
  🟠 #2 Task2 [High]

📌 Колонка: Готово
  ✅ #3 Task3 [Low]
```

## Команды бота (расширенный список)

### Пространства
- `/workspaces` - Список пространств
- `/newworkspace <name>` - Создать пространство
- `/delworkspace <name>` - Удалить пространство
- `/renameworkspace <old> <new>` - Переименовать

### Доски
- `/boards` - Список досок текущего пространства
- `/newboard <name>` - Создать доску
- `/delboard <name>` - Удалить доску
- `/board <name>` - Показать доску

### Колонки
- `/columns <board>` - Список колонок доски
- `/addcolumn <board> <name>` - Добавить колонку
- `/delcolumn <board> <name>` - Удалить колонку

### Проекты
- `/projects` - Список проектов
- `/newproject <id> <name>` - Создать проект
- `/project <id>` - Показать проект и дашборд
- `/projectdashboard <id>` - Показать дашборд проекта

### Задачи
- `/newtask` - Создать задачу
- `/task <id>` - Показать задачу
- `/movetask <id> <column>` - Переместить задачу
- `/priority <id> <level>` - Установить приоритет
- `/addtag <id> <tag>` - Добавить метку
- `/addfield <id> <field> <value>` - Добавить поле

### Статистика
- `/stats` - Общая статистика
- `/statsproject <id>` - Статистика проекта
- `/statsboard <name>` - Статистика доски

### Визуализация
- `/board <name>` - Показать доску визуально
- `/boardview <name>` - Полный вид доски

### Todo List (Новое)
- `/todo [дата]` - Показать туду-лист на указанную дату (по умолчанию сегодня)
- Пакетное добавление через AI: "Добавь на завтра задачи..." (естественный язык)

## Обработка ошибок

Все операции должны:
1. Валидировать входные данные
2. Проверять существование ресурсов
3. Проверять права доступа (пользователь может работать только со своими данными)
4. Обрабатывать ошибки БД
5. Показывать понятные сообщения пользователю

## Производительность

- Использовать индексы для часто запрашиваемых полей
- Кэшировать структуру досок (если применимо)
- Оптимизировать запросы синхронизации полей
- Использовать транзакции для операций изменения нескольких таблиц

## Масштабируемость

Текущая архитектура поддерживает:
- Множество пространств на пользователя
- Множество досок в пространстве
- Множество колонок в доске
- Множество задач в колонке
- Множество проектов
- Множество полей и меток
- Множество личных задач на пользователя (Todo List)
- Пакетное создание задач через AI агентов

Для больших объемов данных можно:
- Добавить пагинацию для списков
- Оптимизировать запросы
- Рассмотреть миграцию на PostgreSQL


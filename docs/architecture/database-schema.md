# Схема базы данных

> **Дата создания:** 2025-01-28  
> **Обновлено:** 2025-01-29

Подробное описание схемы базы данных Task Tracker Bot.

## Обзор

База данных использует SQLite и состоит из следующих основных таблиц:

- `workspaces` - пространства пользователей
- `boards` - доски в пространствах
- `columns` - колонки на досках
- `projects` - проекты
- `tasks` - задачи
- `personal_tasks` - личные задачи пользователей (Todo List)
- `task_tags` - метки задач
- `task_tag_relations` - связи задач и меток
- `custom_fields` - динамические поля
- `task_custom_fields` - значения полей задач
- `project_field_sync` - синхронизация полей проекта

## Таблицы

### workspaces

Пространства пользователей (Работа, Дом, Спорт и т.д.).

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

### boards

Доски в пространствах (Kanban-доски).

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

### columns

Колонки на досках (Очередь, В работе, Готово и т.д.).

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

### projects

Проекты с настраиваемым ID.

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

### tasks

Задачи в колонках досок.

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
    assignee_id INTEGER,  -- Основной ответственный
    started_at TIMESTAMP,  -- Дата начала работы
    completed_at TIMESTAMP,  -- Дата завершения
    deadline TIMESTAMP,  -- Дедлайн задачи
    scheduled_date DATE,  -- Дата выполнения (для Todo List)
    scheduled_time TIME,  -- Время выполнения (для Todo List)
    scheduled_time_end TIME,  -- Конец временного диапазона (для Todo List)
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
CREATE INDEX idx_tasks_scheduled_date ON tasks(scheduled_date);
CREATE INDEX idx_tasks_project_scheduled ON tasks(project_id, scheduled_date) WHERE project_id IS NOT NULL;
CREATE INDEX idx_tasks_scheduled_datetime ON tasks(scheduled_date, scheduled_time) WHERE scheduled_date IS NOT NULL;
```

**Примечание:** Поля `scheduled_date`, `scheduled_time`, `scheduled_time_end` добавлены для поддержки функционала Todo List. Они используются для задач с датами выполнения.

### personal_tasks

Личные задачи пользователей (Todo List). Отдельная таблица для задач, не связанных с проектами.

```sql
CREATE TABLE personal_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    scheduled_date DATE NOT NULL,  -- Дата выполнения
    scheduled_time TIME,  -- Время выполнения (опционально)
    scheduled_time_end TIME,  -- Конец временного диапазона (опционально)
    deadline DATETIME,  -- Дедлайн (если указан)
    completed BOOLEAN DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_personal_tasks_user_date ON personal_tasks(user_id, scheduled_date);
CREATE INDEX idx_personal_tasks_deadline ON personal_tasks(deadline);
CREATE INDEX idx_personal_tasks_completed ON personal_tasks(user_id, completed);
CREATE INDEX idx_personal_tasks_user_completed ON personal_tasks(user_id, completed, scheduled_date);
```

**Примечание:** Таблица `personal_tasks` используется для хранения личных задач пользователей, которые не связаны с проектами. Эти задачи отображаются в туду-листе вместе с рабочими задачами из таблицы `tasks`.

### task_tags

Метки задач на уровне пространства.

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

### task_tag_relations

Связи задач и меток.

```sql
CREATE TABLE task_tag_relations (
    task_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES task_tags(id) ON DELETE CASCADE
);
```

### custom_fields

Динамические поля на уровне пространства.

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

### task_custom_fields

Значения динамических полей для задач.

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

### project_field_sync

Управление синхронизацией полей проекта.

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

## Связи между таблицами

```
workspaces
  ├── boards (workspace_id)
  │   └── columns (board_id)
  │       └── tasks (column_id)
  │           ├── task_tag_relations (task_id)
  │           └── task_custom_fields (task_id)
  ├── projects (workspace_id)
  │   ├── tasks (project_id)
  │   └── project_field_sync (project_id)
  ├── task_tags (workspace_id)
  ├── custom_fields (workspace_id)
  └── personal_tasks (user_id через workspaces.user_id)
```

**Примечание:** Таблица `personal_tasks` связана с пользователями через `user_id`, который соответствует `user_id` в таблице `workspaces`.

## Типы данных

### Приоритеты задач
- `0` - Низкий (Low)
- `1` - Средний (Medium)
- `2` - Высокий (High)
- `3` - Критический (Critical)

### Типы полей
- `text` - Текст
- `url` - Ссылка
- `number` - Число
- `date` - Дата
- `select` - Выбор из списка

### Этапы дашборда проекта
- `preparation` - Подготовка
- `design` - Дизайн
- `development` - Разработка
- `testing` - Тестирование
- `submission` - На отправку
- `moderation` - Модерация
- `rejected` - Реджект
- `published` - Опубликовано

## Дополнительные ресурсы

- [Системная архитектура](system-overview.md) - общая архитектура системы
- [Руководство разработчика](../guides/developer-guide.md) - работа с БД
- [Миграции](../../task_tracker_bot/migrations/) - SQL миграции
- [Миграция Todo List](migrations/002_todo_list_migration.md) - миграция для Todo List функционала
- [Техническая спецификация Todo List](../specifications/todo-list-feature.md) - описание функционала


-- ============================================
-- Миграция БД для MVP 0.2
-- Версия: 0.2
-- Дата: 2025-01-28
-- ============================================

-- ============================================
-- 1. Таблица зависимостей досок
-- ============================================
CREATE TABLE IF NOT EXISTS board_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    source_board_id INTEGER NOT NULL,
    source_column_id INTEGER NOT NULL,
    trigger_type TEXT NOT NULL DEFAULT 'enter',
    target_board_id INTEGER NOT NULL,
    target_column_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    task_title_template TEXT,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (source_board_id) REFERENCES boards(id) ON DELETE CASCADE,
    FOREIGN KEY (source_column_id) REFERENCES columns(id) ON DELETE CASCADE,
    FOREIGN KEY (target_board_id) REFERENCES boards(id) ON DELETE CASCADE,
    FOREIGN KEY (target_column_id) REFERENCES columns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_board_dependencies_workspace 
ON board_dependencies(workspace_id);

CREATE INDEX IF NOT EXISTS idx_board_dependencies_source 
ON board_dependencies(source_board_id, source_column_id);

CREATE INDEX IF NOT EXISTS idx_board_dependencies_enabled 
ON board_dependencies(enabled);

-- ============================================
-- 2. Таблица действий зависимостей
-- ============================================
CREATE TABLE IF NOT EXISTS board_dependency_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dependency_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    action_data TEXT,
    FOREIGN KEY (dependency_id) REFERENCES board_dependencies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_board_dependency_actions_dependency 
ON board_dependency_actions(dependency_id);

-- ============================================
-- 3. Таблица назначений задач
-- ============================================
CREATE TABLE IF NOT EXISTS task_assignees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT DEFAULT 'assignee',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, user_id, role)
);

CREATE INDEX IF NOT EXISTS idx_task_assignees_task 
ON task_assignees(task_id);

CREATE INDEX IF NOT EXISTS idx_task_assignees_user 
ON task_assignees(user_id);

CREATE INDEX IF NOT EXISTS idx_task_assignees_role 
ON task_assignees(role);

-- ============================================
-- 4. Таблица участников проекта
-- ============================================
CREATE TABLE IF NOT EXISTS project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, user_id, role)
);

CREATE INDEX IF NOT EXISTS idx_project_members_project 
ON project_members(project_id);

CREATE INDEX IF NOT EXISTS idx_project_members_user 
ON project_members(user_id);

CREATE INDEX IF NOT EXISTS idx_project_members_role 
ON project_members(role);

-- ============================================
-- 5. Добавить новые колонки в таблицу tasks
-- ============================================

-- Примечание: Эти колонки будут добавлены через Python код с обработкой ошибок
-- SQLite не поддерживает IF NOT EXISTS для ALTER TABLE

-- Колонки для добавления:
-- assignee_id INTEGER - основной ответственный
-- started_at TIMESTAMP - дата начала работы
-- completed_at TIMESTAMP - дата завершения
-- deadline TIMESTAMP - дедлайн задачи

-- ============================================
-- 6. Создать индексы для новых колонок tasks
-- ============================================

-- Индексы будут созданы после добавления колонок через Python код

-- ============================================
-- Примеры данных для тестирования
-- ============================================

-- Пример зависимости: Подготовка Готово -> Дизайн Очередь
-- INSERT INTO board_dependencies (
--     workspace_id, name, source_board_id, source_column_id,
--     trigger_type, target_board_id, target_column_id, action_type,
--     task_title_template
-- ) VALUES (
--     1, 'Подготовка -> Дизайн', 1, 3,
--     'enter', 2, 1, 'create_task',
--     '{project_id} {project_name} Дизайн'
-- );

-- ============================================
-- Проверка миграции
-- ============================================

-- Проверить создание таблиц
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN (
--     'board_dependencies',
--     'board_dependency_actions',
--     'task_assignees',
--     'project_members'
-- );

-- Проверить индексы
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';

-- ============================================
-- Откат миграции (если нужно)
-- ============================================

-- DROP TABLE IF EXISTS board_dependency_actions;
-- DROP TABLE IF EXISTS board_dependencies;
-- DROP TABLE IF EXISTS task_assignees;
-- DROP TABLE IF EXISTS project_members;

-- ALTER TABLE tasks DROP COLUMN assignee_id;
-- ALTER TABLE tasks DROP COLUMN started_at;
-- ALTER TABLE tasks DROP COLUMN completed_at;
-- ALTER TABLE tasks DROP COLUMN deadline;


# Тест-план для Todo List Feature

> **Дата создания:** 2025-01-29  
> **Версия:** 1.0  
> **Статус:** 📝 Готово к тестированию

## 📋 Содержание

1. [Подготовка к тестированию](#подготовка-к-тестированию)
2. [Unit тесты](#unit-тесты)
3. [Интеграционные тесты](#интеграционные-тесты)
4. [E2E тесты](#e2e-тесты)
5. [Тесты миграции БД](#тесты-миграции-бд)
6. [Чеклист тестирования](#чеклист-тестирования)

---

## 🔧 Подготовка к тестированию

### Требования

- [ ] Бот запущен и работает
- [ ] Миграция БД выполнена (`migrate_todo_list.py`)
- [ ] Все зависимости установлены (`python-dateutil`)
- [ ] Тестовое пространство создано
- [ ] Тестовые проекты созданы (5001, 5010, 5007)

### Тестовые данные

#### Проекты
- Проект "5001" - Test Project 1
- Проект "5010" - Test Project 2
- Проект "5007" - Test Project 3

#### Доски
- Доска "Подготовка" с колонкой "Очередь"

---

## 🧪 Unit тесты

### Тесты для DateParser

**Файл:** `task_tracker_bot/tests/test_date_parser.py`

#### Тест 1: Парсинг относительных дат

```python
def test_parse_today():
    """Тест парсинга 'сегодня'"""
    parser = DateParser()
    today = datetime.now().date()
    result = parser.parse_date("сегодня")
    assert result == today

def test_parse_tomorrow():
    """Тест парсинга 'завтра'"""
    parser = DateParser()
    tomorrow = datetime.now().date() + timedelta(days=1)
    result = parser.parse_date("завтра")
    assert result == tomorrow

def test_parse_yesterday():
    """Тест парсинга 'вчера'"""
    parser = DateParser()
    yesterday = datetime.now().date() - timedelta(days=1)
    result = parser.parse_date("вчера")
    assert result == yesterday
```

#### Тест 2: Парсинг абсолютных дат

```python
def test_parse_date_dd_mm():
    """Тест парсинга формата DD.MM"""
    parser = DateParser()
    current_year = datetime.now().year
    result = parser.parse_date("03.12")
    assert result == date(current_year, 12, 3)

def test_parse_date_dd_mm_yyyy():
    """Тест парсинга формата DD.MM.YYYY"""
    parser = DateParser()
    result = parser.parse_date("03.12.2025")
    assert result == date(2025, 12, 3)
```

#### Тест 3: Парсинг времени

```python
def test_parse_time():
    """Тест парсинга времени HH:MM"""
    parser = DateParser()
    result = parser.parse_time("10:00")
    assert result == time(10, 0)

def test_parse_time_range():
    """Тест парсинга диапазона времени"""
    parser = DateParser()
    result = parser.parse_time_range("11:10 - 12:00")
    assert result == (time(11, 10), time(12, 0))
```

#### Тест 4: Извлечение из текста задачи

```python
def test_parse_datetime_from_task():
    """Тест извлечения даты и времени из текста задачи"""
    parser = DateParser()
    result = parser.parse_datetime_from_task(
        "Выгул Феры в 10:00",
        default_date=date(2025, 11, 30)
    )
    assert result["date"] == date(2025, 11, 30)
    assert result["time"] == time(10, 0)
    assert result["remaining_text"] == "Выгул Феры в"

def test_parse_datetime_from_task_with_date():
    """Тест извлечения даты из текста задачи"""
    parser = DateParser()
    result = parser.parse_datetime_from_task(
        "5007 - Промониторить трафик 03.12"
    )
    assert result["date"] == date(2025, 12, 3)
    assert "03.12" not in result["remaining_text"]
```

### Тесты для TaskClassifier

**Файл:** `task_tracker_bot/tests/test_task_classifier.py`

#### Тест 1: Определение личных задач

```python
def test_classify_personal_task():
    """Тест классификации личной задачи"""
    classifier = TaskClassifier(project_repo)
    result = classifier.classify_task("Выгул Феры", workspace_id=1)
    assert result["type"] == "personal"
    assert result["project_id"] is None
    assert result["title"] == "Выгул Феры"
```

#### Тест 2: Определение рабочих задач

```python
def test_classify_work_task_with_dash():
    """Тест классификации рабочей задачи с дефисом"""
    classifier = TaskClassifier(project_repo)
    result = classifier.classify_task("5001 - Протестировать", workspace_id=1)
    assert result["type"] == "work"
    assert result["project_id"] == "5001"
    assert result["title"] == "Протестировать"

def test_classify_work_task_without_dash():
    """Тест классификации рабочей задачи без дефиса"""
    classifier = TaskClassifier(project_repo)
    result = classifier.classify_task("5010 Протестировать", workspace_id=1)
    assert result["type"] == "work"
    assert result["project_id"] == "5010"
    assert result["title"] == "Протестировать"
```

#### Тест 3: Несуществующий проект

```python
def test_classify_task_nonexistent_project():
    """Тест классификации задачи с несуществующим проектом"""
    classifier = TaskClassifier(project_repo)
    result = classifier.classify_task("9999 - Задача", workspace_id=1)
    # Может быть personal если проект не найден
    # Или work если проект создается автоматически
    assert result["type"] in ["personal", "work"]
```

### Тесты для TodoService

**Файл:** `task_tracker_bot/tests/test_todo_service.py`

#### Тест 1: Создание пакета задач

```python
def test_create_todo_batch():
    """Тест создания пакета задач"""
    service = TodoService(...)
    tasks_text = """
    1. Выгул Феры в 10:00
    2. 5001 - Протестировать приложение
    """
    result = service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=1,
        user_id=123456,
        default_date=date(2025, 11, 30)
    )
    assert result["status"] == "success"
    assert len(result["personal_tasks_created"]) == 1
    assert len(result["work_tasks_created"]) == 1
```

#### Тест 2: Множественное время

```python
def test_create_todo_batch_multiple_times():
    """Тест создания задач с множественным временем"""
    service = TodoService(...)
    tasks_text = "1. Выгул Феры в 10:00 и 19:00"
    result = service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=1,
        user_id=123456,
        default_date=date(2025, 11, 30)
    )
    assert len(result["personal_tasks_created"]) == 2
    assert result["personal_tasks_created"][0]["time"] == time(10, 0)
    assert result["personal_tasks_created"][1]["time"] == time(19, 0)
```

#### Тест 3: Получение туду-листа

```python
def test_get_todo_list():
    """Тест получения туду-листа на дату"""
    service = TodoService(...)
    # Создать тестовые задачи
    # ...
    
    result = service.get_todo_list(
        user_id=123456,
        date=date(2025, 11, 30),
        include_work_tasks=True
    )
    assert "personal_tasks" in result
    assert "work_tasks" in result
    assert "grouped_by_time" in result
```

---

## 🔗 Интеграционные тесты

### Тест 1: Пакетное создание через AI агентов

**Файл:** `task_tracker_bot/tests/test_todo_integration.py`

```python
def test_ai_create_todo_batch():
    """Тест пакетного создания через AI агентов"""
    coordinator = AgentCoordinator(db=db)
    
    user_message = """
    Добавь на завтра задачи
    
    1. Выгул Феры в 10:00 и 19:00
    2. Записаться к барберу 11:00
    3. 5001 - Протестировать приложение
    """
    
    result = coordinator.process_user_message(
        user_message=user_message,
        workspace_id=1,
        user_id=123456
    )
    
    assert result["status"] == "success"
    # Проверить созданные задачи в БД
    personal_tasks = personal_task_repo.get_by_date(123456, tomorrow)
    assert len(personal_tasks) == 3  # 2 задачи на 10:00 и 19:00, 1 на 11:00
    
    work_tasks = task_repo.get_all_by_project("5001")
    assert len(work_tasks) > 0
```

### Тест 2: Определение типа задач

```python
def test_task_classification_integration():
    """Тест определения типа задач в реальном сценарии"""
    coordinator = AgentCoordinator(db=db)
    
    user_message = """
    Добавь задачи:
    1. Личная задача без проекта
    2. 5001 - Рабочая задача с проектом
    3. 9999 - Задача с несуществующим проектом
    """
    
    result = coordinator.process_user_message(
        user_message=user_message,
        workspace_id=1,
        user_id=123456
    )
    
    # Проверить, что задачи созданы правильно
    # ...
```

---

## 🎭 E2E тесты

### Тест 1: Полный сценарий добавления и просмотра

**Файл:** `task_tracker_bot/tests/test_todo_e2e.py`

```python
async def test_full_todo_workflow():
    """Полный E2E тест туду-листа"""
    # 1. Добавить задачи через AI
    await send_message("""
    Добавь на завтра задачи
    
    1. Выгул Феры в 10:00 и 19:00
    2. Записаться к барберу 11:00
    3. 5001 - Протестировать приложение
    """)
    
    # 2. Проверить ответ бота
    response = await get_last_message()
    assert "создано" in response.lower()
    
    # 3. Просмотреть туду-лист
    await send_message("/todo завтра")
    
    # 4. Проверить отображение
    response = await get_last_message()
    assert "10:00" in response
    assert "19:00" in response
    assert "11:00" in response
    assert "5001" in response
```

### Тест 2: Навигация по датам

```python
async def test_todo_navigation():
    """Тест навигации по датам в туду-листе"""
    # Создать задачи на разные даты
    # ...
    
    # Переключиться на завтра
    await click_button("Завтра ▶️")
    
    # Проверить отображение задач на завтра
    response = await get_last_message()
    assert "завтра" in response.lower()
```

---

## 🗄️ Тесты миграции БД

**Файл:** `task_tracker_bot/tests/test_todo_migration.py`

### Тест 1: Проверка создания таблицы

```python
def test_personal_tasks_table_exists():
    """Тест существования таблицы personal_tasks"""
    db = Database()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='personal_tasks'
        """)
        assert cursor.fetchone() is not None
```

### Тест 2: Проверка колонок в tasks

```python
def test_tasks_scheduled_columns_exist():
    """Тест существования колонок scheduled_* в tasks"""
    db = Database()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert "scheduled_date" in columns
        assert "scheduled_time" in columns
        assert "scheduled_time_end" in columns
```

### Тест 3: Проверка индексов

```python
def test_todo_indexes_exist():
    """Тест существования индексов"""
    db = Database()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%scheduled%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert len(indexes) > 0
        assert "idx_tasks_scheduled_date" in indexes
        assert "idx_personal_tasks_user_date" in indexes
```

### Тест 4: Откат миграции

```python
def test_migration_rollback():
    """Тест отката миграции"""
    # Выполнить миграцию
    migrate()
    
    # Проверить создание таблицы
    assert personal_tasks_table_exists()
    
    # Откатить миграцию
    rollback()
    
    # Проверить удаление таблицы
    assert not personal_tasks_table_exists()
```

---

## ✅ Чеклист тестирования

### Unit тесты

- [ ] DateParser.parse_date - относительные даты
- [ ] DateParser.parse_date - абсолютные даты
- [ ] DateParser.parse_time - одно время
- [ ] DateParser.parse_time_range - диапазон времени
- [ ] DateParser.parse_datetime_from_task - извлечение из текста
- [ ] TaskClassifier.classify_task - личные задачи
- [ ] TaskClassifier.classify_task - рабочие задачи
- [ ] TaskClassifier.classify_task - несуществующий проект
- [ ] TodoService.create_todo_batch - базовое создание
- [ ] TodoService.create_todo_batch - множественное время
- [ ] TodoService.get_todo_list - получение списка
- [ ] TodoService.mark_personal_task_completed - отметка выполненной

### Интеграционные тесты

- [ ] Пакетное создание через AI агентов
- [ ] Определение типа задач в реальном сценарии
- [ ] Создание задач с датами в будущем
- [ ] Обработка ошибок при создании

### E2E тесты

- [ ] Полный сценарий добавления и просмотра
- [ ] Навигация по датам
- [ ] Отметка задач как выполненных
- [ ] Отображение задач с разными временами
- [ ] Группировка задач по времени

### Тесты миграции

- [ ] Создание таблицы personal_tasks
- [ ] Добавление колонок в tasks
- [ ] Создание индексов
- [ ] Откат миграции
- [ ] Проверка целостности данных

### Тесты производительности

- [ ] Парсинг большого количества задач (100+)
- [ ] Получение туду-листа с множеством задач
- [ ] Поиск задач по дате (индексы)

### Тесты граничных случаев

- [ ] Пустой список задач
- [ ] Некорректный формат даты
- [ ] Некорректный формат времени
- [ ] Задача без даты
- [ ] Задача без времени
- [ ] Задача с несуществующим проектом
- [ ] Задача с некорректным project_id

---

## 📊 Примеры тест-кейсов

### Тест-кейс 1: Парсинг "завтра"

**Вход:** "завтра"  
**Ожидаемый результат:** `date(2025, 11, 30)` (если сегодня 29.11.2025)  
**Статус:** ✅ PASS / ❌ FAIL

### Тест-кейс 2: Парсинг "03.12"

**Вход:** "03.12"  
**Ожидаемый результат:** `date(2025, 12, 3)`  
**Статус:** ✅ PASS / ❌ FAIL

### Тест-кейс 3: Классификация личной задачи

**Вход:** "Выгул Феры"  
**Ожидаемый результат:** `{"type": "personal", "project_id": None}`  
**Статус:** ✅ PASS / ❌ FAIL

### Тест-кейс 4: Классификация рабочей задачи

**Вход:** "5001 - Протестировать"  
**Ожидаемый результат:** `{"type": "work", "project_id": "5001"}`  
**Статус:** ✅ PASS / ❌ FAIL

### Тест-кейс 5: Множественное время

**Вход:** "Выгул Феры в 10:00 и 19:00"  
**Ожидаемый результат:** 2 задачи с временами 10:00 и 19:00  
**Статус:** ✅ PASS / ❌ FAIL

---

## 🔗 Связанные документы

- [Техническая спецификация](../specifications/todo-list-feature.md)
- [Руководство по парсингу дат](../development/date-parsing-guide.md)
- [Инструкции для агентов](../development/agent-instructions-todo.md)
- [План миграции БД](../architecture/migrations/002_todo_list_migration.md)

---

**Дата последнего обновления:** 2025-01-29


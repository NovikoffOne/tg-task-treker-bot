# Руководство по MVP 0.2

> **Дата создания:** 2025-01-28  
> **Обновлено:** 2025-01-28  
> **Статус:** Актуально

Этот документ содержит инструкции для реализации и использования MVP 0.2.

## Для агентов Cursor AI

### Что нужно сделать

Реализовать все функции MVP 0.2 согласно спецификации [mvp-0.2.md](../specifications/mvp-0.2.md).

### Порядок работы

#### Шаг 1: Изучить документацию

1. Прочитать `docs/specifications/mvp-0.2.md` - полная спецификация
2. Прочитать `task_tracker_bot/migrations/001_mvp_0_2_migration.sql` - SQL миграции
3. Прочитать `docs/testing/test-plans/mvp-0.2-plan.md` - план тестирования

#### Шаг 2: Выполнить миграцию БД

1. Запустить миграцию: `python task_tracker_bot/migrations/migrate_0_2.py`
2. Проверить создание всех таблиц и колонок
3. Убедиться, что миграция прошла успешно

#### Шаг 3: Создать модели данных

Создать файлы:
- `task_tracker_bot/models/board_dependency.py`
- `task_tracker_bot/models/task_assignee.py`
- `task_tracker_bot/models/project_member.py`

Обновить:
- `task_tracker_bot/models/task.py` - добавить новые поля

#### Шаг 4: Создать репозитории

Создать файлы:
- `task_tracker_bot/repositories/board_dependency_repository.py`
- `task_tracker_bot/repositories/task_assignee_repository.py`
- `task_tracker_bot/repositories/project_member_repository.py`

Обновить:
- `task_tracker_bot/repositories/task_repository.py` - добавить методы для новых полей

#### Шаг 5: Создать сервисы

Создать файлы:
- `task_tracker_bot/services/dependency_service.py`
- `task_tracker_bot/services/assignment_service.py`

Обновить:
- `task_tracker_bot/services/task_service.py` - интегрировать новые сервисы
- `task_tracker_bot/utils/board_visualizer.py` - добавить метод списка

#### Шаг 6: Создать handlers

Создать файлы:
- `task_tracker_bot/handlers/dependency.py`

Обновить:
- `task_tracker_bot/handlers/task.py` - добавить новые команды
- `task_tracker_bot/handlers/board.py` - добавить команду списка

#### Шаг 7: Обновить UI

Обновить:
- `task_tracker_bot/utils/formatters.py` - обновить форматирование задач
- `task_tracker_bot/utils/keyboards.py` - обновить клавиатуры

#### Шаг 8: Интегрировать в bot.py

Обновить:
- `task_tracker_bot/bot.py` - зарегистрировать новые команды и handlers

#### Шаг 9: Создать тесты

Создать файлы:
- `task_tracker_bot/tests/test_dependency_service.py`
- `task_tracker_bot/tests/test_assignment_service.py`
- `task_tracker_bot/tests/test_mvp_0_2_integration.py`

#### Шаг 10: Запустить тесты

```bash
pytest task_tracker_bot/tests/ -v
```

#### Шаг 11: Протестировать через Telegram MCP

Следовать плану из `docs/testing/test-plans/mvp-0.2-plan.md`

#### Шаг 12: Запустить бота и отправить уведомление

1. Запустить бота: `python task_tracker_bot/bot.py`
2. Отправить уведомление в Telegram через MCP о готовности бота

### Критерии завершения

Работа считается завершенной, когда:

1. ✅ Все файлы созданы и обновлены
2. ✅ Все тесты проходят успешно
3. ✅ Бот запускается без ошибок
4. ✅ Все функции MVP 0.2 работают
5. ✅ Отправлено уведомление в Telegram о готовности

### Важные замечания

- Все изменения должны быть обратно совместимы с MVP 0.1
- Используйте существующие паттерны кода из проекта
- Следуйте правилам из `docs/development/rules.md`
- Пишите тесты для всех новых функций
- Логируйте все автоматические действия

## Для пользователя (разработчика)

### Что уже готово

✅ Созданы все необходимые файлы документации:
- `docs/specifications/mvp-0.2.md` - полная спецификация с планом реализации
- `task_tracker_bot/migrations/001_mvp_0_2_migration.sql` - SQL скрипты миграции
- `task_tracker_bot/migrations/migrate_0_2.py` - Python скрипт миграции
- `docs/testing/test-plans/mvp-0.2-plan.md` - детальный план тестирования через Telegram MCP

### Как передать к реализации

#### Вариант 1: Использовать режим Plan в Cursor

1. Откройте файл `docs/getting-started/mvp-0-2-guide.md`
2. В Cursor AI выберите режим **Plan**
3. Отправьте следующую команду:

```
Реализуй MVP 0.2 согласно спецификации в файле docs/getting-started/mvp-0-2-guide.md. 
Следуй плану из docs/specifications/mvp-0.2.md. 
После завершения запусти бота и отправь уведомление в Telegram через MCP о готовности.
```

#### Вариант 2: Использовать режим Agent в Cursor

1. Откройте файл `docs/getting-started/mvp-0-2-guide.md`
2. В Cursor AI выберите режим **Agent**
3. Отправьте следующую команду:

```
Начни реализацию MVP 0.2. Следуй инструкциям из docs/getting-started/mvp-0-2-guide.md. 
Реализуй все функции по порядку согласно docs/specifications/mvp-0.2.md. 
После завершения всех этапов запусти бота и отправь уведомление в Telegram через MCP.
```

#### Вариант 3: Пошаговая реализация

Если хотите контролировать процесс пошагово:

1. **Шаг 1:** Попросите агента выполнить миграцию БД
   ```
   Выполни миграцию БД для MVP 0.2: запусти migrate_0_2.py и проверь результат
   ```

2. **Шаг 2:** Попросите создать модели данных
   ```
   Создай модели данных для MVP 0.2 согласно docs/specifications/mvp-0.2.md
   ```

3. И так далее по каждому этапу из этого документа

### Что будет сделано

Агенты реализуют:

1. ✅ Миграцию БД (новые таблицы и колонки)
2. ✅ Новые модели данных (BoardDependency, TaskAssignee, ProjectMember)
3. ✅ Новые репозитории для работы с данными
4. ✅ Новые сервисы (DependencyService, AssignmentService)
5. ✅ Обновление существующих сервисов
6. ✅ Новые handlers для команд
7. ✅ Обновление UI (форматтеры, клавиатуры)
8. ✅ Интеграцию в bot.py
9. ✅ Тесты для всех функций
10. ✅ Тестирование через Telegram MCP
11. ✅ Запуск бота и отправку уведомления

### Проверка готовности

После завершения работы агентов проверьте:

1. Все ли файлы созданы согласно спецификации
2. Запускаются ли тесты: `pytest task_tracker_bot/tests/ -v`
3. Запускается ли бот: `python task_tracker_bot/bot.py`
4. Работают ли новые команды:
   - `/mytasks`
   - `/today`
   - `/deadline <id> <дата>`
   - `/boardlist <название>`
   - `/dependencies`

### Если что-то пошло не так

1. Проверьте логи бота
2. Проверьте, что миграция БД выполнена успешно
3. Проверьте, что все зависимости установлены: `pip install -r task_tracker_bot/requirements.txt`
4. Проверьте конфигурацию в `.env` файле
5. Запустите тесты и посмотрите на ошибки

## Дополнительные ресурсы

- [mvp-0.2.md](../specifications/mvp-0.2.md) - полная спецификация
- [mvp-0.2-plan.md](../testing/test-plans/mvp-0.2-plan.md) - план тестирования
- [test-base-case.md](../testing/test-base-case.md) - базовый сценарий тестирования


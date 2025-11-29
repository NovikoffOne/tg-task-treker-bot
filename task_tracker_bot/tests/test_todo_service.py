"""
Unit тесты для TodoService
"""
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, MagicMock
from services.todo_service import TodoService
from repositories.personal_task_repository import PersonalTaskRepository
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.column_repository import ColumnRepository
from repositories.board_repository import BoardRepository
from utils.date_parser import DateParser
from utils.task_classifier import TaskClassifier

@pytest.fixture
def mock_repos():
    """Моки репозиториев"""
    return {
        'personal_task': Mock(spec=PersonalTaskRepository),
        'task': Mock(spec=TaskRepository),
        'project': Mock(spec=ProjectRepository),
        'column': Mock(spec=ColumnRepository),
        'board': Mock(spec=BoardRepository)
    }

@pytest.fixture
def mock_utils():
    """Моки утилит"""
    date_parser = Mock(spec=DateParser)
    task_classifier = Mock(spec=TaskClassifier)
    return {
        'date_parser': date_parser,
        'task_classifier': task_classifier
    }

@pytest.fixture
def todo_service(mock_repos, mock_utils):
    """Создание TodoService с моками"""
    return TodoService(
        personal_task_repo=mock_repos['personal_task'],
        task_repo=mock_repos['task'],
        project_repo=mock_repos['project'],
        column_repo=mock_repos['column'],
        board_repo=mock_repos['board'],
        date_parser=mock_utils['date_parser'],
        task_classifier=mock_utils['task_classifier']
    )

def test_create_todo_batch_personal_task(todo_service, mock_repos, mock_utils):
    """Тест создания личной задачи"""
    tasks_text = "1. Выгул Феры в 10:00"
    workspace_id = 1
    user_id = 123
    default_date = date(2025, 11, 30)
    
    # Настройка моков
    mock_utils['date_parser'].parse_datetime_from_task.return_value = {
        "date": default_date,
        "time": time(10, 0),
        "time_end": None,
        "remaining_text": "Выгул Феры"
    }
    mock_utils['task_classifier'].classify_task.return_value = {
        "type": "personal",
        "project_id": None,
        "title": "Выгул Феры"
    }
    mock_repos['personal_task'].create.return_value = 1
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=default_date
    )
    
    assert result["status"] == "success"
    assert len(result["personal_tasks_created"]) == 1
    assert len(result["work_tasks_created"]) == 0
    mock_repos['personal_task'].create.assert_called_once()

def test_create_todo_batch_work_task(todo_service, mock_repos, mock_utils):
    """Тест создания рабочей задачи"""
    tasks_text = "1. 5001 - Протестировать приложение"
    workspace_id = 1
    user_id = 123
    default_date = date(2025, 11, 30)
    
    # Настройка моков
    from models.project import Project
    mock_project = Mock(spec=Project)
    mock_project.id = "5001"
    mock_project.workspace_id = workspace_id
    
    from models.board import Board
    mock_board = Mock(spec=Board)
    mock_board.id = 1
    
    from models.column import Column
    mock_column = Mock(spec=Column)
    mock_column.id = 1
    
    mock_utils['date_parser'].parse_datetime_from_task.return_value = {
        "date": default_date,
        "time": None,
        "time_end": None,
        "remaining_text": "5001 - Протестировать приложение"
    }
    mock_utils['task_classifier'].classify_task.return_value = {
        "type": "work",
        "project_id": "5001",
        "title": "Протестировать приложение"
    }
    mock_repos['project'].get_by_id.return_value = mock_project
    mock_repos['board'].get_by_name.return_value = mock_board
    mock_repos['board'].get_all_by_workspace.return_value = [mock_board]
    mock_repos['column'].get_all_by_board.return_value = [mock_column]
    mock_repos['column'].get_first_by_board.return_value = mock_column
    mock_repos['task'].create.return_value = 100
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=default_date
    )
    
    assert result["status"] == "success"
    assert len(result["personal_tasks_created"]) == 0
    assert len(result["work_tasks_created"]) == 1
    mock_repos['task'].create.assert_called_once()

def test_get_todo_list(todo_service, mock_repos):
    """Тест получения туду-листа"""
    user_id = 123
    target_date = date(2025, 11, 30)
    
    # Настройка моков
    from models.personal_task import PersonalTask
    mock_personal_task = Mock(spec=PersonalTask)
    mock_personal_task.id = 1
    mock_personal_task.title = "Выгул Феры"
    mock_personal_task.scheduled_time = time(10, 0)
    mock_personal_task.scheduled_time_end = None
    mock_personal_task.completed = False
    mock_personal_task.time_display = "10:00"
    
    mock_repos['personal_task'].get_by_date.return_value = [mock_personal_task]
    mock_repos['task'].get_by_scheduled_date.return_value = []
    
    result = todo_service.get_todo_list(
        user_id=user_id,
        target_date=target_date,
        include_work_tasks=True
    )
    
    assert result["date"] == "30.11.2025"
    assert len(result["personal_tasks"]) == 1
    assert "grouped_by_time" in result

def test_mark_personal_task_completed(todo_service, mock_repos):
    """Тест отметки личной задачи как выполненной"""
    task_id = 1
    user_id = 123
    
    mock_repos['personal_task'].mark_completed.return_value = True
    
    success, error = todo_service.mark_personal_task_completed(task_id, user_id)
    
    assert success is True
    assert error is None
    mock_repos['personal_task'].mark_completed.assert_called_once_with(task_id, user_id)

def test_create_todo_batch_with_tomorrow_date(todo_service, mock_repos, mock_utils):
    """Тест создания задач на завтра"""
    tasks_text = "1. Купить молоко\n2. Позвонить маме"
    workspace_id = 1
    user_id = 123
    tomorrow = datetime.now().date() + timedelta(days=1)
    
    # Настройка моков
    mock_utils['date_parser'].parse_datetime_from_task.side_effect = [
        {
            "date": tomorrow,
            "time": None,
            "time_end": None,
            "remaining_text": "Купить молоко"
        },
        {
            "date": tomorrow,
            "time": None,
            "time_end": None,
            "remaining_text": "Позвонить маме"
        }
    ]
    mock_utils['task_classifier'].classify_task.side_effect = [
        {"type": "personal", "title": "Купить молоко"},
        {"type": "personal", "title": "Позвонить маме"}
    ]
    mock_repos['personal_task'].create.side_effect = [1, 2]
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=tomorrow
    )
    
    assert result["status"] == "success"
    assert len(result["personal_tasks_created"]) == 2
    assert all(task["date"] == tomorrow.isoformat() for task in result["personal_tasks_created"])

def test_create_todo_batch_with_absolute_date(todo_service, mock_repos, mock_utils):
    """Тест создания задач с абсолютной датой"""
    tasks_text = "1. Встреча с клиентом"
    workspace_id = 1
    user_id = 123
    target_date = date(2025, 12, 15)
    
    mock_utils['date_parser'].parse_datetime_from_task.return_value = {
        "date": target_date,
        "time": time(14, 0),
        "time_end": None,
        "remaining_text": "Встреча с клиентом"
    }
    mock_utils['task_classifier'].classify_task.return_value = {
        "type": "personal",
        "title": "Встреча с клиентом"
    }
    mock_repos['personal_task'].create.return_value = 1
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=target_date
    )
    
    assert result["status"] == "success"
    assert result["personal_tasks_created"][0]["date"] == target_date.isoformat()
    assert result["personal_tasks_created"][0]["time"] == time(14, 0).isoformat()

def test_create_todo_batch_parse_task_list(todo_service, mock_repos, mock_utils):
    """Тест парсинга списка задач из текста"""
    tasks_text = """1. Купить молоко
2. Позвонить маме
3. Встреча в 15:00"""
    
    workspace_id = 1
    user_id = 123
    default_date = date(2025, 11, 30)
    
    # Настройка моков для трех задач
    mock_utils['date_parser'].parse_datetime_from_task.side_effect = [
        {"date": default_date, "time": None, "time_end": None, "remaining_text": "Купить молоко"},
        {"date": default_date, "time": None, "time_end": None, "remaining_text": "Позвонить маме"},
        {"date": default_date, "time": time(15, 0), "time_end": None, "remaining_text": "Встреча"}
    ]
    mock_utils['task_classifier'].classify_task.side_effect = [
        {"type": "personal", "title": "Купить молоко"},
        {"type": "personal", "title": "Позвонить маме"},
        {"type": "personal", "title": "Встреча"}
    ]
    mock_repos['personal_task'].create.side_effect = [1, 2, 3]
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=default_date
    )
    
    assert result["status"] == "success"
    assert len(result["personal_tasks_created"]) == 3
    # Проверяем, что parse_datetime_from_task был вызван 3 раза
    assert mock_utils['date_parser'].parse_datetime_from_task.call_count == 3

def test_create_todo_batch_extract_date_from_task_text(todo_service, mock_repos, mock_utils):
    """Тест извлечения даты из текста задачи"""
    tasks_text = "1. Купить молоко завтра в 10:00"
    workspace_id = 1
    user_id = 123
    
    tomorrow = datetime.now().date() + timedelta(days=1)
    
    mock_utils['date_parser'].parse_datetime_from_task.return_value = {
        "date": tomorrow,
        "time": time(10, 0),
        "time_end": None,
        "remaining_text": "Купить молоко"
    }
    mock_utils['task_classifier'].classify_task.return_value = {
        "type": "personal",
        "title": "Купить молоко"
    }
    mock_repos['personal_task'].create.return_value = 1
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=None
    )
    
    assert result["status"] == "success"
    assert result["personal_tasks_created"][0]["date"] == tomorrow.isoformat()
    assert result["personal_tasks_created"][0]["time"] == time(10, 0).isoformat()

def test_create_todo_batch_with_time_range(todo_service, mock_repos, mock_utils):
    """Тест создания задачи с диапазоном времени"""
    tasks_text = "1. Встреча 11:10 - 12:00"
    workspace_id = 1
    user_id = 123
    default_date = date(2025, 11, 30)
    
    mock_utils['date_parser'].parse_datetime_from_task.return_value = {
        "date": default_date,
        "time": time(11, 10),
        "time_end": time(12, 0),
        "remaining_text": "Встреча"
    }
    mock_utils['task_classifier'].classify_task.return_value = {
        "type": "personal",
        "title": "Встреча"
    }
    mock_repos['personal_task'].create.return_value = 1
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=default_date
    )
    
    assert result["status"] == "success"
    task = result["personal_tasks_created"][0]
    assert task["time"] == time(11, 10).isoformat()
    assert task["time_end"] == time(12, 0).isoformat()

def test_create_todo_batch_mixed_personal_and_work(todo_service, mock_repos, mock_utils):
    """Тест создания смешанных задач (личные + рабочие)"""
    tasks_text = "1. Купить молоко\n2. 5001 - Протестировать приложение"
    workspace_id = 1
    user_id = 123
    default_date = date(2025, 11, 30)
    
    from models.project import Project
    from models.board import Board
    from models.column import Column
    
    mock_project = Mock(spec=Project)
    mock_project.id = "5001"
    mock_board = Mock(spec=Board)
    mock_board.id = 1
    mock_column = Mock(spec=Column)
    mock_column.id = 1
    
    mock_utils['date_parser'].parse_datetime_from_task.side_effect = [
        {"date": default_date, "time": None, "time_end": None, "remaining_text": "Купить молоко"},
        {"date": default_date, "time": None, "time_end": None, "remaining_text": "5001 - Протестировать приложение"}
    ]
    mock_utils['task_classifier'].classify_task.side_effect = [
        {"type": "personal", "title": "Купить молоко"},
        {"type": "work", "project_id": "5001", "title": "Протестировать приложение"}
    ]
    mock_repos['personal_task'].create.return_value = 1
    mock_repos['project'].get_by_id.return_value = mock_project
    mock_repos['board'].get_by_name.return_value = mock_board
    mock_repos['column'].get_first_by_board.return_value = mock_column
    mock_repos['task'].create.return_value = 100
    
    result = todo_service.create_todo_batch(
        tasks_text=tasks_text,
        workspace_id=workspace_id,
        user_id=user_id,
        default_date=default_date
    )
    
    assert result["status"] == "success"
    assert len(result["personal_tasks_created"]) == 1
    assert len(result["work_tasks_created"]) == 1


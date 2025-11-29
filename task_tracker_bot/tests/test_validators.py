"""
Тесты для валидаторов
"""
import pytest
from utils.validators import (
    validate_title, validate_description, validate_name,
    validate_url, validate_task_id, validate_priority
)

def test_validate_title():
    """Тест валидации названия задачи"""
    # Валидное название
    is_valid, error = validate_title("Тестовая задача")
    assert is_valid is True
    assert error is None
    
    # Слишком короткое
    is_valid, error = validate_title("A")
    assert is_valid is False
    assert error is not None
    
    # Слишком длинное
    is_valid, error = validate_title("A" * 501)
    assert is_valid is False
    assert error is not None

def test_validate_description():
    """Тест валидации описания"""
    # Валидное описание
    is_valid, error = validate_description("Описание задачи")
    assert is_valid is True
    assert error is None
    
    # Слишком длинное
    is_valid, error = validate_description("A" * 2001)
    assert is_valid is False
    assert error is not None

def test_validate_name():
    """Тест валидации названия"""
    # Валидное название
    is_valid, error = validate_name("Тестовое пространство")
    assert is_valid is True
    assert error is None
    
    # Слишком короткое
    is_valid, error = validate_name("A")
    assert is_valid is False

def test_validate_url():
    """Тест валидации URL"""
    # Валидный URL
    is_valid, error = validate_url("https://figma.com/file/test")
    assert is_valid is True
    assert error is None
    
    # Невалидный URL
    is_valid, error = validate_url("not-a-url")
    assert is_valid is False
    assert error is not None

def test_validate_task_id():
    """Тест валидации ID задачи"""
    # Валидный ID
    is_valid, task_id, error = validate_task_id("123")
    assert is_valid is True
    assert task_id == 123
    assert error is None
    
    # Невалидный ID
    is_valid, task_id, error = validate_task_id("abc")
    assert is_valid is False
    assert task_id is None
    assert error is not None
    
    # Отрицательный ID
    is_valid, task_id, error = validate_task_id("-1")
    assert is_valid is False

def test_validate_priority():
    """Тест валидации приоритета"""
    # Валидные приоритеты
    for priority in [0, 1, 2, 3]:
        is_valid, error = validate_priority(priority)
        assert is_valid is True
        assert error is None
    
    # Невалидные приоритеты
    is_valid, error = validate_priority(-1)
    assert is_valid is False
    
    is_valid, error = validate_priority(4)
    assert is_valid is False


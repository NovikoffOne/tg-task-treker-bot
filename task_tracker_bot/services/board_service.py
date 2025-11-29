"""
Сервис для работы с Board и Column
"""
from typing import List, Optional, Tuple
from repositories.board_repository import BoardRepository
from repositories.column_repository import ColumnRepository
from models.board import Board
from models.column import Column

class BoardService:
    def __init__(self, board_repo: BoardRepository, column_repo: ColumnRepository):
        self.board_repo = board_repo
        self.column_repo = column_repo
    
    def create_board(self, workspace_id: int, name: str) -> tuple[bool, Optional[int], Optional[str]]:
        """Создать доску"""
        # Валидация
        name = name.strip()
        if len(name) < 2:
            return False, None, "Название доски должно быть минимум 2 символа"
        if len(name) > 100:
            return False, None, "Название доски слишком длинное (максимум 100 символов)"
        
        # Проверка уникальности
        existing = self.board_repo.get_by_name(workspace_id, name)
        if existing:
            return False, None, "Доска с таким названием уже существует"
        
        try:
            # Получить максимальную позицию
            boards = self.board_repo.get_all_by_workspace(workspace_id)
            max_position = max([b.position for b in boards], default=-1) + 1
            
            board_id = self.board_repo.create(workspace_id, name, max_position)
            
            # Создать дефолтные колонки
            self._create_default_columns(board_id)
            
            return True, board_id, None
        except Exception as e:
            return False, None, f"Ошибка при создании доски: {str(e)}"
    
    def _create_default_columns(self, board_id: int):
        """Создать дефолтные колонки для доски"""
        default_columns = ["Очередь", "В работе", "Готово"]
        for i, col_name in enumerate(default_columns):
            self.column_repo.create(board_id, col_name, i)
    
    def get_board(self, board_id: int) -> Optional[Board]:
        """Получить доску"""
        return self.board_repo.get_by_id(board_id)
    
    def get_board_by_name(self, workspace_id: int, name: str) -> Optional[Board]:
        """Получить доску по имени"""
        return self.board_repo.get_by_name(workspace_id, name)
    
    def list_boards(self, workspace_id: int) -> List[Board]:
        """Получить все доски пространства"""
        return self.board_repo.get_all_by_workspace(workspace_id)
    
    def rename_board(self, board_id: int, new_name: str) -> tuple[bool, Optional[str]]:
        """Переименовать доску"""
        # Валидация
        new_name = new_name.strip()
        if len(new_name) < 2:
            return False, "Название доски должно быть минимум 2 символа"
        if len(new_name) > 100:
            return False, "Название доски слишком длинное (максимум 100 символов)"
        
        # Проверка существования
        board = self.board_repo.get_by_id(board_id)
        if not board:
            return False, "Доска не найдена"
        
        # Проверка уникальности
        existing = self.board_repo.get_by_name(board.workspace_id, new_name)
        if existing and existing.id != board_id:
            return False, "Доска с таким названием уже существует"
        
        try:
            success = self.board_repo.update(board_id, name=new_name)
            if success:
                return True, None
            return False, "Ошибка при обновлении доски"
        except Exception as e:
            return False, f"Ошибка при переименовании: {str(e)}"
    
    def delete_board(self, board_id: int) -> tuple[bool, Optional[str]]:
        """Удалить доску"""
        board = self.board_repo.get_by_id(board_id)
        if not board:
            return False, "Доска не найдена"
        
        try:
            success = self.board_repo.delete(board_id)
            if success:
                return True, None
            return False, "Ошибка при удалении доски"
        except Exception as e:
            return False, f"Ошибка при удалении: {str(e)}"
    
    def create_column(self, board_id: int, name: str) -> tuple[bool, Optional[int], Optional[str]]:
        """Создать колонку"""
        # Валидация
        name = name.strip()
        if len(name) < 2:
            return False, None, "Название колонки должно быть минимум 2 символа"
        if len(name) > 100:
            return False, None, "Название колонки слишком длинное (максимум 100 символов)"
        
        # Проверка существования доски
        board = self.board_repo.get_by_id(board_id)
        if not board:
            return False, None, "Доска не найдена"
        
        # Проверка уникальности
        existing = self.column_repo.get_by_name(board_id, name)
        if existing:
            return False, None, "Колонка с таким названием уже существует"
        
        try:
            # Получить максимальную позицию
            columns = self.column_repo.get_all_by_board(board_id)
            max_position = max([c.position for c in columns], default=-1) + 1
            
            column_id = self.column_repo.create(board_id, name, max_position)
            return True, column_id, None
        except Exception as e:
            return False, None, f"Ошибка при создании колонки: {str(e)}"
    
    def get_column(self, column_id: int) -> Optional[Column]:
        """Получить колонку"""
        return self.column_repo.get_by_id(column_id)
    
    def list_columns(self, board_id: int) -> List[Column]:
        """Получить все колонки доски"""
        return self.column_repo.get_all_by_board(board_id)
    
    def get_first_column(self, board_id: int) -> Optional[Column]:
        """Получить первую колонку доски"""
        return self.column_repo.get_first_by_board(board_id)
    
    def delete_column(self, column_id: int) -> tuple[bool, Optional[str]]:
        """Удалить колонку"""
        column = self.column_repo.get_by_id(column_id)
        if not column:
            return False, "Колонка не найдена"
        
        try:
            success = self.column_repo.delete(column_id)
            if success:
                return True, None
            return False, "Ошибка при удалении колонки"
        except Exception as e:
            return False, f"Ошибка при удалении: {str(e)}"


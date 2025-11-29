"""
Визуализация досок (текстовый Kanban)
"""
from typing import List
from models.board import Board
from models.column import Column
from models.task import Task
from services.board_service import BoardService
from repositories.task_repository import TaskRepository
from repositories.column_repository import ColumnRepository
from database import Database

class BoardVisualizer:
    def __init__(self, board_service: BoardService):
        self.board_service = board_service
        db = Database()
        self.task_repo = TaskRepository(db)
        self.column_repo = board_service.column_repo
    
    def visualize_board(self, board: Board) -> str:
        """Визуализировать доску в текстовом формате"""
        columns = self.board_service.list_columns(board.id)
        
        if not columns:
            return f"📋 Доска: {board.name}\n\nНет колонок"
        
        text = f"📋 Доска: {board.name}\n\n"
        
        # Получить задачи для каждой колонки
        column_tasks = {}
        for column in columns:
            tasks = self.task_repo.get_all_by_column(column.id)
            column_tasks[column.id] = tasks
        
        # Определить максимальное количество задач в колонке
        max_tasks = max([len(tasks) for tasks in column_tasks.values()], default=0)
        
        # Заголовки колонок
        header = "│"
        separator = "├"
        for column in columns:
            col_name = column.name[:15].ljust(15)  # Ограничить длину названия
            header += f" {col_name} │"
            separator += "─" * (len(col_name) + 2) + "┤"
        
        text += header + "\n"
        text += separator + "\n"
        
        # Задачи по строкам
        for i in range(max_tasks):
            row = "│"
            for column in columns:
                tasks = column_tasks.get(column.id, [])
                if i < len(tasks):
                    task = tasks[i]
                    task_text = f"{task.priority_emoji} #{task.id} {task.title[:10]}"
                    task_text = task_text[:15].ljust(15)
                    row += f" {task_text} │"
                else:
                    row += " " + " " * 15 + " │"
            text += row + "\n"
        
        # Статистика
        total_tasks = sum([len(tasks) for tasks in column_tasks.values()])
        text += f"\nВсего задач: {total_tasks}\n"
        
        for column in columns:
            count = len(column_tasks.get(column.id, []))
            text += f"{column.name}: {count} | "
        
        return text.strip()
    
    def visualize_board_list(self, board: Board) -> str:
        """Визуализировать доску в виде списка задач по колонкам"""
        columns = self.board_service.list_columns(board.id)
        
        if not columns:
            return f"📋 Доска: {board.name}\n\nНет колонок"
        
        text = f"📋 Доска: {board.name}\n\n"
        
        # Получить задачи для каждой колонки
        for column in columns:
            tasks = self.task_repo.get_all_by_column(column.id)
            
            if tasks:
                text += f"📌 Колонка: {column.name}\n"
                for task in tasks:
                    priority_emoji = task.priority_emoji
                    text += f"  {priority_emoji} #{task.id} {task.title}\n"
                text += "\n"
            else:
                text += f"📌 Колонка: {column.name}\n  (пусто)\n\n"
        
        # Статистика
        total_tasks = sum([len(self.task_repo.get_all_by_column(col.id)) for col in columns])
        text += f"Всего задач: {total_tasks}"
        
        return text.strip()


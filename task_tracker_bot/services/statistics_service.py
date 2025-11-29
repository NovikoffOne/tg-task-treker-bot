"""
Сервис статистики
"""
from typing import Dict, List
from repositories.task_repository import TaskRepository
from repositories.project_repository import ProjectRepository
from repositories.board_repository import BoardRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.column_repository import ColumnRepository

class StatisticsService:
    def __init__(self, task_repo: TaskRepository, project_repo: ProjectRepository,
                 board_repo: BoardRepository, workspace_repo: WorkspaceRepository,
                 column_repo: ColumnRepository):
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.board_repo = board_repo
        self.workspace_repo = workspace_repo
        self.column_repo = column_repo
    
    def get_workspace_stats(self, workspace_id: int) -> Dict:
        """Получить статистику пространства"""
        boards = self.board_repo.get_all_by_workspace(workspace_id)
        projects = self.project_repo.get_all_by_workspace(workspace_id)
        
        total_tasks = 0
        tasks_by_status = {}
        
        for board in boards:
            columns = self.column_repo.get_all_by_board(board.id)
            for column in columns:
                tasks = self.task_repo.get_all_by_column(column.id)
                total_tasks += len(tasks)
                column_name = column.name
                if column_name not in tasks_by_status:
                    tasks_by_status[column_name] = 0
                tasks_by_status[column_name] += len(tasks)
        
        return {
            'workspace_id': workspace_id,
            'boards_count': len(boards),
            'projects_count': len(projects),
            'total_tasks': total_tasks,
            'tasks_by_status': tasks_by_status
        }
    
    def get_project_stats(self, project_id: str) -> Dict:
        """Получить статистику проекта"""
        project = self.project_repo.get_by_id(project_id)
        if not project:
            return {}
        
        tasks = self.task_repo.get_all_by_project(project_id)
        
        tasks_by_column = {}
        tasks_by_priority = {0: 0, 1: 0, 2: 0, 3: 0}
        
        for task in tasks:
            # По колонкам
            column = self.column_repo.get_by_id(task.column_id)
            if column:
                column_name = column.name
                if column_name not in tasks_by_column:
                    tasks_by_column[column_name] = 0
                tasks_by_column[column_name] += 1
            
            # По приоритетам
            if task.priority in tasks_by_priority:
                tasks_by_priority[task.priority] += 1
        
        return {
            'project_id': project_id,
            'project_name': project.name,
            'dashboard_stage': project.dashboard_stage,
            'total_tasks': len(tasks),
            'tasks_by_column': tasks_by_column,
            'tasks_by_priority': tasks_by_priority
        }
    
    def get_board_stats(self, board_id: int) -> Dict:
        """Получить статистику доски"""
        board = self.board_repo.get_by_id(board_id)
        if not board:
            return {}
        
        columns = self.column_repo.get_all_by_board(board_id)
        
        stats = {
            'board_id': board_id,
            'board_name': board.name,
            'columns': []
        }
        
        for column in columns:
            tasks = self.task_repo.get_all_by_column(column.id)
            stats['columns'].append({
                'column_id': column.id,
                'column_name': column.name,
                'tasks_count': len(tasks)
            })
        
        return stats


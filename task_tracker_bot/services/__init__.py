"""
Сервисы (бизнес-логика)
"""
from .workspace_service import WorkspaceService
from .board_service import BoardService
from .project_service import ProjectService
from .task_service import TaskService
from .sync_service import SyncService
from .statistics_service import StatisticsService
from .dependency_service import DependencyService
from .assignment_service import AssignmentService

__all__ = [
    'WorkspaceService',
    'BoardService',
    'ProjectService',
    'TaskService',
    'SyncService',
    'StatisticsService',
    'DependencyService',
    'AssignmentService',
]


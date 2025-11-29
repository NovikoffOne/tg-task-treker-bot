"""
Репозитории для работы с БД
"""
from .workspace_repository import WorkspaceRepository
from .board_repository import BoardRepository
from .column_repository import ColumnRepository
from .project_repository import ProjectRepository
from .task_repository import TaskRepository
from .personal_task_repository import PersonalTaskRepository
from .tag_repository import TagRepository
from .custom_field_repository import CustomFieldRepository
from .board_dependency_repository import BoardDependencyRepository
from .task_assignee_repository import TaskAssigneeRepository
from .project_member_repository import ProjectMemberRepository

__all__ = [
    'WorkspaceRepository',
    'BoardRepository',
    'ColumnRepository',
    'ProjectRepository',
    'TaskRepository',
    'PersonalTaskRepository',
    'TagRepository',
    'CustomFieldRepository',
    'BoardDependencyRepository',
    'TaskAssigneeRepository',
    'ProjectMemberRepository',
]


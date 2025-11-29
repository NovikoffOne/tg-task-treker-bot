"""
AI Agents для Task Tracker Bot
Архитектура из 5 агентов на базе io.net AI API
"""

from .orchestrator import OrchestratorAgent
from .task_manager import TaskManagerAgent
from .control_manager import ControlManagerAgent
from .data_manager import DataManagerAgent
from .analyze_manager import AnalyzeManagerAgent
from .agent_coordinator import AgentCoordinator

__all__ = [
    "OrchestratorAgent",
    "TaskManagerAgent",
    "ControlManagerAgent",
    "DataManagerAgent",
    "AnalyzeManagerAgent",
    "AgentCoordinator",
]



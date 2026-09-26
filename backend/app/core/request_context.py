"""Per-request/per-run context used to attribute security telemetry to a project and task."""
from contextvars import ContextVar
from typing import Optional

current_project_id: ContextVar[Optional[str]] = ContextVar("current_project_id", default=None)
current_task_id: ContextVar[Optional[str]] = ContextVar("current_task_id", default=None)


def set_context(project_id: Optional[str] = None, task_id: Optional[str] = None):
    current_project_id.set(project_id)
    current_task_id.set(task_id)

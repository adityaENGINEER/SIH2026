from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class Step(BaseModel):
    step_id: str
    description: str
    capability: str
    status: str = "pending" # pending, running, completed, failed, skipped
    depends_on: List[str] = Field(default_factory=list)
    input: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: "plan_" + datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    goal: Optional[str] = None
    steps: List[Step] = Field(default_factory=list)

class Observation(BaseModel):
    step_id: str
    capability: str
    status: str
    duration_ms: int
    summary: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: str

class ValidationResult(BaseModel):
    valid: bool
    step_id: Optional[str] = None

    reason: Optional[str] = None
    issues: List[str] = Field(default_factory=list)

class TaskState(BaseModel):
    task_id: str
    user_request: str
    document_id: Optional[str] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: str = "queued" # queued, planning, executing, observing, validating, replanning, completed, failed, cancelled
    current_step: Optional[str] = None
    plan: Optional[Plan] = None
    observations: List[Observation] = Field(default_factory=list)
    validation_results: List[ValidationResult] = Field(default_factory=list)
    replan_count: int = 0
    max_replans: int
    step_count: int = 0
    max_steps: int
    created_at: str
    updated_at: str
    final_result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    cancel_requested: bool = False
    routing: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None
    deliverable_id: Optional[str] = None
    approval_id: Optional[str] = None

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}

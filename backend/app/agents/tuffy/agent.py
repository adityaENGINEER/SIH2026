import os
import re
import json
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.request_context import set_context
from app.agents.tuffy.state import TaskState, TERMINAL_STATUSES
from app.agents.tuffy.planner import planner
from app.agents.tuffy.executor import executor
from app.agents.tuffy.observer import observer
from app.agents.tuffy.validator import validator
from app.agents.tuffy.replanner import replanner

logger = logging.getLogger(__name__)

SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9_\-]+$")

class TuffyAgent:
    def __init__(self):
        self.tasks_dir = os.path.join(settings.storage_root, "tasks")
        os.makedirs(self.tasks_dir, exist_ok=True)
        self.max_steps = settings.max_agent_steps
        self.max_replans = settings.max_replans
        # Runs scheduled or executing in this process; any other non-terminal run has no worker.
        self.scheduled_tasks: set = set()
        self.active_tasks: set = set()

    def _get_task_dir(self, task_id: str) -> str:
        return os.path.join(self.tasks_dir, task_id)

    def _get_state_path(self, task_id: str) -> str:
        return os.path.join(self._get_task_dir(task_id), "state.json")

    def _save_state(self, state: TaskState):
        state.updated_at = datetime.utcnow().isoformat() + "Z"
        path = self._get_state_path(state.task_id)
        # A cancel request written by the API must survive saves made by the running loop.
        if not state.cancel_requested and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state.cancel_requested = bool(json.load(f).get("cancel_requested"))
            except (OSError, ValueError):
                pass
        with open(path, "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))

    def get_state(self, task_id: str) -> Optional[TaskState]:
        if not SAFE_TASK_ID.match(task_id or ""):
            return None
        path = self._get_state_path(task_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return TaskState(**data)

    def get_tasks_for_project(self, project_id: str) -> list[TaskState]:
        tasks = []
        if not os.path.exists(self.tasks_dir):
            return tasks
        for task_id in os.listdir(self.tasks_dir):
            state = self.get_state(task_id)
            if state and state.project_id == project_id:
                tasks.append(state)
        # sort by created_at descending
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    def create_task(self, user_request: str, document_id: Optional[str] = None, project_id: Optional[str] = None,
                    conversation_id: Optional[str] = None, routing: Optional[Dict[str, Any]] = None) -> str:
        task_id = f"task_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        task_dir = self._get_task_dir(task_id)
        os.makedirs(task_dir, exist_ok=True)
        
        state = TaskState(
            task_id=task_id,
            user_request=user_request,
            document_id=document_id,
            project_id=project_id,
            conversation_id=conversation_id,
            routing=routing,
            max_replans=self.max_replans,
            max_steps=self.max_steps,
            created_at=datetime.utcnow().isoformat() + "Z",
            updated_at=datetime.utcnow().isoformat() + "Z"
        )
        self._save_state(state)
        self.scheduled_tasks.add(task_id)
        return task_id

    def request_cancel(self, task_id: str) -> TaskState:
        """Persists a cancel request. A run with no live worker is finalized immediately."""
        state = self.get_state(task_id)
        if state.status in TERMINAL_STATUSES:
            return state
        state.cancel_requested = True
        if task_id not in self.active_tasks:
            self._finish(state, "cancelled", {"code": "CANCELLED", "message": "Run cancelled by user before execution."})
        else:
            self._save_state(state)
        return state

    def recover_if_orphaned(self, state: TaskState) -> TaskState:
        """A non-terminal run that is neither scheduled nor executing in this process can never progress: fail it explicitly."""
        if state.status in TERMINAL_STATUSES or state.task_id in self.active_tasks or state.task_id in self.scheduled_tasks:
            return state
        self._finish(state, "failed", {
            "code": "ORPHANED_RUN",
            "message": f"Run was interrupted while '{state.status}' (backend restarted or worker stopped). It did not complete.",
        })
        return state

    def recover_orphaned_runs(self) -> int:
        count = 0
        for task_id in os.listdir(self.tasks_dir):
            state = self.get_state(task_id)
            if state and state.status not in TERMINAL_STATUSES:
                self.recover_if_orphaned(state)
                count += 1
        return count

    def _finish(self, state: TaskState, status: str, error: Optional[Dict[str, Any]] = None):
        if state.plan:
            for step in state.plan.steps:
                if step.status == "running":
                    step.status = "failed"
                    step.error = step.error or error or {"code": status.upper(), "message": f"Run ended ({status}) during this step."}
        state.status = status
        if error:
            state.error = error
        state.completed_at = datetime.utcnow().isoformat() + "Z"
        self._save_state(state)
        if state.project_id and state.conversation_id:
            try:
                from app.services.chat_service import chat_service
                chat_service.update_task_message(state.project_id, state.conversation_id, state.task_id, status)
            except (OSError, ValueError) as e:
                logger.error(f"Could not update chat message for {state.task_id}: {e}")

    async def run_task(self, task_id: str) -> Dict[str, Any]:
        state = self.get_state(task_id)
        if not state:
            return {"error": {"code": "TASK_NOT_FOUND", "message": "Task not found."}}
            
        if state.status in TERMINAL_STATUSES:
            self.scheduled_tasks.discard(task_id)
            return {"error": {"code": "TASK_ALREADY_FINISHED", "message": "Task has already finished."}}

        set_context(project_id=state.project_id, task_id=state.task_id)
        self.scheduled_tasks.discard(task_id)
        self.active_tasks.add(task_id)
        try:
            return await self._orchestrate(state)
        except Exception as e:
            logger.exception(f"Agent loop failed for {task_id}")
            self._finish(state, "failed", {"code": "EXECUTION_FAILED", "message": f"Unexpected error in agent loop: {e}"})
            return {"error": state.error}
        finally:
            self.active_tasks.discard(task_id)

    def _cancelled(self, state: TaskState) -> bool:
        self._save_state(state)  # merges a cancel request persisted by the API
        if state.cancel_requested:
            self._finish(state, "cancelled", {"code": "CANCELLED", "message": "Run cancelled by user. No further steps were executed."})
            return True
        return False

    async def _orchestrate(self, state: TaskState) -> Dict[str, Any]:
        # 1. PLAN
        if not state.plan:
            state.status = "planning"
            self._save_state(state)
            
            state.plan = planner.create_plan(state)
            
        while state.status not in TERMINAL_STATUSES:
            if self._cancelled(state):
                break
            
            # Step limit check
            if state.step_count >= state.max_steps:
                self._finish(state, "failed", {"code": "STEP_LIMIT_REACHED", "message": f"Exceeded maximum steps ({state.max_steps})"})
                break
                
            state.status = "executing"
            self._save_state(state)
            
            # Find next pending step whose dependencies are completed
            pending_step = None
            completed_step_ids = {s.step_id for s in state.plan.steps if s.status == "completed"}
            
            for s in state.plan.steps:
                if s.status == "pending":
                    if all(dep in completed_step_ids for dep in s.depends_on):
                        pending_step = s
                        break
            
            if not pending_step:
                self._complete(state)
                break
                
            state.current_step = pending_step.step_id
            pending_step.status = "running"
            
            # Context piping for generate_approval_document
            if pending_step.capability == "tool_execution" and pending_step.input.get("tool_name") == "generate_approval_document":
                search_result = None
                for completed in state.plan.steps:
                    if completed.capability == "knowledge_search" and completed.status == "completed":
                        search_result = completed.result
                        break
                if search_result and "answer" in search_result:
                    tool_input = pending_step.input.setdefault("tool_input", {})
                    tool_input["knowledge_context"] = search_result["answer"]
                    tool_input["evidence"] = search_result.get("evidence", [])
                    
            if pending_step.capability == "tool_execution" and pending_step.input.get("tool_name") == "analyze_image" and state.document_id:
                from app.services.document_service import document_service
                doc = document_service.get_file_path(state.document_id)
                if "error" not in doc:
                    pending_step.input.setdefault("tool_input", {})["file_path"] = doc["file_path"]
                    
            self._save_state(state)
            
            # 2. EXECUTE
            start_time = time.time()
            
            # Simple bounded retry for document indexing race
            max_index_retries = 3
            index_retry_count = 0
            success = False
            result_data = {}
            
            import asyncio
            while index_retry_count < max_index_retries:
                success, result_data = await executor.execute_step(pending_step)
                if not success and isinstance(result_data.get("error"), dict) and result_data["error"].get("code") == "DOCUMENT_INDEXING":
                    index_retry_count += 1
                    if index_retry_count < max_index_retries:
                        await asyncio.sleep(2) # bounded wait
                        continue
                break
                
            duration_ms = int((time.time() - start_time) * 1000)
            
            # If still DOCUMENT_INDEXING, convert to DOCUMENT_INDEXING_TIMEOUT
            if not success and isinstance(result_data.get("error"), dict) and result_data["error"].get("code") == "DOCUMENT_INDEXING":
                result_data["error"]["code"] = "DOCUMENT_INDEXING_TIMEOUT"
                result_data["error"]["message"] = "Document indexing timed out."
            
            pending_step.status = "completed" if success else "failed"
            pending_step.result = result_data if success else None
            pending_step.error = result_data.get("error") if not success else None
            state.step_count += 1
            
            state.status = "observing"
            self._save_state(state)
            
            # 3. OBSERVE
            obs = observer.observe(pending_step, success, result_data, duration_ms)
            state.observations.append(obs)
            
            state.status = "validating"
            self._save_state(state)
            
            # 4. VALIDATE
            val_result = validator.validate_step(pending_step)
            state.validation_results.append(val_result)
            
            if val_result.valid:
                continue
            else:
                if "DOCUMENT_INDEXING_TIMEOUT" in val_result.issues:
                    self._finish(state, "failed", {"code": "DOCUMENT_INDEXING_TIMEOUT", "message": "Document indexing timed out."})
                    break
                if "DOCUMENT_NOT_IN_PROJECT" in val_result.issues:
                    self._finish(state, "failed", pending_step.error)
                    break
                    
                if self._cancelled(state):
                    break
                state.status = "replanning"
                self._save_state(state)
                
                # 5. REPLAN
                if state.replan_count >= state.max_replans:
                    self._finish(state, "failed", {
                        "code": "REPLAN_LIMIT_REACHED",
                        "message": f"Validation failed and replan limit ({state.max_replans}) reached. Last issue: {val_result.reason}",
                    })
                    break
                    
                state.replan_count += 1
                state.plan = replanner.replan(state)
                self._save_state(state)

        if state.status == "completed":
            return {"status": "completed", "result": state.final_result}
        return {"status": state.status, "error": state.error}

    def _complete(self, state: TaskState):
        state.final_result = {}
        for completed_step in state.plan.steps:
            if completed_step.result:
                if completed_step.capability == "knowledge_search":
                    state.final_result.update(completed_step.result)
                elif completed_step.capability == "tool_execution":
                    tool_res = completed_step.result.get("result", {})
                    if "output" in tool_res:
                        state.final_result["output"] = tool_res["output"]
                    elif "file_path" in tool_res:
                        state.final_result["output"] = {"path": tool_res["file_path"]}
                    if "grounding" in tool_res:
                        state.final_result["grounding"] = tool_res["grounding"]
                    if "analysis" in tool_res:
                        state.final_result["answer"] = tool_res["analysis"]
                        state.final_result["vision_model"] = tool_res.get("model")
                        
        if not state.final_result and state.plan.steps:
            state.final_result = state.plan.steps[-1].result
        self._register_deliverable(state)
        self._finish(state, "completed")

    def _register_deliverable(self, state: TaskState):
        """A generated approval document becomes a project deliverable with a human sign-off approval record."""
        output = (state.final_result or {}).get("output") or {}
        path = output.get("path")
        if not state.project_id or not path or not str(path).lower().endswith(".docx"):
            return
        from app.services.deliverable_service import deliverable_service
        from app.services.approval_service import approval_service
        title = f"Approval Note — {state.user_request[:60]}"
        deliverable = deliverable_service.register_file(state.project_id, title, path, task_id=state.task_id)
        if "error" in deliverable:
            state.final_result["deliverable_error"] = deliverable["error"]
            return
        sources = sorted({s.get("document_id") for s in (state.final_result.get("sources") or []) if s.get("document_id")})
        approval = approval_service.create_approval(
            project_id=state.project_id, title=title, conversation_id=state.conversation_id,
            task_id=state.task_id, agent_run_id=state.task_id, deliverable_id=deliverable["deliverable_id"],
            source_document_ids=sources, output_document_ids=[deliverable["deliverable_id"]],
        )
        deliverable_service.link_approval(state.project_id, deliverable["deliverable_id"], approval["approval_id"])
        # AI may only request review; approval is exclusively a human action.
        approval_service.submit_for_review(state.project_id, approval["approval_id"])
        state.deliverable_id = deliverable["deliverable_id"]
        state.approval_id = approval["approval_id"]

agent = TuffyAgent()

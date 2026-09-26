import uuid
from app.agents.tuffy.state import Plan, Step, TaskState

class TuffyReplanner:
    def replan(self, state: TaskState) -> Plan:
        """
        Creates a new plan based on the failure context.
        """
        last_val = state.validation_results[-1] if state.validation_results else None
        issues = last_val.issues if last_val else []
        
        # If it was a knowledge search failure, try a broader query
        if "NO_RELEVANT_CONTEXT" in issues:
            new_query = state.user_request + " detailed information specifics"
            if state.plan:
                new_steps = []
                for s in state.plan.steps:
                    new_s = Step(**s.model_dump())
                    # A search rejected by the validator is still "completed" at the executor level.
                    rejected = new_s.status == "failed" or new_s.step_id == last_val.step_id
                    if rejected and new_s.capability == "knowledge_search":
                        new_s.status = "pending"
                        new_s.input["query"] = new_query
                        new_s.result = None
                        new_s.error = None
                    elif new_s.status == "failed":
                        new_s.status = "pending"
                        new_s.result = None
                        new_s.error = None
                    new_steps.append(new_s)
                return Plan(steps=new_steps)
            else:
                step = Step(
                    step_id=f"step_{uuid.uuid4().hex[:8]}",
                    description="Re-attempt knowledge search with broader query parameters.",
                    capability="knowledge_search",
                    status="pending",
                    input={
                        "query": new_query,
                        "document_id": state.document_id,
                        "project_id": state.project_id
                    }
                )
                return Plan(steps=[step])
            
        # Default fallback: retry original plan (but will likely fail if deterministic)
        # We can just return the same plan with steps reset to pending
        if state.plan:
            new_steps = []
            for s in state.plan.steps:
                new_s = Step(**s.model_dump())
                new_s.status = "pending"
                new_s.result = None
                new_s.error = None
                new_steps.append(new_s)
            
            return Plan(steps=new_steps)
            
        return Plan(steps=[])

replanner = TuffyReplanner()

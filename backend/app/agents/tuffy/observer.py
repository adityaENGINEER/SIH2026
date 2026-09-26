from datetime import datetime
from typing import Dict, Any
from app.agents.tuffy.state import Observation, Step

class TuffyObserver:
    def observe(self, step: Step, success: bool, result: Dict[str, Any], duration_ms: int) -> Observation:
        """
        Creates a safe observation log from step execution.
        """
        status_str = "completed" if success else "failed"
        
        # Safe result summary - do not log entire answers or secrets
        if success:
            if step.capability == "knowledge_search":
                grounded = result.get("grounded", False)
                sources = result.get("retrieval", {}).get("results_found", 0)
                summary = f"Knowledge search returned grounded={grounded} with {sources} sources."
            else:
                summary = "Step executed successfully."
        else:
            err = result.get("error", {})
            summary = f"Error {err.get('code', 'UNKNOWN')}: {err.get('message', 'No message')}"

        return Observation(
            step_id=step.step_id,
            capability=step.capability,
            status=status_str,
            duration_ms=duration_ms,
            summary=summary,
            result=result if success else None,
            error=result.get("error") if not success else None,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

observer = TuffyObserver()

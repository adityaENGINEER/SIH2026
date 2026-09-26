import logging
from typing import Dict, Any, Tuple
from app.agents.tuffy.state import Step
from app.agents.tuffy.capabilities import capabilities_registry

logger = logging.getLogger(__name__)

class TuffyExecutor:
    async def execute_step(self, step: Step) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes a plan step using the mapped capability.
        Returns (success, result_dict)
        """
        capability_name = step.capability
        
        if capability_name not in capabilities_registry:
            error_msg = f"Capability '{capability_name}' not found or unsupported."
            logger.error(error_msg)
            return False, {"error": {"code": "CAPABILITY_NOT_FOUND", "message": error_msg}}
            
        capability = capabilities_registry[capability_name]
        
        try:
            result = await capability.execute(step.input)
            
            if "error" in result:
                return False, result
                
            return True, result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Execution failed for step {step.step_id}: {str(e)}")
            return False, {"error": {"code": "EXECUTION_FAILED", "message": str(e)}}

executor = TuffyExecutor()

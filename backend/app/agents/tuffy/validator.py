from app.agents.tuffy.state import Step, ValidationResult

class TuffyValidator:
    def validate_step(self, step: Step) -> ValidationResult:
        """
        Validates the structural success of a step.
        """
        issues = []
        
        if step.status == "failed":
            error_code = "UNKNOWN_ERROR"
            if isinstance(step.error, dict):
                error_code = step.error.get("code", "UNKNOWN_ERROR")
            elif isinstance(step.error, str):
                error_code = step.error
                
            issues.append(error_code)
            return ValidationResult(valid=False, step_id=step.step_id, reason=f"Step execution failed: {step.error}", issues=issues)
            
        if step.status != "completed":
            issues.append("STEP_INCOMPLETE")
            return ValidationResult(valid=False, step_id=step.step_id, reason="Step did not complete.", issues=issues)
            
        result = step.result or {}
        
        if step.capability == "knowledge_search":
            grounded = result.get("grounded", False)
            answer = str(result.get("answer", "")).lower()
            rejection_phrases = [
                "does not contain", 
                "could not find", 
                "not available", 
                "cannot answer",
                "does not provide"
            ]
            if not grounded or any(phrase in answer for phrase in rejection_phrases):
                issues.append("NO_RELEVANT_CONTEXT")
                return ValidationResult(valid=False, step_id=step.step_id, reason="Insufficient knowledge context to answer.", issues=issues)
                
        if step.capability == "tool_execution":
            if step.input.get("tool_name") == "generate_approval_document":
                import os
                from app.core.config import settings
                tool_res = result.get("result", {})
                file_path = tool_res.get("file_path") or (tool_res.get("output", {})).get("path")
                
                if not file_path:
                    issues.append("MISSING_FILE_PATH")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="Document generator did not return a file path.", issues=issues)
                    
                if not file_path.endswith(".docx"):
                    issues.append("INVALID_FILE_TYPE")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="Generated file is not a .docx", issues=issues)
                    
                if not os.path.exists(file_path):
                    issues.append("FILE_NOT_FOUND")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="Generated file does not exist on disk.", issues=issues)
                    
                if os.path.getsize(file_path) == 0:
                    issues.append("FILE_EMPTY")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="Generated file is empty.", issues=issues)
                    
                if not os.path.abspath(file_path).startswith(os.path.abspath(settings.storage_root)):
                    issues.append("PATH_TRAVERSAL_DETECTED")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="File path is outside approved storage.", issues=issues)

                grounding = tool_res.get("grounding")
                if grounding is not None and grounding.get("facts_from_source", 0) == 0:
                    issues.append("NO_GROUNDED_FACTS")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="Generated document contains no facts traceable to source evidence.", issues=issues)
            if step.input.get("tool_name") == "execute_python_code":
                tool_res = result.get("result", {})
                if not tool_res:
                    issues.append("MISSING_EXECUTION_RESULT")
                    return ValidationResult(valid=False, step_id=step.step_id, reason="Sandbox returned no result.", issues=issues)
                
                status = tool_res.get("status")
                exit_code = tool_res.get("exit_code", 1)
                stderr = tool_res.get("stderr", "")
                
                if status == "failed" or exit_code != 0:
                    if "timed out" in stderr:
                        issues.append("EXECUTION_TIMEOUT")
                    else:
                        issues.append("NON_ZERO_EXIT")
                    return ValidationResult(valid=False, step_id=step.step_id, reason=f"Code execution failed with exit code {exit_code}: {stderr}", issues=issues)
            
            if step.input.get("tool_name") == "analyze_image":
                tool_res = result.get("result", {})
                if "error" in tool_res:
                    issues.append("VISION_FAILED")
                    return ValidationResult(valid=False, step_id=step.step_id, reason=f"Vision model failed: {tool_res['error']}", issues=issues)
                    
            if "result" not in result and "error" not in result and "bytes_written" not in result and "value" not in result:
                # Some tools put output right in result, some under result dict
                pass
                
        return ValidationResult(valid=True, step_id=step.step_id, reason="Step completed successfully", issues=issues)

validator = TuffyValidator()

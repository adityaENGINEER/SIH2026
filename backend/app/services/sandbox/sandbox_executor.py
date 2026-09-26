import os
import uuid
import json
import logging
import subprocess
import shutil
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class SandboxExecutionResult(BaseModel):
    execution_id: str
    status: str
    stdout: str
    stderr: str
    exit_code: int

class SandboxExecutor:
    def __init__(self):
        self.sandbox_dir = os.path.join(settings.storage_root, "sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.executions: Dict[str, SandboxExecutionResult] = {}
        
        # Test if docker is available
        self.docker_available = False
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            if res.returncode == 0:
                self.docker_available = True
                logger.info("Docker is available for SandboxExecutor")
            else:
                logger.warning("Docker is installed but daemon is not running. Using fallback.")
        except Exception:
            logger.warning("Docker is not available. Using controlled development fallback.")
            
    def get_execution(self, execution_id: str) -> SandboxExecutionResult:
        if execution_id not in self.executions:
            return None
        return self.executions[execution_id]

    def execute(self, code: str, timeout_sec: int = 10) -> SandboxExecutionResult:
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        # Security checks
        if "import os" in code and "os.system" in code:
            pass
        
        # Block obvious path traversal
        if "../" in code or "..\\" in code:
            return SandboxExecutionResult(
                execution_id=execution_id,
                status="failed",
                stdout="",
                stderr="Path traversal attempt detected and blocked.",
                exit_code=1
            )
            
        workspace_path = os.path.join(self.sandbox_dir, execution_id)
        os.makedirs(workspace_path, exist_ok=True)
        
        script_path = os.path.join(workspace_path, "main.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        stdout_data = ""
        stderr_data = ""
        exit_code = 1
        status = "failed"
        
        try:
            if self.docker_available:
                # Use Docker
                # Ensure path is absolute and formatted for docker (Windows -> Unix path is tricky in WSL, but Docker Desktop handles C:\...)
                abs_workspace = os.path.abspath(workspace_path)
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{abs_workspace}:/sandbox",
                    "-w", "/sandbox",
                    "--network", "none",
                    "--memory", "128m",
                    "--cpus", "0.5",
                    "python:3.12-slim",
                    "python", "main.py"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
                stdout_data = res.stdout
                stderr_data = res.stderr
                exit_code = res.returncode
            else:
                # Fallback to local subprocess
                import sys
                cmd = [sys.executable, "main.py"]
                res = subprocess.run(cmd, cwd=workspace_path, capture_output=True, text=True, timeout=timeout_sec)
                stdout_data = res.stdout
                stderr_data = res.stderr
                exit_code = res.returncode
                
            status = "completed" if exit_code == 0 else "failed"
                
        except subprocess.TimeoutExpired as e:
            status = "failed"
            stderr_data = f"Execution timed out after {timeout_sec} seconds."
            if e.stdout:
                stdout_data = e.stdout.decode('utf-8', errors='ignore') if isinstance(e.stdout, bytes) else e.stdout
            if e.stderr:
                stderr_data += "\n" + (e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else e.stderr)
            exit_code = 124 # Common timeout exit code
        except Exception as e:
            status = "failed"
            stderr_data = f"Sandbox execution error: {str(e)}"
            exit_code = 1
            
        finally:
            # Clean up
            try:
                shutil.rmtree(workspace_path)
            except Exception as e:
                logger.error(f"Failed to cleanup sandbox workspace {workspace_path}: {e}")
                
        result = SandboxExecutionResult(
            execution_id=execution_id,
            status=status,
            stdout=stdout_data,
            stderr=stderr_data,
            exit_code=exit_code
        )
        self.executions[execution_id] = result
        return result

sandbox_service = SandboxExecutor()

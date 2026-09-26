import uuid
from typing import Optional
from app.agents.tuffy.state import Plan, Step, TaskState
from app.services.document_service import document_service
from app.services.model_router import model_router

# Approval documents need broader evidence; still capped by rag_max_top_k and rag_max_context_chars.
DOC_GEN_TOP_K = 5

class TuffyPlanner:
    def create_plan(self, state: TaskState) -> Plan:
        """
        Creates a deterministic plan for M11.
        Parses user_request to decide if we need knowledge_search, tool_execution, or both.
        """
        req_lower = state.user_request.lower()
        steps = []
        
        needs_search = False
        needs_calc = False
        needs_write = False
        needs_doc_gen = False
        needs_sandbox = False
        needs_vision = False
        
        routing = state.routing
        if routing is None:
            doc_meta = document_service.get_metadata(state.document_id) if state.document_id else None
            routing = model_router.route(state.user_request, doc_meta)
        if routing.get("purpose") == "vision":
            needs_vision = True
            
        # Simple heuristic
        sandbox_keywords = ["run code", "execute code", "execute python", "python script", "run python", "sandbox"]
        if any(kw in req_lower for kw in sandbox_keywords):
            needs_sandbox = True
            
        if "calculate" in req_lower or "*" in req_lower or "/" in req_lower or "+" in req_lower:
            needs_calc = True
        doc_gen_keywords = ["approval note", "approval document", "authorization note", "authorization document", "permit extension", "permit authorization", "generate approval", "create approval document", "prepare authorization", "draft authorization", "prepare permit extension", "authorization request"]
        if any(kw in req_lower for kw in doc_gen_keywords):
            needs_doc_gen = True
        # Document generation consumes the knowledge_search answer as its context, so it always needs a search step.
        text_request = "find" in req_lower or "search" in req_lower or "problem" in req_lower or "inspection" in req_lower or "analyze" in req_lower
        if (text_request or state.document_id or needs_doc_gen) and not (needs_vision and not needs_doc_gen):
            needs_search = True
        if "write" in req_lower or "output" in req_lower:
            needs_write = True
            
        # Default to search if nothing matched
        if not needs_calc and not needs_search and not needs_write and not needs_sandbox and not needs_vision:
            needs_search = True
            
        step_idx = 1
        last_step_id = None
        
        if needs_search:
            s_id = f"step_{step_idx}"
            
            # If we need to generate a document, the raw user request (e.g. "Prepare approval note") 
            # makes a poor RAG query. We should use a query that extracts the necessary data.
            search_query = state.user_request
            if needs_doc_gen:
                search_query = f"Extract all relevant technical findings, data points, and context required to {state.user_request.lower()}"
                
            step = Step(
                step_id=s_id,
                description="Search the knowledge base for relevant information.",
                capability="knowledge_search",
                status="pending",
                input={
                    "query": search_query,
                    "document_id": state.document_id,
                    "project_id": state.project_id,
                    **({"top_k": DOC_GEN_TOP_K} if needs_doc_gen else {}),
                }
            )
            steps.append(step)
            last_step_id = s_id
            step_idx += 1
            
        if needs_calc:
            s_id = f"step_{step_idx}"
            calc_expr = state.user_request
            if calc_expr.lower().startswith("calculate "):
                calc_expr = calc_expr[10:].strip()
                
            step = Step(
                step_id=s_id,
                description="Calculate mathematical expression.",
                capability="tool_execution",
                status="pending",
                depends_on=[last_step_id] if last_step_id else [],
                input={
                    "tool_name": "calculator",
                    "tool_input": {"expression": calc_expr}
                }
            )
            steps.append(step)
            last_step_id = s_id
            step_idx += 1
            
        if needs_write:
            s_id = f"step_{step_idx}"
            step = Step(
                step_id=s_id,
                description="Write output to a file.",
                capability="tool_execution",
                status="pending",
                depends_on=[last_step_id] if last_step_id else [],
                input={
                    "tool_name": "file_writer",
                    "tool_input": {"path": "storage/temp/output.txt", "content": state.user_request}
                }
            )
            steps.append(step)
            last_step_id = s_id
            
        if needs_doc_gen:
            s_id = f"step_{step_idx}"
            step = Step(
                step_id=s_id,
                description="Generate industrial authorization document.",
                capability="tool_execution",
                status="pending",
                depends_on=[last_step_id] if last_step_id else [],
                input={
                    "tool_name": "generate_approval_document",
                    "tool_input": {
                        "task_id": state.task_id,
                        "document_data": {} # Will be populated by previous step or statically for now
                    }
                }
            )
            steps.append(step)
            last_step_id = s_id
            step_idx += 1
            
        if needs_sandbox:
            s_id = f"step_{step_idx}"
            
            # Simple heuristic to extract the code from request
            # E.g. "Execute Python code: print(2 + 3)" -> "print(2 + 3)"
            code = req_lower
            if ":" in code:
                code = state.user_request.split(":", 1)[1].strip()
            elif "\n" in code:
                code = state.user_request.split("\n", 1)[1].strip()
            elif "print(" in code or "sum(" in code:
                # Naive fallback for the tests
                code = state.user_request.replace("execute python code", "").strip()
            else:
                code = state.user_request
                
            step = Step(
                step_id=s_id,
                description="Execute Python code in secure sandbox.",
                capability="tool_execution",
                status="pending",
                depends_on=[last_step_id] if last_step_id else [],
                input={
                    "tool_name": "execute_python_code",
                    "tool_input": {
                        "code": code
                    }
                }
            )
            steps.append(step)
            last_step_id = s_id
            step_idx += 1
            
        if needs_vision:
            s_id = f"step_{step_idx}"
            step = Step(
                step_id=s_id,
                description="Analyze image using vision model.",
                capability="tool_execution",
                status="pending",
                depends_on=[last_step_id] if last_step_id else [],
                input={
                    "tool_name": "analyze_image",
                    "tool_input": {
                        "file_path": "", # Will be dynamically injected by agent if tied to a document upload
                        "prompt": state.user_request
                    }
                }
            )
            steps.append(step)
            last_step_id = s_id
            step_idx += 1
            
        return Plan(steps=steps)

planner = TuffyPlanner()

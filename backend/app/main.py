import logging
from fastapi import FastAPI
from app.api.routes import health, system, models, documents, ocr, knowledge, tasks, tools, sandbox, vision, projects, approvals, deliverables, security

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Builder AI Workbench", version="1.0.0")

from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(models.router, prefix="/api", tags=["Models"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(ocr.router, prefix="/api", tags=["OCR"])
app.include_router(knowledge.router, prefix="/api", tags=["Knowledge"])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
app.include_router(tools.router, prefix="/api", tags=["Tools"])
app.include_router(sandbox.router, prefix="/api/sandbox", tags=["Sandbox"])
app.include_router(vision.router, prefix="/api/vision", tags=["Vision"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(approvals.router, prefix="/api/projects", tags=["Approvals"])
app.include_router(deliverables.router, prefix="/api/projects", tags=["Deliverables"])
app.include_router(security.router, prefix="/api/security", tags=["Security"])


@app.on_event("startup")
def recover_orphaned_agent_runs():
    from app.agents.tuffy.agent import agent
    recovered = agent.recover_orphaned_runs()
    if recovered:
        logging.getLogger(__name__).warning(f"Marked {recovered} orphaned agent run(s) as failed after startup.")


@app.exception_handler(ValueError)
async def invalid_identifier_handler(request, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400, content={"detail": {"code": "INVALID_REQUEST", "message": str(exc)}})


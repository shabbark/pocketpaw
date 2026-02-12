# Deep Work API endpoints.
# Created: 2026-02-12
# Updated: 2026-02-12 — Added success key, tightened description validation.
#
# FastAPI router for Deep Work orchestration:
#   POST /start                     — submit project (natural language)
#   GET  /projects/{id}/plan        — get generated plan for review
#   POST /projects/{id}/approve     — approve plan, start execution
#   POST /projects/{id}/pause       — pause execution
#   POST /projects/{id}/resume      — resume execution
#
# Mount: app.include_router(deep_work_router, prefix="/api/deep-work")

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Deep Work"])


class StartDeepWorkRequest(BaseModel):
    """Request body for starting a Deep Work project."""

    description: str = Field(
        ..., min_length=10, max_length=5000, description="Natural language project description"
    )


@router.post("/start")
async def start_deep_work(request: StartDeepWorkRequest) -> dict[str, Any]:
    """Submit a new project for Deep Work planning.

    Creates a project, runs the planner (research -> PRD -> tasks -> team),
    and returns the project in AWAITING_APPROVAL status.
    """
    from pocketclaw.deep_work import start_deep_work as _start

    try:
        project = await _start(request.description)
        return {"success": True, "project": project.to_dict()}
    except Exception as e:
        logger.exception(f"Deep Work start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/plan")
async def get_plan(project_id: str) -> dict[str, Any]:
    """Get the generated plan for a project.

    Returns project details, tasks, progress, and the PRD document.
    """
    from pocketclaw.mission_control.manager import get_mission_control_manager

    manager = get_mission_control_manager()
    project = await manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = await manager.get_project_tasks(project_id)
    progress = await manager.get_project_progress(project_id)

    # Get PRD document if available
    prd = None
    if project.prd_document_id:
        prd_doc = await manager.get_document(project.prd_document_id)
        if prd_doc:
            prd = prd_doc.to_dict()

    return {
        "project": project.to_dict(),
        "tasks": [t.to_dict() for t in tasks],
        "progress": progress,
        "prd": prd,
    }


@router.post("/projects/{project_id}/approve")
async def approve_project(project_id: str) -> dict[str, Any]:
    """Approve a project plan and start execution."""
    from pocketclaw.deep_work import approve_project as _approve

    try:
        project = await _approve(project_id)
        return {"success": True, "project": project.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Approve failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/pause")
async def pause_project(project_id: str) -> dict[str, Any]:
    """Pause project execution."""
    from pocketclaw.deep_work import pause_project as _pause

    try:
        project = await _pause(project_id)
        return {"success": True, "project": project.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Pause failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/resume")
async def resume_project(project_id: str) -> dict[str, Any]:
    """Resume a paused project."""
    from pocketclaw.deep_work import resume_project as _resume

    try:
        project = await _resume(project_id)
        return {"success": True, "project": project.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

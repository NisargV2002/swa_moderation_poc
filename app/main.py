"""
FastAPI Entrypoint

Purpose:
- Expose moderation APIs.
- Connect UI with backend pipeline.
"""

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi import Query

from app.db import (
    get_projects,
    get_project_by_id,
    get_moderation_history,
    get_run_policy_results,
)

from app.moderation_engine import (
    run_moderation
)

from config.settings import settings


app = FastAPI(
    title=settings.APP_NAME
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": settings.APP_NAME,
        "scope": settings.CONTENT_SCOPE,
        "enabledPolicies": (
            settings.enabled_policies
        ),
        "llmEnabled": settings.USE_LLM,
        "deployment": (
            settings.AZURE_OPENAI_DEPLOYMENT
        )
    }


@app.get("/projects")
def projects():
    """
    Lightweight project list for UI table.
    """

    return get_projects()


@app.get("/projects/{project_id}")
def project_details(project_id: int):
    """
    Full project details.
    """

    project = get_project_by_id(
        project_id
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project


@app.get("/history/{run_id}/policies")
def run_policy_detail(run_id: int):
    """Per-policy breakdown for a single run (used by history detail expand)."""
    return get_run_policy_results(run_id)


@app.get("/history")
def moderation_history(
    limit:  int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0,   ge=0)
):
    """
    Return all past moderation runs, newest first.
    Optional: ?limit=50&offset=0
    """
    return get_moderation_history(limit=limit, offset=offset)


@app.post("/moderate/{project_id}")
def trigger_moderation(
    project_id: int,
    policy_code: Optional[str] = Query(
        default=None
    )
):
    """
    Trigger moderation.

    Examples:
    /moderate/5
    /moderate/5?policy_code=TYPE-PROJECT-01
    """

    return run_moderation(
        project_id,
        policy_code=policy_code
    )
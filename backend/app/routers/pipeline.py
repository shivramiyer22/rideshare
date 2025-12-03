"""
Pipeline API Router - Endpoints for managing the agent pipeline.

This router provides endpoints for:
- Manual pipeline triggering
- Pipeline status checking
- Pipeline history retrieval

The pipeline runs Forecasting + Analysis agents in parallel, followed by
Recommendations and What-If analysis sequentially.

IMPORTANT: These endpoints do NOT affect chatbot functionality.
The chatbot continues to work independently while pipeline runs in background.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.pipeline_orchestrator import (
    run_agent_pipeline,
    get_pipeline_status,
    get_pipeline_history,
    agent_pipeline
)
from app.agents.data_ingestion import change_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PipelineTriggerRequest(BaseModel):
    """Request model for manual pipeline trigger."""
    force: bool = Field(
        default=False,
        description="Force pipeline run even if no changes detected"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for manual trigger (for logging)"
    )


class PipelineTriggerResponse(BaseModel):
    """Response model for pipeline trigger."""
    success: bool
    message: str
    run_id: Optional[str] = None
    status: Optional[str] = None
    queued: bool = False


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status."""
    is_running: bool
    current_run_id: Optional[str]
    current_status: str
    change_tracker: Dict[str, Any]


class PipelineHistoryItem(BaseModel):
    """Model for a single pipeline history item."""
    run_id: str
    trigger_source: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    change_count: Optional[int] = 0
    duration_seconds: Optional[float] = None


class PipelineHistoryResponse(BaseModel):
    """Response model for pipeline history."""
    total: int
    runs: List[Dict[str, Any]]


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/trigger", response_model=PipelineTriggerResponse)
async def trigger_pipeline(
    request: PipelineTriggerRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger the agent pipeline.
    
    This endpoint starts the pipeline execution:
    1. Forecasting Agent (generates 30/60/90 day forecasts)
    2. Analysis Agent (competitor analysis, external data, pricing rules)
       (runs in parallel with Forecasting)
    3. Recommendation Agent (generates strategic recommendations)
    4. What-If Analysis (calculates KPI impact)
    
    The pipeline runs in the background and doesn't block this request.
    Use GET /status to check progress.
    
    Args:
        request: Pipeline trigger parameters
            - force: Run even if no changes detected
            - reason: Optional reason for manual trigger
    
    Returns:
        PipelineTriggerResponse with run_id and status
    """
    logger.info(f"Manual pipeline trigger requested. Force: {request.force}, Reason: {request.reason}")
    
    # Check if pipeline is already running
    if agent_pipeline.is_running():
        return PipelineTriggerResponse(
            success=False,
            message="Pipeline is already running",
            run_id=agent_pipeline.current_run_id,
            status="running",
            queued=False
        )
    
    # Check if there are changes to process (unless forced)
    if not request.force and not change_tracker.has_pending_changes():
        return PipelineTriggerResponse(
            success=False,
            message="No changes detected since last pipeline run. Use force=true to run anyway.",
            run_id=None,
            status="no_changes",
            queued=False
        )
    
    # Get changes summary
    changes_summary = change_tracker.get_and_clear_changes() if change_tracker.has_pending_changes() else {
        "changes": [],
        "collections_changed": [],
        "change_count": 0,
        "manual_trigger": True,
        "reason": request.reason
    }
    
    # Add manual trigger info
    changes_summary["manual_trigger"] = True
    if request.reason:
        changes_summary["trigger_reason"] = request.reason
    
    # Generate run ID before starting
    run_id = agent_pipeline.generate_run_id()
    
    # Start pipeline in background
    async def run_pipeline_background():
        try:
            await run_agent_pipeline(
                trigger_source="manual_api",
                changes_summary=changes_summary
            )
        except Exception as e:
            logger.error(f"Background pipeline run failed: {e}")
    
    background_tasks.add_task(run_pipeline_background)
    
    return PipelineTriggerResponse(
        success=True,
        message="Pipeline started successfully",
        run_id=run_id,
        status="started",
        queued=True
    )


@router.get("/status", response_model=PipelineStatusResponse)
async def get_status():
    """
    Get current pipeline status.
    
    Returns:
    - is_running: Whether a pipeline is currently executing
    - current_run_id: ID of the current/last run
    - current_status: Status of current/last run
    - change_tracker: Current state of change tracking
    """
    status = get_pipeline_status()
    tracker_status = change_tracker.get_status()
    
    return PipelineStatusResponse(
        is_running=status["is_running"],
        current_run_id=status["current_run_id"],
        current_status=status["current_status"],
        change_tracker=tracker_status
    )


@router.get("/history", response_model=PipelineHistoryResponse)
async def get_history(limit: int = 10):
    """
    Get pipeline run history.
    
    Args:
        limit: Maximum number of runs to return (default: 10)
    
    Returns:
        List of recent pipeline runs with details
    """
    runs = await get_pipeline_history(limit=limit)
    
    # Calculate duration for completed runs
    for run in runs:
        if run.get("started_at") and run.get("completed_at"):
            try:
                started = run["started_at"]
                completed = run["completed_at"]
                if isinstance(started, datetime) and isinstance(completed, datetime):
                    run["duration_seconds"] = (completed - started).total_seconds()
            except:
                pass
        
        # Add change count
        changes = run.get("changes_processed", {})
        run["change_count"] = changes.get("change_count", 0) if isinstance(changes, dict) else 0
    
    return PipelineHistoryResponse(
        total=len(runs),
        runs=runs
    )


@router.get("/changes")
async def get_pending_changes():
    """
    Get details of pending changes waiting for next pipeline run.
    
    This endpoint shows what MongoDB changes have been recorded
    since the last pipeline run. The hourly scheduler will process
    these changes, or you can manually trigger with POST /trigger.
    
    Returns:
        Dict with pending changes summary
    """
    return change_tracker.get_status()


@router.post("/clear-changes")
async def clear_pending_changes():
    """
    Clear pending changes without running the pipeline.
    
    Use this if you want to reset the change tracker without
    triggering a pipeline run. The next pipeline run will only
    process changes that occur after this reset.
    
    Returns:
        Summary of cleared changes
    """
    cleared = change_tracker.get_and_clear_changes()
    return {
        "message": "Pending changes cleared",
        "cleared": cleared
    }


@router.get("/last-run")
async def get_last_run():
    """
    Get details of the last pipeline run.
    
    Returns comprehensive information about the most recent
    pipeline execution including all phase results.
    """
    runs = await get_pipeline_history(limit=1)
    
    if not runs:
        return {
            "message": "No pipeline runs found",
            "last_run": None
        }
    
    return {
        "message": "Last pipeline run",
        "last_run": runs[0]
    }


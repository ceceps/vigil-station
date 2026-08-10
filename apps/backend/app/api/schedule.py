"""
Schedule API router.
Handles endpoints for approving or overriding scheduling recommendations.
"""
from fastapi import APIRouter, HTTPException, Path
import structlog
from datetime import datetime

from app.schemas.schemas import ScheduleApprovalRequest, ScheduleApprovalResponse
from app.core.cache import tle_cache

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("/{schedule_id}/approve", response_model=ScheduleApprovalResponse)
async def approve_schedule(
    schedule_id: str = Path(..., description="ID of the schedule/pass to approve"),
    request: ScheduleApprovalRequest = None
):
    """
    Approve or override a scheduling recommendation.
    
    This endpoint allows operators to make the final decision on whether to
    accept an AI recommendation or override it with their own judgment.
    
    Path Parameters:
        - schedule_id: ID of the pass/schedule to approve
    
    Request Body:
        - approved: Boolean indicating approval (true) or override (false)
        - override_reason: Optional reason for override (required if approved=false)
    
    Returns:
        Status of the approval and the schedule ID
    """
    try:
        logger.info(
            "Processing schedule approval",
            schedule_id=schedule_id,
            approved=request.approved
        )
        
        # Validate override reason if not approved
        if not request.approved and not request.override_reason:
            raise HTTPException(
                status_code=400,
                detail="override_reason is required when approved=false"
            )
        
        # Store the approval decision in the database
        schedule_data = {
            'id': schedule_id,
            'satellite_id': 0,  # Will be populated from pass data in production
            'ground_station_id': 0,
            'start_time': datetime.utcnow(),
            'end_time': datetime.utcnow(),
            'max_elevation_deg': 0.0,
            'status': 'approved' if request.approved else 'rejected',
            'approved': request.approved,
            'override_reason': request.override_reason
        }
        
        tle_cache.store_schedule(schedule_data)
        
        status = 'approved' if request.approved else 'rejected'
        
        logger.info(
            "Schedule approval processed",
            schedule_id=schedule_id,
            status=status
        )
        
        return ScheduleApprovalResponse(
            status=status,
            schedule_id=schedule_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to process schedule approval",
            schedule_id=schedule_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process approval: {str(e)}"
        )


@router.get("/{schedule_id}/status")
async def get_schedule_status(
    schedule_id: str = Path(..., description="ID of the schedule to check")
):
    """
    Get the approval status of a schedule.
    
    Path Parameters:
        - schedule_id: ID of the schedule to check
    
    Returns:
        Current status and approval information
    """
    try:
        schedule = tle_cache.get_schedule(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Schedule {schedule_id} not found"
            )
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get schedule status",
            schedule_id=schedule_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )
"""
Analytics API router.
Provides endpoints for AI-driven operational analysis based on historical database records.
"""
from fastapi import APIRouter, HTTPException
import structlog
from typing import Dict, Any, List

from app.core.cache import tle_cache
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/insights")
async def get_operational_insights() -> Dict[str, Any]:
    """
    Get AI-driven operational insights synthesized from database history.
    Analyses conflict frequency, recommendation acceptance rates, and operator patterns.
    """
    try:
        conflicts = tle_cache.get_conflicts_from_db()
        recommendations = tle_cache.get_all_recommendations()
        schedules = tle_cache.get_all_schedules()

        total_conflicts = len(conflicts)
        total_recommendations = len(recommendations)
        total_decisions = len(schedules)

        approved_count = sum(1 for s in schedules if s.get('approved') is True)
        overridden_count = sum(1 for s in schedules if s.get('approved') is False)
        
        approval_rate = round((approved_count / total_decisions * 100), 1) if total_decisions > 0 else 100.0

        # Count conflicts by ground station
        station_conflict_counts: Dict[int, int] = {}
        for c in conflicts:
            gs_id = c['ground_station_id']
            station_conflict_counts[gs_id] = station_conflict_counts.get(gs_id, 0) + 1

        most_conflicted_gs_id = max(station_conflict_counts, key=station_conflict_counts.get) if station_conflict_counts else None
        
        station_name = "N/A"
        if most_conflicted_gs_id:
            gs_obj = next((g for g in settings.ground_stations if g['id'] == most_conflicted_gs_id), None)
            if gs_obj:
                station_name = gs_obj['name']

        # Extract override reasons for learning synthesis
        override_reasons = [s['override_reason'] for s in schedules if s.get('override_reason')]

        # Synthesize executive summary reasoning
        ai_summary = (
            f"Based on historical database records, {total_conflicts} conflicts have been logged. "
            f"Operators have made {total_decisions} decisions with a {approval_rate}% AI recommendation approval rate. "
        )
        if station_name != "N/A":
            ai_summary += f"Ground station '{station_name}' shows the highest contention frequency. "
        
        if override_reasons:
            ai_summary += f"Recent operator overrides cite reasons such as: '{override_reasons[0]}'."
        else:
            ai_summary += "AI recommendations align well with mission priorities and constraints."

        return {
            "summary": {
                "total_conflicts": total_conflicts,
                "total_recommendations": total_recommendations,
                "total_decisions": total_decisions,
                "approved_count": approved_count,
                "overridden_count": overridden_count,
                "approval_rate_percent": approval_rate,
                "busiest_ground_station": station_name
            },
            "insights_reasoning": ai_summary,
            "recent_overrides": override_reasons[:5],
            "conflicts_history": conflicts[:10],
            "recommendations_history": recommendations[:20],
            "schedules_history": schedules[:20]
        }
    except Exception as e:
        logger.error("Failed to generate analytics insights", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics insights: {str(e)}"
        )

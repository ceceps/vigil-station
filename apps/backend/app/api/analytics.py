"""
Analytics API router.
Provides endpoints for AI-driven operational analysis based on historical database records.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
import structlog

from app.core.cache import tle_cache
from app.core.config import settings
from app.services.llm_reasoner import llm_reasoner

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/insights")
async def get_operational_insights(
    start: Optional[str] = Query(None, description="Start date in ISO format or YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date in ISO format or YYYY-MM-DD")
) -> Dict[str, Any]:
    """
    Get AI-driven operational insights synthesized from database history for a given time range.
    Analyses conflict frequency, recommendation acceptance rates, and operator patterns.
    """
    try:
        start_dt = None
        end_dt = None
        time_label = "all-time database history"

        if start:
            start_str = start if 'T' in start else f"{start}T00:00:00+00:00"
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        if end:
            end_str = end if 'T' in end else f"{end}T23:59:59+00:00"
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))

        if start and end:
            time_label = f"{start} to {end}"
        elif start:
            time_label = f"from {start}"
        elif end:
            time_label = f"until {end}"

        conflicts = tle_cache.get_conflicts_from_db(start_time=start_dt, end_time=end_dt)
        recommendations = tle_cache.get_all_recommendations(start_time=start_dt, end_time=end_dt)
        schedules = tle_cache.get_all_schedules(start_time=start_dt, end_time=end_dt)

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

        # Determine overall database data dates (spanning all records)
        all_conflicts = tle_cache.get_conflicts_from_db()
        data_dates = []
        for c in all_conflicts:
            if c.get('overlap_start'):
                data_dates.append(c['overlap_start'][:10])
            if c.get('created_at'):
                data_dates.append(c['created_at'][:10])
        
        data_start_date = min(data_dates) if data_dates else datetime.utcnow().strftime("%Y-%m-%d")
        data_end_date = max(data_dates) if data_dates else datetime.utcnow().strftime("%Y-%m-%d")

        summary_data = {
            "total_conflicts": total_conflicts,
            "total_recommendations": total_recommendations,
            "total_decisions": total_decisions,
            "approved_count": approved_count,
            "overridden_count": overridden_count,
            "approval_rate_percent": approval_rate,
            "busiest_ground_station": station_name,
            "data_start_date": data_start_date,
            "data_end_date": data_end_date
        }

        # Generate AI Analyst Report with Claude
        ai_analyst_report = await llm_reasoner.generate_analytics_report(
            summary=summary_data,
            recent_overrides=override_reasons,
            time_range_label=time_label
        )

        return {
            "summary": summary_data,
            "insights_reasoning": ai_analyst_report,
            "recent_overrides": override_reasons[:5],
            "conflicts_history": conflicts[:10],
            "recommendations_history": recommendations[:20],
            "schedules_history": schedules[:20],
            "timeframe_label": time_label,
            "data_start_date": data_start_date,
            "data_end_date": data_end_date,
            "active_start_date": start or data_start_date,
            "active_end_date": end or data_end_date
        }
    except Exception as e:
        logger.error("Failed to generate analytics insights", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics insights: {str(e)}"
        )

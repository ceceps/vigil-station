"""
TLE cache management using PostgreSQL with SQLAlchemy.
Stores TLE data locally to avoid hitting Space-Track.org rate limits.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import SessionLocal, TLECache, Schedule, Conflict, Recommendation

logger = structlog.get_logger(__name__)


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    # Already has timezone
    return dt.astimezone(timezone.utc)


class TLECacheManager:
    """Manages TLE data caching in PostgreSQL."""
    
    def __init__(self):
        """Initialize the TLE cache manager."""
        logger.info("TLE Cache Manager initialized with PostgreSQL")
    
    def _get_db(self) -> Session:
        """Get a database session."""
        return SessionLocal()
    
    def is_cache_valid(self, satellite_group: str) -> bool:
        """Check if cached TLE data is still valid based on age."""
        db = self._get_db()
        try:
            # Get the oldest fetch time for the satellite group
            oldest_tle = db.query(TLECache).filter(
                TLECache.satellite_group == satellite_group
            ).order_by(TLECache.fetched_at.asc()).first()
            
            if not oldest_tle:
                return False
            
            # Ensure both datetimes are timezone-aware for comparison
            fetched_at = ensure_utc(oldest_tle.fetched_at)
            cache_expiry = utc_now() - timedelta(hours=settings.tle_cache_hours)
            is_valid = fetched_at > cache_expiry
            
            logger.info(
                "Cache validity check",
                satellite_group=satellite_group,
                is_valid=is_valid,
                oldest_fetch=fetched_at.isoformat()
            )
            return is_valid
        finally:
            db.close()
    
    def store_tles(self, tles: List[Dict[str, Any]], satellite_group: str) -> int:
        """Store TLE data in the cache."""
        db = self._get_db()
        try:
            fetched_at = utc_now()
            stored_count = 0
            
            for tle in tles:
                try:
                    # Check if TLE already exists
                    existing = db.query(TLECache).filter(
                        TLECache.norad_id == tle['norad_id']
                    ).first()
                    
                    if existing:
                        # Update existing TLE
                        existing.name = tle['name']
                        existing.tle_line1 = tle['tle_line1']
                        existing.tle_line2 = tle['tle_line2']
                        existing.satellite_group = satellite_group
                        existing.fetched_at = fetched_at
                        existing.extra_data = json.dumps(tle.get('metadata', {}))
                    else:
                        # Create new TLE
                        new_tle = TLECache(
                            norad_id=tle['norad_id'],
                            name=tle['name'],
                            tle_line1=tle['tle_line1'],
                            tle_line2=tle['tle_line2'],
                            satellite_group=satellite_group,
                            fetched_at=fetched_at,
                            extra_data=json.dumps(tle.get('metadata', {}))
                        )
                        db.add(new_tle)
                    
                    stored_count += 1
                except Exception as e:
                    logger.error(
                        "Failed to store TLE",
                        norad_id=tle.get('norad_id'),
                        error=str(e)
                    )
            
            db.commit()
            
            logger.info(
                "TLEs stored in cache",
                satellite_group=satellite_group,
                count=stored_count
            )
            return stored_count
        except Exception as e:
            db.rollback()
            logger.error("Failed to store TLEs", error=str(e))
            raise
        finally:
            db.close()
    
    def get_tles(self, satellite_group: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve TLE data from the cache."""
        db = self._get_db()
        try:
            query = db.query(TLECache).filter(
                TLECache.satellite_group == satellite_group
            ).order_by(TLECache.name)
            
            if limit:
                query = query.limit(limit)
            
            tles_orm = query.all()
            
            tles = []
            for tle_orm in tles_orm:
                fetched_at = ensure_utc(tle_orm.fetched_at)
                tles.append({
                    'norad_id': tle_orm.norad_id,
                    'name': tle_orm.name,
                    'tle_line1': tle_orm.tle_line1,
                    'tle_line2': tle_orm.tle_line2,
                    'satellite_group': tle_orm.satellite_group,
                    'fetched_at': fetched_at.isoformat(),
                    'metadata': json.loads(tle_orm.extra_data) if tle_orm.extra_data else {}
                })
            
            logger.info(
                "TLEs retrieved from cache",
                satellite_group=satellite_group,
                count=len(tles)
            )
            return tles
        finally:
            db.close()
    
    def get_tle_by_norad_id(self, norad_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single TLE by NORAD ID."""
        db = self._get_db()
        try:
            tle_orm = db.query(TLECache).filter(
                TLECache.norad_id == norad_id
            ).first()
            
            if not tle_orm:
                return None
            
            fetched_at = ensure_utc(tle_orm.fetched_at)
            return {
                'norad_id': tle_orm.norad_id,
                'name': tle_orm.name,
                'tle_line1': tle_orm.tle_line1,
                'tle_line2': tle_orm.tle_line2,
                'satellite_group': tle_orm.satellite_group,
                'fetched_at': fetched_at.isoformat(),
                'metadata': json.loads(tle_orm.extra_data) if tle_orm.extra_data else {}
            }
        finally:
            db.close()
    
    def clear_cache(self, satellite_group: Optional[str] = None) -> None:
        """Clear TLE cache, optionally for a specific satellite group."""
        db = self._get_db()
        try:
            if satellite_group:
                db.query(TLECache).filter(
                    TLECache.satellite_group == satellite_group
                ).delete()
                logger.info("Cache cleared for group", satellite_group=satellite_group)
            else:
                db.query(TLECache).delete()
                logger.info("All cache cleared")
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Failed to clear cache", error=str(e))
            raise
        finally:
            db.close()
    
    def store_schedule(self, schedule_data: Dict[str, Any]) -> None:
        """Store a schedule approval/override."""
        db = self._get_db()
        try:
            # Ensure datetime fields are timezone-aware
            if 'start_time' in schedule_data:
                if isinstance(schedule_data['start_time'], str):
                    schedule_data['start_time'] = datetime.fromisoformat(schedule_data['start_time'].replace('Z', '+00:00'))
                schedule_data['start_time'] = ensure_utc(schedule_data['start_time'])
                
            if 'end_time' in schedule_data:
                if isinstance(schedule_data['end_time'], str):
                    schedule_data['end_time'] = datetime.fromisoformat(schedule_data['end_time'].replace('Z', '+00:00'))
                schedule_data['end_time'] = ensure_utc(schedule_data['end_time'])
            
            existing = db.query(Schedule).filter(
                Schedule.id == schedule_data['id']
            ).first()
            
            if existing:
                # Update existing schedule
                for key, value in schedule_data.items():
                    setattr(existing, key, value)
                existing.updated_at = utc_now()
            else:
                # Create new schedule
                new_schedule = Schedule(**schedule_data)
                db.add(new_schedule)
            
            db.commit()
            logger.info("Schedule stored", schedule_id=schedule_data['id'])
        except Exception as e:
            db.rollback()
            logger.error("Failed to store schedule", error=str(e))
            raise
        finally:
            db.close()
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a schedule by ID."""
        db = self._get_db()
        try:
            schedule = db.query(Schedule).filter(
                Schedule.id == schedule_id
            ).first()
            
            if not schedule:
                return None
            
            return {
                'id': schedule.id,
                'satellite_id': schedule.satellite_id,
                'ground_station_id': schedule.ground_station_id,
                'start_time': ensure_utc(schedule.start_time).isoformat(),
                'end_time': ensure_utc(schedule.end_time).isoformat(),
                'max_elevation_deg': schedule.max_elevation_deg,
                'status': schedule.status,
                'approved': schedule.approved,
                'override_reason': schedule.override_reason,
                'created_at': ensure_utc(schedule.created_at).isoformat(),
                'updated_at': ensure_utc(schedule.updated_at).isoformat()
            }
        finally:
            db.close()

    def store_conflicts(self, conflicts: List[Dict[str, Any]]) -> None:
        """Store detected conflicts in PostgreSQL database."""
        db = self._get_db()
        try:
            for c in conflicts:
                overlap_start = c['overlap_start']
                if isinstance(overlap_start, str):
                    overlap_start = datetime.fromisoformat(overlap_start.replace('Z', '+00:00'))
                overlap_start = ensure_utc(overlap_start)

                overlap_end = c['overlap_end']
                if isinstance(overlap_end, str):
                    overlap_end = datetime.fromisoformat(overlap_end.replace('Z', '+00:00'))
                overlap_end = ensure_utc(overlap_end)

                pass_ids_str = json.dumps(c['pass_ids']) if isinstance(c['pass_ids'], list) else str(c['pass_ids'])

                existing = db.query(Conflict).filter(Conflict.id == c['id']).first()
                if not existing:
                    new_conflict = Conflict(
                        id=c['id'],
                        ground_station_id=c['ground_station_id'],
                        pass_ids=pass_ids_str,
                        overlap_start=overlap_start,
                        overlap_end=overlap_end,
                        resolved=c.get('resolved', False)
                    )
                    db.add(new_conflict)
            db.commit()
            logger.info("Stored conflicts in database", count=len(conflicts))
        except Exception as e:
            db.rollback()
            logger.error("Failed to store conflicts in DB", error=str(e))
        finally:
            db.close()

    def get_conflicts_from_db(
        self,
        ground_station_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored conflicts from database with optional time range filter."""
        db = self._get_db()
        try:
            query = db.query(Conflict)
            if ground_station_id:
                query = query.filter(Conflict.ground_station_id == ground_station_id)
            if start_time:
                query = query.filter((Conflict.created_at >= start_time) | (Conflict.overlap_start >= start_time))
            if end_time:
                query = query.filter((Conflict.created_at <= end_time) | (Conflict.overlap_start <= end_time))
            conflicts_orm = query.order_by(Conflict.overlap_start.desc(), Conflict.created_at.desc()).all()

            results = []
            for c in conflicts_orm:
                pass_ids = json.loads(c.pass_ids) if c.pass_ids.startswith('[') else [c.pass_ids]
                results.append({
                    'id': c.id,
                    'ground_station_id': c.ground_station_id,
                    'pass_ids': pass_ids,
                    'overlap_start': ensure_utc(c.overlap_start).isoformat(),
                    'overlap_end': ensure_utc(c.overlap_end).isoformat(),
                    'resolved': c.resolved,
                    'created_at': ensure_utc(c.created_at).isoformat()
                })
            return results
        finally:
            db.close()

    def store_recommendation(self, recommendation_data: Dict[str, Any]) -> None:
        """Store AI-generated recommendation in PostgreSQL database."""
        db = self._get_db()
        try:
            rec_id = f"rec_{recommendation_data['conflict_id']}"
            alt_window = recommendation_data.get('alternative_window')
            alt_window_str = json.dumps(alt_window) if alt_window else None

            existing = db.query(Recommendation).filter(
                Recommendation.conflict_id == recommendation_data['conflict_id']
            ).first()

            if existing:
                existing.suggested_action = recommendation_data.get('suggested_action', 'reschedule')
                existing.target_pass_id = recommendation_data.get('target_pass_id')
                existing.alternative_window = alt_window_str
                existing.reasoning = recommendation_data.get('reasoning', '')
            else:
                new_rec = Recommendation(
                    id=rec_id,
                    conflict_id=recommendation_data['conflict_id'],
                    suggested_action=recommendation_data.get('suggested_action', 'reschedule'),
                    target_pass_id=recommendation_data.get('target_pass_id'),
                    alternative_window=alt_window_str,
                    reasoning=recommendation_data.get('reasoning', '')
                )
                db.add(new_rec)
            db.commit()
            logger.info("Recommendation stored in database", conflict_id=recommendation_data['conflict_id'])
        except Exception as e:
            db.rollback()
            logger.error("Failed to store recommendation in DB", error=str(e))
        finally:
            db.close()

    def get_recommendation_by_conflict_id(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve recommendation for a specific conflict from database."""
        db = self._get_db()
        try:
            rec = db.query(Recommendation).filter(
                Recommendation.conflict_id == conflict_id
            ).first()
            if not rec:
                return None
            alt_window = json.loads(rec.alternative_window) if rec.alternative_window else None
            return {
                'id': rec.id,
                'conflict_id': rec.conflict_id,
                'suggested_action': rec.suggested_action,
                'target_pass_id': rec.target_pass_id,
                'alternative_window': alt_window,
                'reasoning': rec.reasoning,
                'created_at': ensure_utc(rec.created_at).isoformat()
            }
        finally:
            db.close()

    def get_all_recommendations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored recommendations from database with optional time range filter."""
        db = self._get_db()
        try:
            query = db.query(Recommendation)
            if start_time:
                query = query.filter(Recommendation.created_at >= start_time)
            if end_time:
                query = query.filter(Recommendation.created_at <= end_time)
            recs = query.order_by(Recommendation.created_at.desc()).all()
            results = []
            for rec in recs:
                alt_window = json.loads(rec.alternative_window) if rec.alternative_window else None
                results.append({
                    'id': rec.id,
                    'conflict_id': rec.conflict_id,
                    'suggested_action': rec.suggested_action,
                    'target_pass_id': rec.target_pass_id,
                    'alternative_window': alt_window,
                    'reasoning': rec.reasoning,
                    'created_at': ensure_utc(rec.created_at).isoformat()
                })
            return results
        finally:
            db.close()

    def get_all_schedules(
        self,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored schedules from database with optional time range filter."""
        db = self._get_db()
        try:
            query = db.query(Schedule)
            if start_time:
                query = query.filter(Schedule.updated_at >= start_time)
            if end_time:
                query = query.filter(Schedule.updated_at <= end_time)
            query = query.order_by(Schedule.updated_at.desc())
            if limit:
                query = query.limit(limit)
            schedules_orm = query.all()
            
            results = []
            for s in schedules_orm:
                results.append({
                    'id': s.id,
                    'satellite_id': s.satellite_id,
                    'ground_station_id': s.ground_station_id,
                    'start_time': ensure_utc(s.start_time).isoformat(),
                    'end_time': ensure_utc(s.end_time).isoformat(),
                    'max_elevation_deg': s.max_elevation_deg,
                    'status': s.status,
                    'approved': s.approved,
                    'override_reason': s.override_reason,
                    'created_at': ensure_utc(s.created_at).isoformat(),
                    'updated_at': ensure_utc(s.updated_at).isoformat()
                })
            return results
        finally:
            db.close()


# Global cache instance
tle_cache = TLECacheManager()

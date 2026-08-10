"""
Schedule conflict detection service.
Identifies overlapping pass windows at the same ground station.
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger(__name__)


def parse_datetime(dt) -> datetime:
    """Parse datetime from various formats to timezone-aware datetime."""
    if isinstance(dt, datetime):
        # Already a datetime, ensure it's timezone-aware
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    elif isinstance(dt, str):
        # Parse ISO string, handle both Z and +00:00 formats
        dt_str = dt.replace('Z', '+00:00')
        return datetime.fromisoformat(dt_str)
    else:
        raise ValueError(f"Cannot parse datetime from type {type(dt)}")


class ConflictDetector:
    """Service for detecting scheduling conflicts between satellite passes."""
    
    def detect_conflicts(
        self,
        passes: List[Dict[str, Any]],
        ground_station_id: int
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts (overlapping passes) at a single ground station.
        
        Args:
            passes: List of pass dictionaries with start_time, end_time, id
            ground_station_id: ID of the ground station to check
        
        Returns:
            List of conflict dictionaries with overlapping pass information
        """
        conflicts = []
        
        # Sort passes by start time
        sorted_passes = sorted(passes, key=lambda p: parse_datetime(p['start_time']))
        
        # Check each pair of passes for overlap
        for i in range(len(sorted_passes)):
            for j in range(i + 1, len(sorted_passes)):
                pass1 = sorted_passes[i]
                pass2 = sorted_passes[j]
                
                # Check if passes overlap
                overlap = self._check_overlap(pass1, pass2)
                
                if overlap:
                    overlap_start, overlap_end = overlap
                    
                    # Create conflict record
                    conflict_id = self._generate_conflict_id(
                        pass1['id'],
                        pass2['id']
                    )
                    
                    conflict = {
                        'id': conflict_id,
                        'ground_station_id': ground_station_id,
                        'pass_ids': [pass1['id'], pass2['id']],
                        'overlap_start': overlap_start.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                        'overlap_end': overlap_end.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                        'passes': [pass1, pass2]  # Include full pass data for reasoning
                    }
                    
                    conflicts.append(conflict)
                    
                    logger.info(
                        "Conflict detected",
                        conflict_id=conflict_id,
                        ground_station_id=ground_station_id,
                        pass1_id=pass1['id'],
                        pass2_id=pass2['id']
                    )
        
        return conflicts
    
    def detect_conflicts_all_stations(
        self,
        passes_by_station: Dict[int, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts across all ground stations.
        
        Args:
            passes_by_station: Dictionary mapping ground_station_id to list of passes
        
        Returns:
            Combined list of all conflicts
        """
        all_conflicts = []
        
        for ground_station_id, passes in passes_by_station.items():
            conflicts = self.detect_conflicts(passes, ground_station_id)
            all_conflicts.extend(conflicts)
        
        logger.info(
            "Conflict detection complete",
            total_conflicts=len(all_conflicts),
            stations_checked=len(passes_by_station)
        )
        
        return all_conflicts
    
    def _check_overlap(
        self,
        pass1: Dict[str, Any],
        pass2: Dict[str, Any]
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Check if two passes overlap in time.
        
        Args:
            pass1: First pass dictionary
            pass2: Second pass dictionary
        
        Returns:
            Tuple of (overlap_start, overlap_end) if overlap exists, None otherwise
        """
        try:
            start1 = parse_datetime(pass1['start_time'])
            end1 = parse_datetime(pass1['end_time'])
            start2 = parse_datetime(pass2['start_time'])
            end2 = parse_datetime(pass2['end_time'])
            
            # Check for overlap
            # Overlap exists if: start1 < end2 AND start2 < end1
            if start1 < end2 and start2 < end1:
                # Calculate overlap period
                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                return (overlap_start, overlap_end)
            
            return None
        except Exception as e:
            logger.error(
                "Failed to check overlap",
                pass1_id=pass1.get('id'),
                pass2_id=pass2.get('id'),
                error=str(e)
            )
            return None
    
    def _generate_conflict_id(self, pass1_id: str, pass2_id: str) -> str:
        """Generate a unique conflict ID from two pass IDs."""
        # Sort pass IDs to ensure consistent conflict ID regardless of order
        ids = sorted([pass1_id, pass2_id])
        return f"conflict_{ids[0]}_{ids[1]}"
    
    def get_conflict_severity(self, conflict: Dict[str, Any]) -> str:
        """
        Determine the severity of a conflict based on overlap duration.
        
        Args:
            conflict: Conflict dictionary
        
        Returns:
            Severity level: 'low', 'medium', 'high'
        """
        overlap_start = parse_datetime(conflict['overlap_start'])
        overlap_end = parse_datetime(conflict['overlap_end'])
        
        overlap_duration_minutes = (overlap_end - overlap_start).total_seconds() / 60
        
        if overlap_duration_minutes < 2:
            return 'low'
        elif overlap_duration_minutes < 5:
            return 'medium'
        else:
            return 'high'
    
    def find_alternative_windows(
        self,
        target_pass: Dict[str, Any],
        all_passes: List[Dict[str, Any]],
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Find alternative time windows for a conflicting pass.
        
        Args:
            target_pass: The pass to reschedule
            all_passes: All passes for the same satellite at the same ground station
            time_window_hours: How far ahead to look for alternatives
        
        Returns:
            List of alternative pass windows that don't conflict
        """
        alternatives = []
        
        try:
            target_start = parse_datetime(target_pass['start_time'])
            
            # Filter passes for the same satellite and ground station
            same_satellite_passes = [
                p for p in all_passes
                if p['satellite_id'] == target_pass['satellite_id']
                and p['ground_station_id'] == target_pass['ground_station_id']
                and p['id'] != target_pass['id']
            ]
            
            # Find passes that don't conflict with any other passes
            for candidate in same_satellite_passes:
                candidate_start = parse_datetime(candidate['start_time'])
                
                # Check if within time window
                time_diff_hours = abs((candidate_start - target_start).total_seconds() / 3600)
                if time_diff_hours > time_window_hours:
                    continue
                
                # Check if this candidate conflicts with any other passes
                has_conflict = False
                for other_pass in all_passes:
                    if other_pass['id'] == candidate['id']:
                        continue
                    if other_pass['satellite_id'] == candidate['satellite_id']:
                        continue  # Same satellite, can't conflict with itself
                    
                    if self._check_overlap(candidate, other_pass):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    alternatives.append(candidate)
            
            # Sort by proximity to original time
            alternatives.sort(
                key=lambda p: abs(
                    (parse_datetime(p['start_time']) - target_start).total_seconds()
                )
            )
            
            return alternatives
            
        except Exception as e:
            logger.error(
                "Failed to find alternative windows",
                target_pass_id=target_pass.get('id'),
                error=str(e)
            )
            return []


# Global detector instance
conflict_detector = ConflictDetector()
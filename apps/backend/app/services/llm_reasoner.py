"""
LLM-based reasoning service using Anthropic Claude.
Generates natural language recommendations for conflict resolution.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from anthropic import Anthropic

from app.core.config import settings

logger = structlog.get_logger(__name__)


class LLMReasoner:
    """Service for generating AI-powered scheduling recommendations."""
    
    def __init__(self):
        """Initialize the Anthropic Claude client."""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"
        logger.info("LLM Reasoner initialized with Claude")
    
    async def generate_recommendation(
        self,
        conflict: Dict[str, Any],
        alternative_passes: List[Dict[str, Any]],
        weather_data: Optional[Dict[str, Any]] = None,
        space_weather_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a conflict resolution recommendation using Claude.
        
        Args:
            conflict: Conflict dictionary with pass details
            alternative_passes: List of alternative pass windows
            weather_data: Optional weather data for the passes
            space_weather_data: Optional space weather data for the passes
        
        Returns:
            Recommendation dictionary with suggested_action, target_pass_id, 
            alternative_window, and reasoning
        """
        try:
            # Build the prompt with all relevant data
            prompt = self._build_recommendation_prompt(
                conflict,
                alternative_passes,
                weather_data,
                space_weather_data
            )
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            response_text = message.content[0].text
            recommendation = self._parse_recommendation_response(
                response_text,
                conflict,
                alternative_passes
            )
            
            logger.info(
                "Recommendation generated",
                conflict_id=conflict['id'],
                suggested_action=recommendation['suggested_action']
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(
                "Failed to generate recommendation",
                conflict_id=conflict.get('id'),
                error=str(e)
            )
            # Return a fallback recommendation
            return self._generate_fallback_recommendation(conflict, alternative_passes)
    
    def _build_recommendation_prompt(
        self,
        conflict: Dict[str, Any],
        alternative_passes: List[Dict[str, Any]],
        weather_data: Optional[Dict[str, Any]] = None,
        space_weather_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for Claude with all relevant context."""
        
        # Extract conflict details
        passes = conflict.get('passes', [])
        pass1 = passes[0] if len(passes) > 0 else {}
        pass2 = passes[1] if len(passes) > 1 else {}
        
        overlap_start = conflict.get('overlap_start', '')
        overlap_end = conflict.get('overlap_end', '')
        
        # Format pass details
        pass1_details = f"""
Pass 1:
- Satellite ID: {pass1.get('satellite_id')}
- Start: {pass1.get('start_time')}
- End: {pass1.get('end_time')}
- Max Elevation: {pass1.get('max_elevation_deg', 0):.1f}°
"""
        
        pass2_details = f"""
Pass 2:
- Satellite ID: {pass2.get('satellite_id')}
- Start: {pass2.get('start_time')}
- End: {pass2.get('end_time')}
- Max Elevation: {pass2.get('max_elevation_deg', 0):.1f}°
"""
        
        # Format alternative passes
        alternatives_text = ""
        if alternative_passes:
            alternatives_text = "\n\nAlternative Pass Windows Available:\n"
            for i, alt in enumerate(alternative_passes[:3], 1):  # Limit to top 3
                alternatives_text += f"""
Alternative {i}:
- Start: {alt.get('start_time')}
- End: {alt.get('end_time')}
- Max Elevation: {alt.get('max_elevation_deg', 0):.1f}°
"""
        
        # Add weather context if available
        weather_text = ""
        if weather_data:
            weather_text = f"""

Weather Conditions:
- Cloud Cover: {weather_data.get('cloud_cover_percent', 'N/A')}%
- Precipitation: {weather_data.get('precipitation_mm', 'N/A')} mm
- Conditions: {weather_data.get('conditions', 'unknown')}
- Favorable: {'Yes' if weather_data.get('is_favorable', True) else 'No'}
"""
        
        # Add space weather context if available
        space_weather_text = ""
        if space_weather_data:
            overall_status = space_weather_data.get('overall_status', 'unknown')
            communication_impact = space_weather_data.get('communication_impact', {})
            affected = communication_impact.get('affected', False)
            risk_factors = communication_impact.get('risk_factors', [])
            
            space_weather_text = f"""

Space Weather Conditions:
- Overall Status: {overall_status.upper()}
- Communication Impact: {'YES - Link quality may be degraded' if affected else 'No significant impact'}
"""
            if risk_factors:
                space_weather_text += "- Risk Factors:\n"
                for factor in risk_factors:
                    space_weather_text += f"  * {factor}\n"
        
        prompt = f"""You are a satellite operations planning assistant. Two satellite passes are scheduled at the same ground station with overlapping time windows, creating a scheduling conflict.

CONFLICT DETAILS:
Ground Station ID: {conflict.get('ground_station_id')}
Overlap Period: {overlap_start} to {overlap_end}

{pass1_details}
{pass2_details}
{alternatives_text}
{weather_text}
{space_weather_text}

TASK:
Analyze this conflict and provide a recommendation for resolution. Consider:
1. Which pass should be prioritized or rescheduled
2. Whether alternative windows are suitable (elevation above minimum threshold)
3. Weather conditions if provided
4. Space weather conditions if provided (may affect link quality)
5. Timing proximity to the original schedule

Provide your recommendation in the following format:

SUGGESTED_ACTION: [reschedule|prioritize|defer]
TARGET_PASS: [pass_id to reschedule, or "none" if prioritizing]
ALTERNATIVE_START: [ISO timestamp or "none"]
ALTERNATIVE_END: [ISO timestamp or "none"]
REASONING: [2-3 sentences explaining your recommendation based on the data provided. Reference specific values like elevation angles, timing, and weather conditions.]

Be specific and reference actual data values in your reasoning. Do not use vague statements."""
        
        return prompt
    
    def _parse_recommendation_response(
        self,
        response_text: str,
        conflict: Dict[str, Any],
        alternative_passes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Parse Claude's response into a structured recommendation."""
        
        lines = response_text.strip().split('\n')
        
        suggested_action = "reschedule"
        target_pass_id = None
        alternative_window = None
        reasoning = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("SUGGESTED_ACTION:"):
                suggested_action = line.split(":", 1)[1].strip().lower()
            
            elif line.startswith("TARGET_PASS:"):
                target = line.split(":", 1)[1].strip()
                if target.lower() != "none":
                    target_pass_id = target
            
            elif line.startswith("ALTERNATIVE_START:"):
                alt_start = line.split(":", 1)[1].strip()
                if alt_start.lower() != "none":
                    if not alternative_window:
                        alternative_window = {}
                    alternative_window['start_time'] = alt_start
            
            elif line.startswith("ALTERNATIVE_END:"):
                alt_end = line.split(":", 1)[1].strip()
                if alt_end.lower() != "none":
                    if not alternative_window:
                        alternative_window = {}
                    alternative_window['end_time'] = alt_end
            
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
                # Collect multi-line reasoning
                idx = lines.index(line)
                for next_line in lines[idx + 1:]:
                    if next_line.strip() and not next_line.strip().startswith(("SUGGESTED_ACTION:", "TARGET_PASS:", "ALTERNATIVE_")):
                        reasoning += " " + next_line.strip()
        
        # If no target pass specified, use the second pass from conflict
        if not target_pass_id and conflict.get('passes'):
            target_pass_id = conflict['passes'][1].get('id')
        
        # If no alternative window but we have alternatives, use the first one
        if not alternative_window and alternative_passes:
            best_alt = alternative_passes[0]
            alternative_window = {
                'start_time': best_alt['start_time'].isoformat() + 'Z' if isinstance(best_alt['start_time'], datetime) else best_alt['start_time'],
                'end_time': best_alt['end_time'].isoformat() + 'Z' if isinstance(best_alt['end_time'], datetime) else best_alt['end_time']
            }
        
        return {
            'conflict_id': conflict['id'],
            'suggested_action': suggested_action,
            'target_pass_id': target_pass_id,
            'alternative_window': alternative_window,
            'reasoning': reasoning if reasoning else "Recommendation generated based on orbital mechanics and scheduling constraints."
        }
    
    def _generate_fallback_recommendation(
        self,
        conflict: Dict[str, Any],
        alternative_passes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a simple fallback recommendation if LLM fails."""
        
        passes = conflict.get('passes', [])
        target_pass = passes[1] if len(passes) > 1 else passes[0]
        
        alternative_window = None
        if alternative_passes:
            best_alt = alternative_passes[0]
            alternative_window = {
                'start_time': best_alt['start_time'].isoformat() + 'Z' if isinstance(best_alt['start_time'], datetime) else best_alt['start_time'],
                'end_time': best_alt['end_time'].isoformat() + 'Z' if isinstance(best_alt['end_time'], datetime) else best_alt['end_time']
            }
        
        reasoning = f"Reschedule recommended due to scheduling conflict. "
        if alternative_window:
            reasoning += f"Alternative window available with suitable elevation angle."
        else:
            reasoning += "No immediate alternative windows available within the search period."
        
        return {
            'conflict_id': conflict['id'],
            'suggested_action': 'reschedule',
            'target_pass_id': target_pass.get('id'),
            'alternative_window': alternative_window,
            'reasoning': reasoning
        }


# Global reasoner instance
llm_reasoner = LLMReasoner()

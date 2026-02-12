"""
The Victim Prioritization Model is responsible for assessing and ranking victims
based on various factors to optimize rescue efforts.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.models import Victim, InjurySeverity, NodeRisk
from app.environment.engine import EnvironmentEngine
from app.risk.model import RiskModel

class PrioritizationConfig(BaseModel):
    """Configuration for the victim prioritization scoring function."""
    severity_weight: float = Field(0.4, ge=0.0, le=1.0, description="Weight for injury severity.")
    time_sensitivity_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for time sensitivity (survival window).")
    accessibility_risk_weight: float = Field(0.2, ge=0.0, le=1.0, description="Weight for accessibility risk.")
    num_agents_available_weight: float = Field(0.1, ge=0.0, le=1.0, description="Weight for number of agents available.")

    # Thresholds for severity scaling
    severity_critical_score: float = 1.0
    severity_severe_score: float = 0.75
    severity_moderate_score: float = 0.5
    severity_mild_score: float = 0.25

    # Other factors can be added here
    # e.g., "children_present_bonus": 0.2


class VictimPrioritizationModel:
    """
    Calculates a priority score for each victim, allowing for their ranking
    in rescue operations. The scoring is configurable and extensible.
    """

    def __init__(self, environment_engine: EnvironmentEngine, risk_model: RiskModel,
                 config: Optional[PrioritizationConfig] = None):
        """
        Initializes the VictimPrioritizationModel.

        Args:
            environment_engine (EnvironmentEngine): The environment engine.
            risk_model (RiskModel): The risk modeling layer.
            config (Optional[PrioritizationConfig]): Configuration for scoring.
                                                     Uses default if None.
        """
        self.env = environment_engine
        self.risk_model = risk_model
        self.config = config if config else PrioritizationConfig()

    async def prioritize_victims(self, victims: List[Victim], num_agents_available: int = 1) -> List[Victim]:
        """
        Calculates and assigns a priority score to each victim based on configured weights
        and environmental factors, then returns them sorted by priority.

        Args:
            victims (List[Victim]): A list of victim objects to prioritize.
            num_agents_available (int): The number of agents available for rescue.

        Returns:
            List[Victim]: The list of victims, sorted in descending order of priority score.
        """
        if not victims:
            return []

        for victim in victims:
            if victim.is_rescued:
                victim.priority_score = 0.0
                continue

            # 1. Injury Severity Score
            severity_score = self._get_severity_score(victim.injury_severity)

            # 2. Time Sensitivity Score (Survival Window)
            # Higher score for shorter survival window remaining, but also consider initial time_since
            time_remaining = victim.estimated_survival_window_minutes - victim.time_since_incident_minutes
            time_sensitivity_score = 0.0
            if time_remaining > 0:
                # Invert: shorter time remaining -> higher score. Max score if time_remaining is very low.
                # Max 1.0 if time_remaining is close to 0, min 0.0 if very long.
                time_sensitivity_score = max(0.0, min(1.0, 1 - (time_remaining / 360.0))) # Scale by max expected window

            # 3. Accessibility Risk Score
            # Use the environment's risk map to get accessibility risk.
            # Victims in higher risk areas might be prioritized due to urgent need, or deprioritized due to difficulty.
            # For now, higher risk makes it harder, so lower immediate priority. Can be inverted based on strategy.
            # Let's say, lower risk to reach is better.
            node_risk = self.risk_model.get_risk_at_coordinate(victim.location)
            accessibility_risk_val = node_risk.total_risk if node_risk else 0.0
            # Higher risk -> lower accessibility_score for prioritization, reflecting difficulty
            accessibility_score = 1.0 - accessibility_risk_val

            # 4. Agent Availability (simple factor for now)
            # More agents available might slightly increase priority for tasks requiring more resources.
            # Or, could be used to de-prioritize if no agents can reach.
            # For now, let's keep it simple and assume it's a minor bonus if agents are available.
            agent_availability_factor = 0.0 # Will be used if needed

            # --- Combine scores using weights ---
            # Sum of weights should ideally be 1.0 for direct interpretation
            total_weighted_score = (
                self.config.severity_weight * severity_score +
                self.config.time_sensitivity_weight * time_sensitivity_score +
                self.config.accessibility_risk_weight * accessibility_score +
                self.config.num_agents_available_weight * agent_availability_factor
            )

            # Normalize the score to be between 0 and 1
            victim.priority_score = min(1.0, max(0.0, total_weighted_score))

        # Sort victims by priority score in descending order
        victims.sort(key=lambda v: v.priority_score, reverse=True)
        return victims

    def _get_severity_score(self, severity: InjurySeverity) -> float:
        """Maps injury severity to a numerical score."""
        if severity == InjurySeverity.CRITICAL:
            return self.config.severity_critical_score
        elif severity == InjurySeverity.SEVERE:
            return self.config.severity_severe_score
        elif severity == InjurySeverity.MODERATE:
            return self.config.severity_moderate_score
        elif severity == InjurySeverity.MILD:
            return self.config.severity_mild_score
        return 0.0 # Should not happen

    def reset(self) -> None:
        """Resets the prioritization model's internal state if any."""
        print("VictimPrioritizationModel reset.")

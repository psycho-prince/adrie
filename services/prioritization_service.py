from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor
from typing import List, Optional

from core.config import settings
from core.utils import run_in_threadpool
from models.models import InjurySeverity, PrioritizationConfig, Victim
from services.environment_service import EnvironmentService
from services.risk_service import RiskService


class PrioritizationService:
    """Calculates a priority score for each victim, allowing for their ranking
    in rescue operations. The scoring is configurable and extensible.
    """

    def __init__(
        self,
        environment_service: EnvironmentService,
        risk_service: RiskService,
        executor: ThreadPoolExecutor,
        config: Optional[PrioritizationConfig] = None,
    ):
        """Initializes the PrioritizationService.

        Args:
            environment_service (EnvironmentService): The environment service.
            risk_service (RiskService): The risk service.
            executor (ThreadPoolExecutor): The ThreadPoolExecutor for CPU-bound tasks.
            config (Optional[PrioritizationConfig]): Configuration for scoring.
                                                     Uses default if None.

        """
        self.env = environment_service
        self.risk_model = risk_service
        self.executor = executor  # Store the executor
        self.config = (
            config
            if config
            else PrioritizationConfig(
                severity_weight=settings.PRIORITIZATION_SEVERITY_WEIGHT,
                time_sensitivity_weight=settings.PRIORITIZATION_TIME_SENSITIVITY_WEIGHT,
                accessibility_risk_weight=settings.PRIORITIZATION_ACCESSIBILITY_RISK_WEIGHT,
                num_agents_available_weight=settings.PRIORITIZATION_NUM_AGENTS_AVAILABLE_WEIGHT,
                severity_critical_score=settings.PRIORITIZATION_SEVERITY_CRITICAL_SCORE,
                severity_severe_score=settings.PRIORITIZATION_SEVERITY_SEVERE_SCORE,
                severity_moderate_score=settings.PRIORITIZATION_SEVERITY_MODERATE_SCORE,
                severity_mild_score=settings.PRIORITIZATION_SEVERITY_MILD_SCORE,
            )
        )

    async def prioritize_victims(
        self, victims: List[Victim], num_agents_available: int = 1
    ) -> List[Victim]:
        """Calculates and assigns a priority score to each victim based on configured weights
        and environmental factors, then returns them sorted by priority.

        Args:
            victims (List[Victim]): A list of victim objects to prioritize.
            num_agents_available (int): The number of agents available for rescue.

        Returns:
            List[Victim]: The list of victims, sorted in descending order of priority score.

        """
        return await run_in_threadpool(
            self._sync_prioritize_victims, self.executor, victims, num_agents_available
        )

    def _sync_prioritize_victims(
        self, victims: List[Victim], num_agents_available: int = 1
    ) -> List[Victim]:
        """Synchronous helper method to perform the CPU-bound victim prioritization logic.
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
            time_remaining = (
                victim.estimated_survival_window_minutes
                - victim.time_since_incident_minutes
            )
            time_sensitivity_score = 0.0
            if time_remaining > 0:
                # Invert: shorter time remaining -> higher score. Max score if time_remaining is very low.
                # Max 1.0 if time_remaining is close to 0, min 0.0 if very long.
                time_sensitivity_score = max(
                    0.0, min(1.0, 1 - (time_remaining / 360.0))
                )  # Scale by max expected window

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
            agent_availability_factor = 0.0  # Will be used if needed

            # --- Combine scores using weights ---
            # Sum of weights should ideally be 1.0 for direct interpretation
            total_weighted_score = (
                self.config.severity_weight * severity_score
                + self.config.time_sensitivity_weight * time_sensitivity_score
                + self.config.accessibility_risk_weight * accessibility_score
                + self.config.num_agents_available_weight * agent_availability_factor
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

    def reset(self) -> None:
        """Resets the prioritization service's internal state if any."""
        print("PrioritizationService reset.")

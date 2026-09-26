"""The Metrics Service is responsible for tracking, calculating, and reporting
various performance metrics and business KPIs for disaster response missions.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import ValidationError  # Import ValidationError

from core.exceptions import MetricsCalculationException  # Import custom exception
from core.logger import get_logger
from models.models import MetricsSummary, MetricType, Mission

logger = get_logger(__name__)


class MetricsService:
    """Manages the collection, calculation, and aggregation of metrics and KPIs
    for individual missions and the overall ADRIE system.
    """

    def __init__(self, mission_id: UUID):
        """Initializes the MetricsService for a specific mission.

        Args:
            mission_id (UUID): The ID of the mission this metrics service is tracking.

        """
        self.mission_id = mission_id
        self.metrics_data: Dict[str, Any] = {}  # Raw data collected during mission
        logger.info(f"MetricsService initialized for mission {self.mission_id}.")

    async def record_metric(
        self, metric_type: MetricType, value: Any, timestamp: Optional[str] = None
    ) -> None:
        """Records a single metric value.

        Args:
            metric_type (MetricType): The type of metric being recorded.
            value (Any): The value of the metric.
            timestamp (Optional[str]): ISO 8601 timestamp. Defaults to now if None.

        """
        if metric_type.value not in self.metrics_data:
            self.metrics_data[metric_type.value] = []

        self.metrics_data[metric_type.value].append(
            {
                "value": value,
                "timestamp": timestamp
                if timestamp
                else datetime.utcnow().isoformat() + "Z",
            }
        )
        logger.debug(
            f"Recorded metric {metric_type.value}: {value} for mission {self.mission_id}."
        )

    async def get_metrics_summary(self, mission: Mission) -> MetricsSummary:
        """Generates a comprehensive summary of key performance indicators for the mission.

        Args:
            mission (Mission): The mission object for which to generate the summary.

        Returns:
            MetricsSummary: A Pydantic model containing aggregated metrics.

        """
        summary_data: Dict[str, Any] = {"mission_id": self.mission_id}

        # Example calculations (these would be much more sophisticated in a real system)
        # Total Rescue Time
        if mission.start_time and mission.end_time:
            start = datetime.fromisoformat(mission.start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(mission.end_time.replace("Z", "+00:00"))
            summary_data[MetricType.TOTAL_RESCUE_TIME.value] = int(
                (end - start).total_seconds()
            )
        else:
            summary_data[MetricType.TOTAL_RESCUE_TIME.value] = None  # Still ongoing

        # Victims Rescued Count
        summary_data[MetricType.VICTIMS_RESCUED_COUNT.value] = len(
            mission.victims_rescued
        )

        # Predicted Lives Saved (Placeholder)
        # This would typically come from the Victim Prioritization Model or simulation outcomes
        summary_data[MetricType.PREDICTED_LIVES_SAVED.value] = len(
            mission.victims_rescued
        )  # Simple for now

        # Aggregate Risk Exposure (Placeholder: would aggregate from agent path risks)
        # For demonstration, use a fixed value or average of some recorded risk.
        if (
            MetricType.AGGREGATE_RISK_EXPOSURE.value in self.metrics_data
            and len(self.metrics_data[MetricType.AGGREGATE_RISK_EXPOSURE.value]) > 0
        ):
            risk_values = [
                item["value"]
                for item in self.metrics_data[MetricType.AGGREGATE_RISK_EXPOSURE.value]
            ]
            summary_data["average_agent_risk_exposure"] = sum(risk_values) / len(
                risk_values
            )
        else:
            summary_data["average_agent_risk_exposure"] = 0.15  # Default/example

        # Agent Utilization (Placeholder: would track agent states over time)
        summary_data["agent_utilization_percentage"] = 0.75  # Default/example

        # Efficiency Index (Placeholder: complex calculation based on multiple factors)
        summary_data["efficiency_index"] = 0.85  # Default/example

        summary_data["active_agents_count"] = len(mission.assigned_agent_ids)

        # Convert to MetricsSummary Pydantic model for validation and consistent output
        try:
            return MetricsSummary(
                mission_id=self.mission_id,
                total_rescue_time_seconds=summary_data.get(
                    MetricType.TOTAL_RESCUE_TIME.value
                ),
                average_agent_risk_exposure=summary_data.get(
                    "average_agent_risk_exposure"
                ),
                agent_utilization_percentage=summary_data.get(
                    "agent_utilization_percentage"
                ),
                efficiency_index=summary_data.get("efficiency_index"),
                predicted_lives_saved=summary_data.get(
                    MetricType.PREDICTED_LIVES_SAVED.value
                ),
                victims_rescued_count=summary_data.get(
                    MetricType.VICTIMS_RESCUED_COUNT.value
                ),
                active_agents_count=summary_data.get("active_agents_count"),
                additional_metrics={},
            )
        except ValidationError as e:
            logger.error(
                f"Pydantic validation error creating MetricsSummary for mission {self.mission_id}: {e}",
                exc_info=True,
            )
            raise MetricsCalculationException(detail=f"Validation error: {e}")
        except Exception as e:
            logger.error(
                f"Error creating MetricsSummary for mission {self.mission_id}: {e}",
                exc_info=True,
            )
            raise MetricsCalculationException(detail=f"{e}")

    def reset(self) -> None:
        """Resets the metrics service, clearing all collected data."""
        self.metrics_data = {}
        logger.info(f"MetricsService for mission {self.mission_id} reset.")

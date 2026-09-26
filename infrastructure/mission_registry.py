import asyncio
from typing import Any, Dict
from uuid import UUID

from core.exceptions import MissionConflictException, MissionNotFoundException
from models.models import Mission
# Removed all service imports


class MissionRegistry:
    """A thread-safe registry for managing active missions and their associated services.

    Replaces the global adrie_instances dictionary.
    """

    def __init__(self) -> None:
        """Initialize the MissionRegistry."""
        self._missions: Dict[UUID, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()  # Use asyncio.Lock for async compatibility

    async def add_mission(self, mission_id: UUID, mission_data: Dict[str, Any]) -> None:
        """Add a new mission and its associated data to the registry."""

        async with self._lock:
            if mission_id in self._missions:

                raise MissionConflictException(mission_id)
            self._missions[mission_id] = mission_data


    async def get_mission_data(self, mission_id: UUID) -> Dict[str, Any]:
        """Retrieve all data for a specific mission."""



        async with self._lock:
            if mission_id not in self._missions:
    
                raise MissionNotFoundException(mission_id)

            return self._missions[mission_id]

    async def remove_mission(self, mission_id: UUID) -> None:
        """Remove a mission and all its associated data from the registry."""
        async with self._lock:
            if mission_id not in self._missions:
                raise MissionNotFoundException(mission_id)
            del self._missions[mission_id]

    async def get_mission(self, mission_id: UUID) -> Mission:
        """Retrieve the Mission Pydantic model for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["mission"]

    async def get_environment_service(self, mission_id: UUID) -> "EnvironmentService":
        """Retrieve the EnvironmentService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["environment_service"]

    async def get_risk_service(self, mission_id: UUID) -> "RiskService":
        """Retrieve the RiskService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["risk_service"]

    async def get_agent_service(self, mission_id: UUID) -> "AgentService":
        """Retrieve the AgentService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["agent_service"]

    async def get_planner_service(self, mission_id: UUID) -> "PlannerService":
        """Retrieve the PlannerService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["planner_service"]

    async def get_prioritization_service(
        self, mission_id: UUID
    ) -> "PrioritizationService":
        """Retrieve the PrioritizationService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["prioritization_service"]

    async def get_explainability_service(
        self, mission_id: UUID
    ) -> "ExplainabilityService":
        """Retrieve the ExplainabilityService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["explainability_service"]

    async def get_metrics_service(self, mission_id: UUID) -> "MetricsService":
        """Retrieve the MetricsService instance for a given mission ID."""
        mission_data = await self.get_mission_data(mission_id)
        return mission_data["metrics_service"]

    async def clear(self) -> None:
        """Clear all missions from the registry."""

        async with self._lock:
            self._missions.clear()


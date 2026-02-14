"""The Environment Service is responsible for generating
and managing the disaster environment.

This includes procedural map generation, dynamic hazard modeling,
and maintaining the state of the grid.
"""

import random  # Replaced numpy with standard random
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from core.utils import run_in_threadpool
from models.models import (
    Coordinate,
    GridNode,
    Hazard,
    HazardType,
    InjurySeverity,
    NodeRisk,
    SimulateRequest,
    Victim,
    VictimStatus,
)


class EnvironmentService:
    """Manages the disaster grid environment.

    Includes map generation, hazard modeling, victim placement,
    and dynamic state updates.
    """

    def __init__(
        self,
        mission_id: Optional[UUID] = None,
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        """Initialize the EnvironmentService.

        Args:
            mission_id (Optional[UUID]): The ID of the mission this environment
                                          is associated with. If None, a new UUID
                                          will be generated.
            executor (ThreadPoolExecutor): The ThreadPoolExecutor for CPU-bound tasks.

        """
        self.mission_id: UUID = mission_id if mission_id else uuid4()
        self.executor = executor
        self.grid_size: int = 0
        self.grid: Dict[Coordinate, GridNode] = {}
        self.hazards: Dict[UUID, Hazard] = {}
        self.victims: Dict[UUID, Victim] = {}
        self.current_risk_map: Dict[Coordinate, NodeRisk] = {}
        self._initialized: bool = False

    async def initialize_environment(self, request: SimulateRequest) -> None:
        """Initialize the disaster environment based on the simulation request.

        Args:
            request (SimulateRequest): The request containing simulation parameters.

        Raises:
            RuntimeError: If environment is already initialized.
            ValidationError: If simulation request parameters are invalid.

        """
        if self._initialized:
            raise RuntimeError(
                "Environment already initialized. "
                "Create a new service for a new simulation."
            )
        if self.executor is None:
            raise RuntimeError("ThreadPoolExecutor not provided to EnvironmentService.")

        self.grid_size = request.map_size

        # Set seed for reproducibility if provided
        if request.seed is not None:
            await run_in_threadpool(random.seed, self.executor, request.seed)

        await run_in_threadpool(self._generate_grid, self.executor)
        await run_in_threadpool(
            self._generate_hazards, self.executor, request.hazard_intensity_factor
        )
        await run_in_threadpool(self._place_victims, self.executor, request.num_victims)

        self._initialized = True
        print(
            f"Environment initialized for mission {self.mission_id} with "
            f"grid size {self.grid_size}x{self.grid_size}."
        )
        print(f"Generated {len(self.hazards)} hazards and {len(self.victims)} victims.")

    def _generate_grid(self) -> None:
        """Procedurally generate the disaster grid.

        For simplicity, initially all nodes are passable and at elevation 0.
        More complex generation can be added later (e.g., buildings, rubble).
        """
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                coord = Coordinate(x=x, y=y)
                self.grid[coord] = GridNode(
                    coordinate=coord, is_passable=True, elevation=0
                )

    def _generate_hazards(self, intensity_factor: float) -> None:
        """Generate dynamic hazards across the grid based on intensity factor.

        Args:
            intensity_factor (float): Overall intensity factor influencing
                                      hazard density and severity.

        """
        num_hazards = int(
            self.grid_size * self.grid_size * intensity_factor * 0.05
        )  # 5% of grid cells potentially
        hazard_locations: Set[Coordinate] = set()

        for _ in range(num_hazards):
            x, y = (
                random.randint(0, self.grid_size - 1),
                random.randint(0, self.grid_size - 1),
            )
            location = Coordinate(x=int(x), y=int(y))
            if location in hazard_locations:
                continue  # Avoid placing multiple hazards at the exact same spot

            hazard_type = random.choice(list(HazardType))
            intensity = float(random.uniform(0.1, 1.0) * intensity_factor)
            radius = int(
                random.randint(1, min(5, self.grid_size // 5))
            )  # Max radius 5 or 1/5th of grid size

            hazard = Hazard(
                id=uuid4(),
                type=hazard_type,
                location=location,
                intensity=intensity,
                radius=radius,
                dynamic=True,
                risk_factor=intensity,  # Simple mapping for now,
                                        # to be refined by RiskModelingLayer
            )
            self.hazards[hazard.id] = hazard
            hazard_locations.add(location)

    def _place_victims(self, num_victims: int) -> None:
        """Places victims randomly on the grid.

        Args:
            num_victims (int): The number of victims to place.

        """
        placed_locations: Set[Coordinate] = set()
        for _ in range(num_victims):
            while True:
                x, y = (
                    random.randint(0, self.grid_size - 1),
                    random.randint(0, self.grid_size - 1),
                )
                location = Coordinate(x=int(x), y=int(y))
                if (
                    location not in placed_locations
                    and self.grid.get(
                        location,
                        GridNode(coordinate=location, is_passable=False, elevation=0),
                    ).is_passable
                ):
                    break
            placed_locations.add(location)

            severity = random.choice(list(InjurySeverity))
            time_since = int(random.randint(10, 120))  # 10-120 minutes
            survival_window = int(
                random.randint(time_since + 30, time_since + 360)
            )  # 30-360 mins after current time_since

            victim = Victim(
                id=uuid4(),
                location=location,
                injury_severity=severity,
                time_since_incident_minutes=time_since,
                estimated_survival_window_minutes=survival_window,
                accessibility_risk=float(random.uniform(0.1, 0.8)),
                status=VictimStatus.TRAPPED,
                priority_score=0.0,
                is_rescued=False,
                assigned_agent_id=None,
            )
            self.victims[victim.id] = victim

    def get_grid_dimensions(self) -> int:
        """Return the size of the square grid."""
        return self.grid_size

    def get_grid_node(self, coordinate: Coordinate) -> Optional[GridNode]:
        """Retrieve a GridNode by its coordinate.

        Args:
            coordinate (Coordinate): The (x,y) coordinate of the node.

        Returns:
            Optional[GridNode]: The GridNode object if found, otherwise None.

        """
        return self.grid.get(coordinate)

    def get_all_hazards(self) -> List[Hazard]:
        """Return a list of all active hazards."""
        return list(self.hazards.values())

    def get_all_victims(self) -> List[Victim]:
        """Return a list of all identified victims."""
        return list(self.victims.values())

    def update_hazard_intensity(
        self, hazard_id: UUID, new_intensity: float
    ) -> Optional[Hazard]:
        """Update the intensity of a specific hazard.

        Args:
            hazard_id (UUID): The ID of the hazard to update.
            new_intensity (float): The new intensity value (0.0 to 1.0).

        Returns:
            Optional[Hazard]: The updated Hazard object, or None if not found.

        """
        if hazard_id in self.hazards:
            self.hazards[hazard_id].intensity = new_intensity
            # Potentially trigger recalculation of risk map here or in RiskModelingLayer
            return self.hazards[hazard_id]
        return None

    def update_victim_status(
        self, victim_id: UUID, new_status: VictimStatus
    ) -> Optional[Victim]:
        """Update the status of a specific victim.

        Args:
            victim_id (UUID): The ID of the victim to update.
            new_status (VictimStatus): The new status of the victim.

        Returns:
            Optional[Victim]: The updated Victim object, or None if not found.

        """
        if victim_id in self.victims:
            self.victims[victim_id].status = new_status
            if new_status == VictimStatus.SAFE:
                self.victims[victim_id].is_rescued = True
            return self.victims[victim_id]
        return None

    def update_risk_map(self, risk_map: Dict[Coordinate, NodeRisk]) -> None:
        """Update the internal current risk map.

        This method is expected to be called by the Risk Modeling Layer.

        Args:
            risk_map (Dict[Coordinate, NodeRisk]): The newly calculated risk map.

        """
        self.current_risk_map = risk_map
        print(f"Environment risk map updated with {len(risk_map)} nodes.")

    def get_risk_at_coordinate(self, coordinate: Coordinate) -> Optional[NodeRisk]:
        """Retrieve the current risk information for a given coordinate.

        Args:
            coordinate (Coordinate): The coordinate to query risk for.

        Returns:
            Optional[NodeRisk]: The NodeRisk object for the coordinate,
                                or None if not found.

        """
        return self.current_risk_map.get(coordinate)

    def get_neighbors(self, coord: Coordinate) -> List[Coordinate]:
        """Return a list of valid, passable neighboring coordinates (up, down, left, right).

        Args:
            coord (Coordinate): The central coordinate.

        Returns:
            List[Coordinate]: A list of valid, passable neighbor coordinates.

        """
        neighbors: List[Coordinate] = []
        possible_moves_coords = [
            (coord.x + 1, coord.y),
            (coord.x - 1, coord.y),
            (coord.x, coord.y + 1),
            (coord.x, coord.y - 1),
        ]

        for move_x, move_y in possible_moves_coords:
            if 0 <= move_x < self.grid_size and 0 <= move_y < self.grid_size:
                move = Coordinate(x=move_x, y=move_y)
                node = self.grid.get(move)
                if node and node.is_passable:
                    neighbors.append(move)
        return neighbors

    def get_random_passable_coordinate(self) -> Coordinate:
        """Return a random passable coordinate from the grid."""
        if not self.grid:
            raise RuntimeError("Environment grid is not initialized.")
        passable_coords = [c for c, node in self.grid.items() if node.is_passable]
        if not passable_coords:
            raise RuntimeError("No passable coordinates found in the environment.")
        return passable_coords[
            random.randint(0, len(passable_coords) - 1)
        ]  # Adjusted for 0-indexed random

    def reset(self) -> None:
        """Reset the environment service, clearing all generated data."""
        self.grid_size = 0
        self.grid = {}
        self.hazards = {}
        self.victims = {}
        self.current_risk_map = {}
        self._initialized = False
        self.mission_id = uuid4()  # Generate new mission ID on reset
        print("EnvironmentService reset.")

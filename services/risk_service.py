"""The Risk Service is responsible for assessing and propagating risk throughout the disaster environment.
It calculates risk factors for individual grid nodes based on hazards and environmental conditions.
"""

from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor
from typing import Dict, List, Optional

from adrie.core.config import settings  # Import settings
from adrie.core.utils import run_in_threadpool
from adrie.models.models import Coordinate, Hazard, HazardType, NodeRisk, RiskLevel
from adrie.services.environment_service import EnvironmentService


class RiskService:
    """Manages risk assessment and propagation within the disaster environment.
    Calculates and updates a comprehensive risk map based on active hazards.
    """

    def __init__(
        self, environment_service: EnvironmentService, executor: ThreadPoolExecutor
    ):
        """Initializes the RiskService with a reference to the EnvironmentService.

        Args:
            environment_service (EnvironmentService): The environment service managing the disaster grid.
            executor (ThreadPoolExecutor): The ThreadPoolExecutor for CPU-bound tasks.

        """
        self.env = environment_service
        self.executor = executor  # Store the executor
        self.hazard_weights: Dict[HazardType, float] = {
            HazardType.FIRE: settings.HAZARD_FIRE_WEIGHT,
            HazardType.COLLAPSE: settings.HAZARD_COLLAPSE_WEIGHT,
            HazardType.FLOOD: settings.HAZARD_FLOOD_WEIGHT,
            HazardType.GAS_LEAK: settings.HAZARD_GAS_LEAK_WEIGHT,
            HazardType.DEBRIS: settings.HAZARD_DEBRIS_WEIGHT,
        }

    # Removed _define_hazard_weights method

    async def recalculate_risk_map(self) -> Dict[Coordinate, NodeRisk]:
        """Recalculates the complete risk map for the environment.
        This involves assessing direct hazard risks and propagating them.

        Returns:
            Dict[Coordinate, NodeRisk]: A dictionary mapping coordinates to their calculated NodeRisk.

        """
        grid_size = self.env.get_grid_dimensions()
        current_hazards = self.env.get_all_hazards()

        # Offload the synchronous logic to a thread pool
        risk_map = await run_in_threadpool(
            self._sync_recalculate_risk_map_logic,
            self.executor,
            grid_size,
            current_hazards,
        )

        self.env.update_risk_map(risk_map)
        return risk_map

    def _sync_recalculate_risk_map_logic(
        self, grid_size: int, current_hazards: List[Hazard]
    ) -> Dict[Coordinate, NodeRisk]:
        """Synchronous helper method to perform the CPU-bound risk map recalculation.
        """
        risk_map: Dict[Coordinate, NodeRisk] = {}

        # Initialize all nodes with zero risk
        for x in range(grid_size):
            for y in range(grid_size):
                coord = Coordinate(x=x, y=y)
                risk_map[coord] = NodeRisk(
                    coordinate=coord,
                    total_risk=0.0,
                    dominant_hazard=None,
                    risk_level=RiskLevel.LOW,
                )

        # Apply direct hazard risks and initial propagation
        for hazard in current_hazards:
            self._apply_hazard_risk(hazard, risk_map, grid_size)

        # Further propagate risk (e.g., to adjacent nodes)
        # This can be an iterative process if needed for complex propagation
        self._propagate_risk_to_neighbors(risk_map, grid_size)

        # Update risk levels based on total_risk
        for coord, node_risk in risk_map.items():
            node_risk.risk_level = self._get_risk_level(node_risk.total_risk)

        return risk_map

    def _apply_hazard_risk(
        self, hazard: Hazard, risk_map: Dict[Coordinate, NodeRisk], grid_size: int
    ) -> None:
        """Applies the direct risk from a single hazard to the risk map,
        considering its intensity, radius, and type-specific weight.
        """
        base_weight = self.hazard_weights.get(
            hazard.type, 0.5
        )  # Default weight if type not defined

        for x_offset in range(-hazard.radius, hazard.radius + 1):
            for y_offset in range(-hazard.radius, hazard.radius + 1):
                # Simple square radius for now; can be circular/diamond
                if abs(x_offset) + abs(y_offset) <= hazard.radius:  # Diamond shape
                    target_x, target_y = (
                        hazard.location.x + x_offset,
                        hazard.location.y + y_offset,
                    )

                    if 0 <= target_x < grid_size and 0 <= target_y < grid_size:
                        # Ensure values are strictly non-negative and within bounds
                        clamped_target_x = max(0, min(target_x, grid_size - 1))
                        clamped_target_y = max(0, min(target_y, grid_size - 1))
                        target_coord = Coordinate(x=clamped_target_x, y=clamped_target_y)
                        current_node_risk = risk_map[target_coord]

                        # Calculate risk contribution, decaying with distance
                        distance = max(1, abs(x_offset) + abs(y_offset))
                        decay_factor = settings.RISK_DECAY_FACTOR_BASE / distance
                        risk_contribution = (
                            hazard.intensity * base_weight * decay_factor
                        )

                        # Aggregate risk: simple sum for now, can be max or weighted average
                        current_node_risk.total_risk = min(
                            1.0, current_node_risk.total_risk + risk_contribution
                        )

                        # Update dominant hazard if this hazard contributes more
                        if (
                            current_node_risk.dominant_hazard is None
                            or risk_contribution
                            > self.hazard_weights.get(
                                current_node_risk.dominant_hazard, 0
                            )
                        ):
                            current_node_risk.dominant_hazard = hazard.type

    def _propagate_risk_to_neighbors(
        self, risk_map: Dict[Coordinate, NodeRisk], grid_size: int, iterations: int = 1
    ) -> None:
        """Propagates risk from high-risk nodes to adjacent nodes.
        This simulates effects like smoke spreading, or structural instability.
        """
        # A copy is needed if propagation depends on initial state of neighbors in an iteration
        # For a single iteration, we can modify in place
        for _ in range(iterations):  # Can iterate multiple times for wider propagation
            new_risk_values: Dict[Coordinate, float] = {
                coord: node_risk.total_risk for coord, node_risk in risk_map.items()
            }

            for x in range(grid_size):
                for y in range(grid_size):
                    coord = Coordinate(x=x, y=y)
                    current_risk = risk_map[coord].total_risk

                    if current_risk > 0:
                        neighbors = self.env.get_neighbors(
                            coord
                        )  # Use env's get_neighbors to respect passability
                        for neighbor_coord in neighbors:
                            # Propagate a fraction of the current node's risk
                            propagation_factor = (
                                settings.RISK_PROPAGATION_FACTOR
                            )  # This can be made dynamic/configurable
                            propagated_risk = current_risk * propagation_factor

                            # Ensure neighbor's risk doesn't decrease and doesn't exceed 1.0
                            new_risk_values[neighbor_coord] = min(
                                1.0,
                                max(new_risk_values[neighbor_coord], propagated_risk),
                            )

            # Apply the new risk values to the risk_map
            for coord, risk_val in new_risk_values.items():
                risk_map[coord].total_risk = risk_val
                risk_map[coord].risk_level = self._get_risk_level(
                    risk_map[coord].total_risk
                )

    def _get_risk_level(self, total_risk: float) -> RiskLevel:
        """Categorizes a total risk score into a predefined risk level."""
        if total_risk >= 0.8:
            return RiskLevel.CRITICAL
        elif total_risk >= 0.5:
            return RiskLevel.HIGH
        elif total_risk >= 0.2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def get_risk_at_coordinate(self, coordinate: Coordinate) -> Optional[NodeRisk]:
        """Retrieves the calculated risk for a specific coordinate from the environment's risk map.

        Args:
            coordinate (Coordinate): The coordinate to query.

        Returns:
            Optional[NodeRisk]: The NodeRisk object for the coordinate, or None if not found.

        """
        return self.env.get_risk_at_coordinate(coordinate)

    def probabilistic_collapse_model(self, coordinate: Coordinate) -> float:
        """(Stub) Implements a probabilistic model for structural collapse at a given coordinate.
        This would consider factors like hazard intensity, structural integrity, etc.

        Args:
            coordinate (Coordinate): The coordinate to assess for collapse probability.

        Returns:
            float: Probability of collapse (0.0 to 1.0).

        """
        # Placeholder: More sophisticated logic would be here
        node_risk = self.get_risk_at_coordinate(coordinate)
        if node_risk and node_risk.risk_level == RiskLevel.CRITICAL:
            return 0.7  # High probability if critical risk
        elif node_risk and node_risk.risk_level == RiskLevel.HIGH:
            return 0.3
        return 0.05  # Low background collapse probability

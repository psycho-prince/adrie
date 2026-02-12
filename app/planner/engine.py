"""
The Planning Engine generates optimal paths and action sequences for agents,
considering environmental risks, agent capabilities, and multi-objective optimization.
It utilizes a risk-weighted A* algorithm and supports dynamic re-planning.
"""

import heapq
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.core.models import Coordinate, Agent, AgentTask, AgentPlan, HazardType, NodeRisk, Plan
from app.environment.engine import EnvironmentEngine
from app.risk.model import RiskModel

class PlanningEngine:
    """
    Orchestrates pathfinding and task sequencing for multiple agents, factoring in
    environmental dynamics and risk.
    """

    def __init__(self, environment_engine: EnvironmentEngine, risk_model: RiskModel):
        """
        Initializes the PlanningEngine.

        Args:
            environment_engine (EnvironmentEngine): The environment engine.
            risk_model (RiskModel): The risk modeling layer.
        """
        self.env = environment_engine
        self.risk_model = risk_model

    async def generate_agent_plan(
        self,
        agent: Agent,
        target_task: AgentTask,
        current_mission_id: UUID,
        planning_objective: str = "minimize_risk_exposure"
    ) -> Optional[AgentPlan]:
        """
        Generates a detailed plan for a single agent to complete a given task.
        Uses a risk-weighted A* search.

        Args:
            agent (Agent): The agent for which to generate the plan.
            target_task (AgentTask): The task the agent needs to complete.
            current_mission_id (UUID): The ID of the current mission.
            planning_objective (str): The primary objective for planning
                                      (e.g., 'minimize_time', 'minimize_risk_exposure').

        Returns:
            Optional[AgentPlan]: The generated AgentPlan, or None if no path found.
        """
        start_coord = agent.current_location
        goal_coord = target_task.target_location

        if not goal_coord:
            print(f"Agent {agent.id} task has no target location. Cannot plan.")
            return None

        path, total_cost, total_risk = await self._a_star_search(
            start_coord, goal_coord, agent, planning_objective
        )

        if not path:
            print(f"No path found for agent {agent.id} to {goal_coord}.")
            return None

        # Update the task with the actual path and costs
        target_task.path_to_target = path
        target_task.expected_risk_exposure = total_risk
        target_task.estimated_time_seconds = int(total_cost) # Assuming cost loosely translates to time

        agent_plan = AgentPlan(
            agent_id=agent.id,
            tasks=[target_task],
            total_estimated_time_seconds=int(total_cost),
            total_expected_risk=total_risk
        )
        return agent_plan

    async def _a_star_search(
        self,
        start: Coordinate,
        goal: Coordinate,
        agent: Agent,
        planning_objective: str
    ) -> Tuple[Optional[List[Coordinate]], float, float]:
        """
        Implements the A* search algorithm, weighted by risk and other objectives.

        Args:
            start (Coordinate): The starting coordinate.
            goal (Coordinate): The goal coordinate.
            agent (Agent): The agent for which the path is being planned.
            planning_objective (str): The objective ('minimize_time', 'minimize_risk_exposure').

        Returns:
            Tuple[Optional[List[Coordinate]], float, float]: A tuple containing the path (list of Coordinates),
            total cost, and total risk of the path. Returns (None, 0.0, 0.0) if no path is found.
        """
        open_set: List[Tuple[float, float, Coordinate]] = [] # (f_score, g_score, coordinate)
        heapq.heappush(open_set, (0.0, 0.0, start))

        came_from: Dict[Coordinate, Coordinate] = {}
        g_score: Dict[Coordinate, float] = {start: 0.0} # Cost from start to current
        risk_score: Dict[Coordinate, float] = {start: 0.0} # Accumulated risk from start to current

        f_score: Dict[Coordinate, float] = {start: await self._heuristic(start, goal, agent, planning_objective, 0.0)}

        while open_set:
            current_f, current_g, current_coord = heapq.heappop(open_set)

            if current_coord == goal:
                path = self._reconstruct_path(came_from, current_coord)
                return path, g_score[current_coord], risk_score[current_coord]

            neighbors = self.env.get_neighbors(current_coord)
            for neighbor in neighbors:
                if not self.env.get_grid_node(neighbor) or not self.env.get_grid_node(neighbor).is_passable:
                    continue # Skip impassable nodes

                # Calculate tentative_g_score based on movement cost (e.g., 1 per step)
                tentative_g_score = g_score[current_coord] + 1.0

                # Calculate risk for the neighbor node
                neighbor_node_risk = self.risk_model.get_risk_at_coordinate(neighbor)
                current_node_risk_val = neighbor_node_risk.total_risk if neighbor_node_risk else 0.0

                # Incorporate risk into cost calculation
                # A simple way: add risk directly to cost or multiply by a factor
                cost_with_risk = 1.0 + (current_node_risk_val * 100.0) # Scale risk to make it significant

                # Calculate new accumulated risk
                new_risk_accumulator = risk_score[current_coord] + current_node_risk_val

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current_coord
                    g_score[neighbor] = tentative_g_score
                    risk_score[neighbor] = new_risk_accumulator

                    f_score[neighbor] = tentative_g_score + await self._heuristic(
                        neighbor, goal, agent, planning_objective, new_risk_accumulator
                    )
                    heapq.heappush(open_set, (f_score[neighbor], g_score[neighbor], neighbor))
        return None, 0.0, 0.0

    async def _heuristic(
        self,
        current: Coordinate,
        goal: Coordinate,
        agent: Agent,
        planning_objective: str,
        accumulated_risk: float
    ) -> float:
        """
        Calculates the heuristic cost for A* search.
        Incorporates Manhattan distance, and optionally future risk/time based on objective.
        """
        h_cost = abs(current.x - goal.x) + abs(current.y - goal.y) # Manhattan distance

        if planning_objective == "minimize_risk_exposure":
            # Heuristic should also consider future risk
            # For simplicity, we can assume future path has similar risk to current accumulated
            h_cost += accumulated_risk * 100 # Emphasize risk

        # Add agent-specific factors if any (e.g., energy cost, speed)
        # Placeholder for more complex heuristics
        return float(h_cost)

    def _reconstruct_path(self, came_from: Dict[Coordinate, Coordinate], current: Coordinate) -> List[Coordinate]:
        """Reconstructs the path from the came_from map."""
        path: List[Coordinate] = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1] # Reverse to get path from start to goal

    async def replan_if_hazards_change(self, mission_id: UUID, agents: List[Agent],
                                       planning_objective: str) -> Dict[UUID, Optional[AgentPlan]]:
        """
        (Stub) Triggers re-planning for agents if environmental hazards have significantly changed.
        This would involve comparing current risk map with previous state or actively monitoring.

        Args:
            mission_id (UUID): The ID of the current mission.
            agents (List[Agent]): List of active agents.
            planning_objective (str): The primary objective for planning.

        Returns:
            Dict[UUID, Optional[AgentPlan]]: A dictionary mapping agent_id to their new plan.
        """
        print(f"Re-planning check for mission {mission_id} (stub).")
        # In a real scenario, this would involve comparing current risk with a baseline
        # or checking for new critical alerts.
        # For now, this is a placeholder.
        return {agent.id: None for agent in agents} # No new plans by default

    def reset(self) -> None:
        """Resets the planning engine's internal state if any."""
        print("PlanningEngine reset.")

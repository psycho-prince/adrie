"""
The Multi-Agent Coordination Engine is responsible for managing multiple rescue agents,
including task allocation, collision avoidance, and route conflict resolution.
"""

from typing import Dict, List, Optional, Tuple
from uuid import UUID
from app.core.models import Agent, Coordinate, AgentStatus, AgentTask, Victim, AgentCapability
from app.environment.engine import EnvironmentEngine

class AgentCoordinationEngine:
    """
    Manages the lifecycle and coordination of multiple rescue agents within the disaster environment.
    Handles task allocation, and eventually collision avoidance and route conflict resolution.
    """

    def __init__(self, environment_engine: EnvironmentEngine):
        """
        Initializes the AgentCoordinationEngine.

        Args:
            environment_engine (EnvironmentEngine): The environment engine managing the disaster grid.
        """
        self.env = environment_engine
        self.agents: Dict[UUID, Agent] = {}

    def register_agent(self, agent: Agent) -> None:
        """
        Registers a new agent with the coordination engine.

        Args:
            agent (Agent): The agent to register.
        """
        if agent.id in self.agents:
            raise ValueError(f"Agent with ID {agent.id} already registered.")
        self.agents[agent.id] = agent
        print(f"Agent {agent.name} ({agent.id}) registered.")

    def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """
        Retrieves an agent by its ID.

        Args:
            agent_id (UUID): The ID of the agent to retrieve.

        Returns:
            Optional[Agent]: The Agent object if found, otherwise None.
        """
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[Agent]:
        """
        Returns a list of all registered agents.

        Returns:
            List[Agent]: A list of Agent objects.
        """
        return list(self.agents.values())

    def update_agent_location(self, agent_id: UUID, new_location: Coordinate) -> Optional[Agent]:
        """
        Updates the location of a specific agent.

        Args:
            agent_id (UUID): The ID of the agent to update.
            new_location (Coordinate): The new coordinate of the agent.

        Returns:
            Optional[Agent]: The updated Agent object, or None if not found.
        """
        agent = self.agents.get(agent_id)
        if agent:
            agent.current_location = new_location
            return agent
        return None

    def update_agent_status(self, agent_id: UUID, new_status: AgentStatus) -> Optional[Agent]:
        """
        Updates the status of a specific agent.

        Args:
            agent_id (UUID): The ID of the agent to update.
            new_status (AgentStatus): The new status of the agent.

        Returns:
            Optional[Agent]: The updated Agent object, or None if not found.
        """
        agent = self.agents.get(agent_id)
        if agent:
            agent.status = new_status
            return agent
        return None

    async def allocate_tasks(self, available_agents: List[Agent], victims_to_rescue: List[Victim]) -> Dict[UUID, List[AgentTask]]:
        """
        Allocates tasks (e.g., rescue a victim) to available agents.
        This is a heuristic-based allocation for now.
        Future: Implement auction-based or more sophisticated models.

        Args:
            available_agents (List[Agent]): Agents that are currently available for tasks.
            victims_to_rescue (List[Victim]): Victims that need to be rescued,
                                              presumably already prioritized.

        Returns:
            Dict[UUID, List[AgentTask]]: A dictionary mapping agent_id to a list of tasks.
        """
        agent_tasks: Dict[UUID, List[AgentTask]] = {agent.id: [] for agent in available_agents}
        
        # Simple greedy allocation: assign the closest available agent to the highest priority victim
        # This will be replaced by a more robust model later

        # Ensure agents have the capability to extract victims
        extract_capable_agents = [
            agent for agent in available_agents if AgentCapability.EXTRACT_VICTIMS in agent.capabilities
        ]

        if not extract_capable_agents:
            print("No agents capable of extracting victims are available.")
            return {}

        for victim in victims_to_rescue:
            if victim.is_rescued or victim.assigned_agent_id:
                continue # Skip if already rescued or assigned

            best_agent: Optional[Agent] = None
            min_distance: float = float('inf')

            for agent in extract_capable_agents:
                # Basic Manhattan distance for now
                distance = abs(agent.current_location.x - victim.location.x) + 
                           abs(agent.current_location.y - victim.location.y)
                
                if distance < min_distance:
                    min_distance = distance
                    best_agent = agent
            
            if best_agent:
                # Assign victim to agent
                best_agent.assigned_victim_id = victim.id
                victim.assigned_agent_id = best_agent.id
                
                # Create a task for the agent
                # The actual path will be determined by the Planning Engine
                task = AgentTask(
                    type="rescue_victim",
                    target_location=victim.location,
                    victim_id=victim.id,
                    path_to_target=[], # Will be filled by planner
                    expected_risk_exposure=victim.accessibility_risk,
                    estimated_time_seconds=int(min_distance * 10) # Placeholder for time
                )
                agent_tasks[best_agent.id].append(task)
                print(f"Assigned victim {victim.id} to agent {best_agent.name} ({best_agent.id}).")
                
                # Remove assigned agent from available list for this round of allocation
                # For more complex scenarios, an agent might be able to take multiple tasks
                available_agents.remove(best_agent) 
                extract_capable_agents.remove(best_agent) # Remove from capable agents list too
                if not extract_capable_agents:
                    print("No more extract-capable agents available for task allocation.")
                    break

        return agent_tasks

    async def avoid_collisions(self, agent_paths: Dict[UUID, List[Coordinate]]) -> Dict[UUID, List[Coordinate]]:
        """
        (Stub) Implements collision avoidance logic for agents.
        This would adjust paths to prevent agents from occupying the same space at the same time.

        Args:
            agent_paths (Dict[UUID, List[Coordinate]]): Current planned paths for agents.

        Returns:
            Dict[UUID, List[Coordinate]]: Adjusted paths to avoid collisions.
        """
        print("Collision avoidance logic (stub) executed.")
        # For now, simply return the original paths
        return agent_paths

    async def resolve_route_conflicts(self, agent_paths: Dict[UUID, List[Coordinate]]) -> Dict[UUID, List[Coordinate]]:
        """
        (Stub) Implements route conflict resolution logic.
        This would handle situations where multiple agents want to use the same critical path segment,
        optimizing for throughput or minimal delay.

        Args:
            agent_paths (Dict[UUID, List[Coordinate]]): Current planned paths for agents.

        Returns:
            Dict[UUID, List[Coordinate]]: Adjusted paths to resolve conflicts.
        """
        print("Route conflict resolution logic (stub) executed.")
        # For now, simply return the original paths
        return agent_paths

    def reset(self) -> None:
        """Resets the agent coordination engine, unregistering all agents."""
        self.agents = {}
        print("AgentCoordinationEngine reset.")

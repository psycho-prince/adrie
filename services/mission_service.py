import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from adrie.core.exceptions import (
    MissionConflictException,
    MissionNotFoundException,
)
from adrie.infrastructure.mission_registry import MissionRegistry # Import the class
from adrie.models.models import (
    Agent,
    AgentCapability,
    AgentStatus,
    AgentType,
    Mission,
    MissionStatus,
    Plan,
    PlanRequest,
    PlanResponse,
    SimulateRequest,
    SimulateResponse,
)
from adrie.services.agent_service import AgentService
from adrie.services.environment_service import EnvironmentService
from adrie.services.explainability_service import ExplainabilityService
from adrie.services.metrics_service import MetricsService
from adrie.services.planner_service import PlannerService
from adrie.services.prioritization_service import PrioritizationService
from adrie.services.risk_service import RiskService


class MissionService:
    """Manages the lifecycle and state of missions, acting as an orchestrator
    for various domain services.
    """

    def __init__(self, executor: ThreadPoolExecutor, mission_registry: MissionRegistry):
        self.executor = executor
        self.mission_registry = mission_registry # Store the injected registry

    async def initiate_simulation(self, request: SimulateRequest) -> SimulateResponse:
        """Initiates a new disaster simulation environment, generating maps, hazards, and victims.
        Initializes all mission-specific services and registers them in the MissionRegistry.
        """
        mission_id = uuid4()

        try:
            await self.mission_registry.get_mission_data(mission_id) # Use self.mission_registry
            raise MissionConflictException(mission_id)
        except MissionNotFoundException:
            # Mission does not exist, proceed with creation
            pass

        # Initialize mission-specific services
        env_service = EnvironmentService(mission_id=mission_id, executor=self.executor)
        await env_service.initialize_environment(
            request
        )

        risk_service = RiskService(
            environment_service=env_service, executor=self.executor
        )
        agent_service = AgentService(
            environment_service=env_service, executor=self.executor
        )
        planner_service = PlannerService(
            environment_service=env_service,
            risk_service=risk_service,
            executor=self.executor,
        )
        prioritization_service = PrioritizationService(
            environment_service=env_service,
            risk_service=risk_service,
            executor=self.executor,
        )
        explainability_service = ExplainabilityService()
        metrics_service = MetricsService(mission_id=mission_id)

        mission_obj = Mission(
            id=mission_id,
            name=f"Simulation {mission_id}",
            status=MissionStatus.IN_PROGRESS,
            start_time=datetime.utcnow().isoformat() + "Z",
            environment_id=mission_id,
            end_time=None,
            assigned_agent_ids=[],
            victims_identified=[],
            victims_rescued=[],
        )
        mission_data = {
            "mission": mission_obj,
            "environment_service": env_service,
            "risk_service": risk_service,
            "agent_service": agent_service,
            "planner_service": planner_service,
            "prioritization_service": prioritization_service,
            "explainability_service": explainability_service,
            "metrics_service": metrics_service,
            "current_plan": None,
        }

        await self.mission_registry.add_mission(mission_id, mission_data) # Use self.mission_registry

        await risk_service.recalculate_risk_map()

        for _ in range(request.num_agents):
            agent_service.register_agent(
                Agent(
                    id=uuid4(),
                    name=f"Agent-{uuid4().hex[:4]}",
                    type=random.choice(
                        [AgentType.ROBOTIC_ARM, AgentType.DRONE, AgentType.UGV]
                    ),
                    current_location=env_service.get_random_passable_coordinate(),
                    capabilities=[
                        AgentCapability.SEARCH_VICTIMS,
                        AgentCapability.EXTRACT_VICTIMS,
                    ],
                    status=AgentStatus.IDLE,
                    battery_level=1.0,
                    health=1.0,
                    assigned_victim_id=None,
                    current_path=[],
                    risk_exposure_tolerance=0.7,
                )
            )
        mission_obj.assigned_agent_ids = [a.id for a in agent_service.get_all_agents()]
        mission_obj.victims_identified = [v.id for v in env_service.get_all_victims()]

        return SimulateResponse(
            mission_id=mission_id, message="Simulation initiated successfully."
        )

    async def generate_mission_plan(
        self, mission_id: UUID, request: PlanRequest
    ) -> PlanResponse:
        """Generates a multi-agent rescue plan for the specified mission, considering
        victim prioritization and environmental risks.
        """
        mission = await self.mission_registry.get_mission(mission_id) # Use self.mission_registry
        if mission.status not in [MissionStatus.IN_PROGRESS, MissionStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot plan for mission in '{mission.status}' status.",
            )

        env_service = await self.mission_registry.get_environment_service(mission_id) # Use self.mission_registry
        risk_service = await self.mission_registry.get_risk_service(mission_id) # Use self.mission_registry
        agent_service = await self.mission_registry.get_agent_service(mission_id) # Use self.mission_registry
        planner_service = await self.mission_registry.get_planner_service(mission_id) # Use self.mission_registry
        prioritization_service = await self.mission_registry.get_prioritization_service( # Use self.mission_registry
            mission_id
        )

        if request.replan:
            await risk_service.recalculate_risk_map()

        victims_to_prioritize = [
            v for v in env_service.get_all_victims() if not v.is_rescued
        ]
        prioritized_victims = await prioritization_service.prioritize_victims(
            victims_to_prioritize,
            num_agents_available=len(agent_service.get_all_agents()),
        )
        victims_prioritized_order = [v.id for v in prioritized_victims]

        all_agent_plans: List[Plan] = []
        overall_plan_risk = 0.0
        overall_plan_time = 0

        # Corrected: agent_service.allocate_tasks returns Dict[UUID, List[Task]]
        available_agents = [
            a for a in agent_service.get_all_agents() if a.status == AgentStatus.IDLE
        ]

        agent_tasks_map = await agent_service.allocate_tasks(available_agents, prioritized_victims)

        for agent_id, tasks in agent_tasks_map.items():
            current_agent = agent_service.get_agent(agent_id)
            if not current_agent:
                continue

            for task in tasks:
                agent_plan = await planner_service.generate_agent_plan(
                    current_agent, task, mission_id, request.planning_objective
                )
                if agent_plan:
                    all_agent_plans.append(agent_plan)
                    overall_plan_risk += agent_plan.total_expected_risk
                    overall_plan_time += agent_plan.total_estimated_time_seconds
                    current_agent.status = (
                        AgentStatus.MOVING
                    )

        avg_risk = overall_plan_risk / len(all_agent_plans) if all_agent_plans else 0.0
        avg_time = overall_plan_time / len(all_agent_plans) if all_agent_plans else 0
        overall_efficiency_score = (
            1.0 / (avg_time + avg_risk * 100)
            if (avg_time + avg_risk * 100) > 0
            else 0.0
        )

        rescue_plan = Plan(
            id=uuid4(),
            mission_id=mission_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_plans=all_agent_plans,
            victims_to_rescue_order=victims_prioritized_order,
            overall_risk_score=avg_risk,
            overall_efficiency_score=overall_efficiency_score,
        )

        (await self.mission_registry.get_mission_data(mission_id))["current_plan"] = ( # Use self.mission_registry
            rescue_plan
        )

        return PlanResponse(
            plan_id=rescue_plan.id,
            mission_id=mission_id,
            agent_plans=all_agent_plans,
            victims_prioritized_order=victims_prioritized_order,
            message="Plan generated successfully.",
        )

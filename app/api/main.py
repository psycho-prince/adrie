"""
Main FastAPI application for ADRIE.
This file sets up the FastAPI app, includes routers, and handles dependency injection.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict
from uuid import UUID

from configs.config import settings
from app.core.logger import get_logger
from app.core.models import SimulateRequest, SimulateResponse, PlanRequest, PlanResponse, ExplainabilityOutput, MissionStatus, Mission
from app.environment.engine import EnvironmentEngine
from app.risk.model import RiskModel
from app.agents.engine import AgentCoordinationEngine
from app.planner.engine import PlanningEngine
from app.prioritization.model import VictimPrioritizationModel
from app.explainability.service import ExplainabilityService
from app.metrics.engine import MetricsEngine # Will implement this soon

logger = get_logger(__name__)

# --- Global State Management (for single-instance engines) ---
# In a more complex, multi-tenant system, these might be managed per-mission or per-user.
# For this prototype, we'll maintain a single instance for simplicity.
adrie_instances: Dict[UUID, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    Initializes core ADRIE components.
    """
    logger.info(f"Starting up ADRIE: {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} environment.")
    # Here we would initialize any global resources, e.g., database connections, LLM clients.
    yield
    logger.info("Shutting down ADRIE.")
    # Clean up resources if necessary
    adrie_instances.clear()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Disaster Response Intelligence Engine API",
    lifespan=lifespan
)

# --- Dependency Injection Functions ---

async def get_environment_engine(mission_id: UUID) -> EnvironmentEngine:
    """Provides a mission-specific EnvironmentEngine instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["environment_engine"]

async def get_risk_model(mission_id: UUID) -> RiskModel:
    """Provides a mission-specific RiskModel instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["risk_model"]

async def get_agent_coordination_engine(mission_id: UUID) -> AgentCoordinationEngine:
    """Provides a mission-specific AgentCoordinationEngine instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["agent_coordination_engine"]

async def get_planning_engine(mission_id: UUID) -> PlanningEngine:
    """Provides a mission-specific PlanningEngine instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["planning_engine"]

async def get_victim_prioritization_model(mission_id: UUID) -> VictimPrioritizationModel:
    """Provides a mission-specific VictimPrioritizationModel instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["victim_prioritization_model"]

async def get_explainability_service(mission_id: UUID) -> ExplainabilityService:
    """Provides a mission-specific ExplainabilityService instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["explainability_service"]

async def get_metrics_engine(mission_id: UUID) -> MetricsEngine:
    """Provides a mission-specific MetricsEngine instance."""
    if mission_id not in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {mission_id} not found."
        )
    return adrie_instances[mission_id]["metrics_engine"]

# --- API Endpoints ---

@app.get("/", summary="Root endpoint for ADRIE API")
async def root():
    """Provides a simple welcome message and API status."""
    return {"message": "Welcome to ADRIE API", "version": settings.APP_VERSION, "status": "online"}

@app.post("/simulate", response_model=SimulateResponse, status_code=status.HTTP_201_CREATED,
          summary="Initiate a new disaster simulation.")
async def simulate(request: SimulateRequest):
    """
    Initiates a new disaster simulation environment, generating maps, hazards, and victims.
    Returns a mission ID to track the simulation.
    """
    mission_id = UUID(request.mission_id) if request.mission_id else UUID(uuid4())
    
    if mission_id in adrie_instances:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mission with ID {mission_id} already exists. Please choose a different ID or reset."
        )

    try:
        env_engine = EnvironmentEngine(mission_id=mission_id)
        env_engine.initialize_environment(request)
        
        # Initialize other components for this mission
        risk_model = RiskModel(environment_engine=env_engine)
        agent_coord_engine = AgentCoordinationEngine(environment_engine=env_engine)
        planning_engine = PlanningEngine(environment_engine=env_engine, risk_model=risk_model)
        victim_prioritization_model = VictimPrioritizationModel(environment_engine=env_engine, risk_model=risk_model)
        explainability_service = ExplainabilityService() # LLM interface will be injected/configured later
        metrics_engine = MetricsEngine(mission_id=mission_id)

        adrie_instances[mission_id] = {
            "mission": Mission(
                id=mission_id,
                name=f"Simulation {mission_id}",
                status=MissionStatus.IN_PROGRESS,
                start_time=datetime.utcnow().isoformat() + "Z",
                environment_id=mission_id
            ),
            "environment_engine": env_engine,
            "risk_model": risk_model,
            "agent_coordination_engine": agent_coord_engine,
            "planning_engine": planning_engine,
            "victim_prioritization_model": victim_prioritization_model,
            "explainability_service": explainability_service,
            "metrics_engine": metrics_engine
        }

        # Automatically recalculate initial risk map after environment is set up
        await risk_model.recalculate_risk_map()

        # Register agents if any
        for _ in range(request.num_agents):
            agent_coord_engine.register_agent(
                Agent(
                    id=UUID(uuid4()),
                    name=f"Agent-{uuid4().hex[:4]}",
                    type=np.random.choice([AgentType.ROBOTIC_ARM, AgentType.DRONE, AgentType.UGV]),
                    current_location=env_engine._get_random_passable_coordinate(), # Helper method
                    capabilities=[AgentCapability.SEARCH_VICTIMS, AgentCapability.EXTRACT_VICTIMS]
                )
            )
        adrie_instances[mission_id]["mission"].assigned_agent_ids = [a.id for a in agent_coord_engine.get_all_agents()]
        adrie_instances[mission_id]["mission"].victims_identified = [v.id for v in env_engine.get_all_victims()]

        logger.info(f"Simulation {mission_id} initialized successfully.")
        return SimulateResponse(mission_id=mission_id, message="Simulation initiated successfully.")

    except Exception as e:
        logger.error(f"Error initiating simulation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate simulation: {e}"
        )

@app.post("/plan/{mission_id}", response_model=PlanResponse, status_code=status.HTTP_200_OK,
          summary="Generate a rescue plan for agents in a specific mission.")
async def plan(
    mission_id: UUID,
    request: PlanRequest,
    env_engine: EnvironmentEngine = Depends(get_environment_engine),
    risk_model: RiskModel = Depends(get_risk_model),
    agent_coord_engine: AgentCoordinationEngine = Depends(get_agent_coordination_engine),
    planning_engine: PlanningEngine = Depends(get_planning_engine),
    victim_prioritization_model: VictimPrioritizationModel = Depends(get_victim_prioritization_model)
):
    """
    Generates a multi-agent rescue plan for the specified mission, considering
    victim prioritization and environmental risks.
    """
    try:
        mission = adrie_instances[mission_id]["mission"]
        if mission.status not in [MissionStatus.IN_PROGRESS, MissionStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot plan for mission in '{mission.status}' status."
            )

        # 1. Recalculate Risk Map (if hazards changed or on replan request)
        # In a real system, this would be triggered by environment updates
        if request.replan or True: # For now, always recalculate for fresh data
             await risk_model.recalculate_risk_map()

        # 2. Prioritize Victims
        victims_to_prioritize = [v for v in env_engine.get_all_victims() if not v.is_rescued]
        prioritized_victims = await victim_prioritization_model.prioritize_victims(
            victims_to_prioritize,
            num_agents_available=len(agent_coord_engine.get_all_agents())
        )
        victims_prioritized_order = [v.id for v in prioritized_victims]

        # 3. Task Allocation (Assign prioritized victims to agents)
        available_agents = [a for a in agent_coord_engine.get_all_agents() if a.status == AgentStatus.IDLE]
        agent_tasks_map = await agent_coord_engine.allocate_tasks(available_agents, prioritized_victims)

        # 4. Generate Plans for each agent
        all_agent_plans: List[AgentPlan] = []
        overall_plan_risk = 0.0
        overall_plan_time = 0

        for agent_id, tasks in agent_tasks_map.items():
            current_agent = agent_coord_engine.get_agent(agent_id)
            if not current_agent:
                logger.warning(f"Agent {agent_id} not found during plan generation.")
                continue

            for task in tasks:
                agent_plan = await planning_engine.generate_agent_plan(
                    current_agent, task, mission_id, request.planning_objective
                )
                if agent_plan:
                    all_agent_plans.append(agent_plan)
                    overall_plan_risk += agent_plan.total_expected_risk
                    overall_plan_time += agent_plan.total_estimated_time_seconds
                    current_agent.status = AgentStatus.MOVING # Update agent status to reflect planning

        # Simple aggregation for overall scores
        avg_risk = overall_plan_risk / len(all_agent_plans) if all_agent_plans else 0.0
        avg_time = overall_plan_time / len(all_agent_plans) if all_agent_plans else 0
        overall_efficiency_score = 1.0 / (avg_time + avg_risk * 100) if (avg_time + avg_risk * 100) > 0 else 0.0

        rescue_plan = Plan(
            id=UUID(uuid4()),
            mission_id=mission_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_plans=all_agent_plans,
            victims_to_rescue_order=victims_prioritized_order,
            overall_risk_score=avg_risk,
            overall_efficiency_score=overall_efficiency_score
        )
        
        # Store the generated plan
        adrie_instances[mission_id]["current_plan"] = rescue_plan

        logger.info(f"Plan {rescue_plan.id} generated for mission {mission_id}.")
        return PlanResponse(
            plan_id=rescue_plan.id,
            mission_id=mission_id,
            agent_plans=all_agent_plans,
            victims_prioritized_order=victims_prioritized_order,
            message="Plan generated successfully."
        )

    except HTTPException:
        raise # Re-raise FastAPI HTTP exceptions
    except Exception as e:
        logger.error(f"Error generating plan for mission {mission_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plan: {e}"
        )

@app.get("/metrics/{mission_id}", status_code=status.HTTP_200_OK,
         summary="Retrieve performance metrics and KPIs for a specific mission.")
async def get_mission_metrics(
    mission_id: UUID,
    metrics_engine: MetricsEngine = Depends(get_metrics_engine)
):
    """
    Retrieves the latest performance metrics and business KPIs for the specified mission.
    """
    try:
        mission = adrie_instances[mission_id]["mission"]
        metrics_summary = await metrics_engine.get_metrics_summary(mission)
        logger.info(f"Retrieved metrics for mission {mission_id}.")
        return metrics_summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving metrics for mission {mission_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {e}"
        )

@app.get("/explain/{mission_id}/{explanation_type}", response_model=ExplainabilityOutput, status_code=status.HTTP_200_OK,
          summary="Get explainable AI output for a specific decision or mission summary.")
async def get_explanation(
    mission_id: UUID,
    explanation_type: ExplanationType,
    decision_id: Optional[UUID] = None, # For specific decision, e.g., victim prioritization ID
    explainability_service: ExplainabilityService = Depends(get_explainability_service),
    env_engine: EnvironmentEngine = Depends(get_environment_engine)
):
    """
    Provides an explanation for critical decisions or a summary for a mission.
    - `explanation_type`: Type of explanation requested (e.g., VICTIM_PRIORITIZATION, ROUTE_SELECTION, MISSION_SUMMARY, TRADE_OFF_ANALYSIS).
    - `decision_id`: Optional ID of a specific decision to explain (e.g., victim ID for prioritization).
    """
    try:
        mission = adrie_instances[mission_id]["mission"]
        
        # Placeholder for building decision context based on explanation_type
        decision_context: Dict[str, Any] = {}
        human_readable_summary = "Explanation not yet implemented for this type or context."
        structured_explanation_json = {}

        if explanation_type == ExplanationType.VICTIM_PRIORITIZATION:
            if not decision_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="decision_id (victim ID) is required for victim prioritization explanation.")
            
            victim = env_engine.victims.get(decision_id)
            if not victim:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Victim with ID {decision_id} not found in mission {mission_id}.")

            # Example context, would be richer with actual decision logic
            decision_context = {
                "victim_id": str(victim.id),
                "injury_severity": victim.injury_severity.value,
                "time_sensitivity": victim.time_since_incident_minutes,
                "survival_window": victim.estimated_survival_window_minutes,
                "accessibility_risk": victim.accessibility_risk,
                "priority_score": victim.priority_score
            }
            explanation_output = await explainability_service.generate_victim_prioritization_explanation(
                mission, victim, env_engine.get_all_victims(), decision_context
            )
        elif explanation_type == ExplanationType.MISSION_SUMMARY:
            current_plan = adrie_instances[mission_id].get("current_plan")
            if not current_plan:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No plan found for mission {mission_id}. Generate a plan first.")
            metrics_summary = await adrie_instances[mission_id]["metrics_engine"].get_metrics_summary(mission)
            # key_decisions would be pulled from a log of decisions
            explanation_output = await explainability_service.generate_mission_summary(
                mission, current_plan, metrics_summary.model_dump(), [] # Empty list for key_decisions for now
            )
        elif explanation_type == ExplanationType.ROUTE_SELECTION:
            # Requires more context, e.g., which agent, which segment, alternatives
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Route selection explanation not fully implemented yet.")
        elif explanation_type == ExplanationType.TRADE_OFF_ANALYSIS:
            # Requires context on the specific trade-off
             raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Trade-off analysis explanation not fully implemented yet.")
        else:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported explanation type: {explanation_type.value}")
        
        logger.info(f"Generated {explanation_type.value} explanation for mission {mission_id}.")
        return explanation_output

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation for mission {mission_id}, type {explanation_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {e}"
        )



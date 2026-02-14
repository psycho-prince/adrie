from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_thread_pool_executor,
    get_mission_registry,
)
from core.config import settings
from core.exceptions import (
    ExplanationNotImplementedException,
    InvalidExplanationRequestException,
    MetricsCalculationException,
    MissionConflictException,
    MissionNotFoundException,
    PlanningException,
    ServiceInitializationException,
    VictimNotFoundException, # New import
    AgentNotFoundException, # New import
)
from core.logger import get_logger
from infrastructure.mission_registry import MissionRegistry
from models.models import (
    ExplainabilityOutput,
    ExplanationType,
    MetricsSummary,
    PlanRequest,
    PlanResponse,
    SimulateRequest,
    SimulateResponse,
)
from services.agent_service import AgentService
from services.environment_service import EnvironmentService
from services.explainability_service import ExplainabilityService
from services.metrics_service import MetricsService
from services.mission_service import MissionService
from services.planner_service import PlannerService
from services.prioritization_service import PrioritizationService
from services.risk_service import RiskService

router = APIRouter()
logger = get_logger(__name__)

# --- Dependency Injection Functions ---


async def get_mission_service(
    executor: ThreadPoolExecutor = Depends(get_thread_pool_executor),
    registry: MissionRegistry = Depends(get_mission_registry),
) -> MissionService:
    """Provide a MissionService instance."""

    return MissionService(executor=executor, mission_registry=registry)


async def get_environment_service(
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry),
) -> EnvironmentService:
    """Provide a mission-specific EnvironmentService instance."""
    try:
        return await registry.get_environment_service(mission_id)
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


async def get_risk_service(
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry),
) -> RiskService:
    """Provide a mission-specific RiskService instance."""
    try:
        return await registry.get_risk_service(mission_id)
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


async def get_agent_service(
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry),
) -> AgentService:
    """Provide a mission-specific AgentService instance."""
    try:
        return await registry.get_agent_service(mission_id)
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


async def get_planner_service(
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry),
) -> PlannerService:
    """Provide a mission-specific PlannerService instance."""
    try:
        return await registry.get_planner_service(mission_id)
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


async def get_prioritization_service(
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry),
) -> PrioritizationService:
    """Provide a mission-specific PrioritizationService instance."""
    try:
        return await registry.get_prioritization_service(mission_id)
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


async def get_explainability_service(
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry), # Inject MissionRegistry
) -> ExplainabilityService:
    """Provide a mission-specific ExplainabilityService instance."""
    try:
        # Note: ExplainabilityService does not take mission_id in its constructor,
        # but it uses the registry to retrieve mission-specific data within its methods.
        return ExplainabilityService(mission_registry=registry) # Pass registry to constructor
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


async def get_metrics_service_dependency( # Renamed this function
    mission_id: UUID,
    registry: MissionRegistry = Depends(get_mission_registry), # Inject MissionRegistry
) -> MetricsService:
    """Provide a mission-specific MetricsService instance."""
    try:
        return await registry.get_metrics_service(mission_id) # Use injected registry
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )


# --- API Endpoints ---


@router.get("/", summary="Root endpoint for ADRIE API")
async def root() -> Dict[str, str]:
    """Provide a simple welcome message and API status."""
    return {
        "message": "Welcome to ADRIE API",
        "version": settings.APP_VERSION,
        "status": "online",
    }


@router.post(
    "/simulate",
    response_model=SimulateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a new disaster simulation.",
)
async def simulate(
    request: SimulateRequest,
    mission_service: MissionService = Depends(get_mission_service),
) -> SimulateResponse:
    """Initiate a new disaster simulation environment,
    generating maps, hazards, and victims.

    Returns a mission ID to track the simulation.
    """
    try:
        return await mission_service.initiate_simulation(request)
    except MissionConflictException as e:
        raise e  # Re-raise custom HTTP exceptions
    except ServiceInitializationException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error initiating simulation: {e}", exc_info=True)
        raise ServiceInitializationException(
            service_name="MissionService", detail=f"An unexpected error occurred: {e}"
        )


@router.post(
    "/plan/{mission_id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a rescue plan for agents in a specific mission.",
)
async def plan(
    mission_id: UUID,
    request: PlanRequest,
    mission_service: MissionService = Depends(get_mission_service),
) -> PlanResponse:
    """Generate a multi-agent rescue plan for the specified mission.

    Consider victim prioritization and environmental risks.
    """
    try:
        return await mission_service.generate_mission_plan(mission_id, request)
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )
    except (
        HTTPException
    ):  # Re-raise FastAPI HTTP exceptions (e.g., from mission status check)
        raise
    except PlanningException as e:
        raise e
    except Exception as e:
        logger.error(
            f"Unexpected error generating plan for mission {mission_id}: {e}",
            exc_info=True,
        )
        raise PlanningException(detail=f"An unexpected error occurred: {e}")


@router.get(
    "/metrics/{mission_id}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve performance metrics and KPIs for a specific mission.",
)
async def get_mission_metrics(
    mission_id: UUID,
    metrics_service: MetricsService = Depends(get_metrics_service_dependency), # Use renamed dependency
    registry: MissionRegistry = Depends(get_mission_registry), # Inject MissionRegistry
) -> MetricsSummary:
    """Retrieve the latest performance metrics
    and business KPIs for the specified mission.
    """
    try:
        mission = await registry.get_mission(mission_id) # Use injected registry
        metrics_summary = await metrics_service.get_metrics_summary(mission)
        logger.info(f"Retrieved metrics for mission {mission_id}.")
        return metrics_summary
    except MissionNotFoundException as e: # Use e.entity_id here
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )
    except MetricsCalculationException as e:
        raise e
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving metrics for mission {mission_id}: {e}",
            exc_info=True,
        )
        raise MetricsCalculationException(detail=f"An unexpected error occurred: {e}")


@router.get(
    "/explain/{mission_id}/{explanation_type}",
    response_model=ExplainabilityOutput,
    status_code=status.HTTP_200_OK,
    summary="Get explainable AI output for a specific decision or mission summary.",
)
async def get_explanation(
    mission_id: UUID,
    explanation_type: ExplanationType,
    decision_id: Optional[
        UUID
    ] = None,  # For specific decision, e.g., victim prioritization ID
    explainability_service: ExplainabilityService = Depends(get_explainability_service),
) -> ExplainabilityOutput:
    """Provide an explanation for critical decisions or a summary for a mission.

    - `explanation_type`: Type of explanation requested
      (e.g., VICTIM_PRIORITIZATION, ROUTE_SELECTION, MISSION_SUMMARY, TRADE_OFF_ANALYSIS).
    - `decision_id`: Optional ID of a specific decision to explain
      (e.g., victim ID for prioritization).
    """
    try:
        return await explainability_service.get_explanation_output(
            mission_id, explanation_type, decision_id
        )
    except VictimNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim with ID {e.entity_id} not found."
        )
    except AgentNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {e.entity_id} not found."
        )
    except MissionNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {e.entity_id} not found."
        )
    except ExplanationNotImplementedException as e:
        raise e
    except InvalidExplanationRequestException as e:
        raise e
    except Exception as e:
        logger.error(
            f"Unexpected error generating explanation for mission {mission_id}, "
            f"type {explanation_type}: {e}",
            exc_info=True,
        )
        raise InvalidExplanationRequestException(
            detail=f"An unexpected error occurred during explanation generation: {e}"
        )

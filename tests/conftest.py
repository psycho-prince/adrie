"""
Configuration and fixtures for pytest.
"""

import pytest
from httpx import AsyncClient
from adrie.main import app as fastapi_app
from adrie.services.environment_service import EnvironmentService
from adrie.services.risk_service import RiskService
from adrie.services.agent_service import AgentService
from adrie.services.planner_service import PlannerService
from adrie.services.prioritization_service import PrioritizationService
from adrie.services.explainability_service import ExplainabilityService
from adrie.services.metrics_service import MetricsService
from adrie.services.mission_service import MissionService
from adrie.services.metrics_service import MetricsService
from adrie.infrastructure.mission_registry import mission_registry
from uuid import uuid4, UUID
from typing import Generator, AsyncGenerator, Tuple
from concurrent.futures import ThreadPoolExecutor
import asyncio

@pytest.fixture(name="test_app")
async def test_app_fixture() -> AsyncGenerator[AsyncClient, None]:
    """Fixture for FastAPI TestClient."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client

@pytest.fixture(name="executor_fixture")
def executor_fixture() -> Generator[ThreadPoolExecutor, None, None]:
    """Fixture for a ThreadPoolExecutor instance."""
    executor = ThreadPoolExecutor(max_workers=1) # Use a small number of workers for testing
    yield executor
    executor.shutdown(wait=True)

@pytest.fixture(autouse=True)
async def clear_mission_registry() -> AsyncGenerator[None, None]:
    """Clears mission_registry before and after each test to ensure isolation."""
    await mission_registry.clear()
    yield
    await mission_registry.clear()

@pytest.fixture(name="mock_mission_id")
def mock_mission_id_fixture() -> UUID:
    """Fixture for a consistent mock mission ID."""
    return uuid4()

@pytest.fixture(name="environment_engine")
def environment_engine_fixture(mock_mission_id: UUID, executor_fixture: ThreadPoolExecutor) -> EnvironmentService:
    """Fixture for a fresh EnvironmentService instance with injected executor."""
    return EnvironmentService(mission_id=mock_mission_id, executor=executor_fixture)

@pytest.fixture(name="risk_model")
def risk_model_fixture(environment_engine: EnvironmentService, executor_fixture: ThreadPoolExecutor) -> RiskService:
    """Fixture for a fresh RiskService instance with injected executor."""
    return RiskService(environment_service=environment_engine, executor=executor_fixture)

@pytest.fixture(name="agent_service")
def agent_service_fixture(environment_engine: EnvironmentService, executor_fixture: ThreadPoolExecutor) -> AgentService:
    """Fixture for a fresh AgentService instance with injected executor."""
    return AgentService(environment_engine=environment_engine, executor=executor_fixture)

@pytest.fixture(name="planner_service")
def planner_service_fixture(environment_engine: EnvironmentService, risk_model: RiskService, executor_fixture: ThreadPoolExecutor) -> PlannerService:
    """Fixture for a fresh PlannerService instance with injected executor."""
    return PlannerService(environment_service=environment_engine, risk_service=risk_model, executor=executor_fixture)

@pytest.fixture(name="prioritization_service")
def prioritization_service_fixture(environment_engine: EnvironmentService, risk_model: RiskService, executor_fixture: ThreadPoolExecutor) -> PrioritizationService:
    """Fixture for a fresh PrioritizationService instance with injected executor."""
    return PrioritizationService(environment_service=environment_engine, risk_service=risk_model, executor=executor_fixture)

@pytest.fixture(name="explainability_service")
def explainability_service_fixture() -> ExplainabilityService:
    """Fixture for a fresh ExplainabilityService instance."""
    return ExplainabilityService()

@pytest.fixture(name="metrics_engine")
def metrics_engine_fixture(mock_mission_id: UUID) -> MetricsService:
    """Fixture for a fresh MetricsService instance."""
    return MetricsService(mission_id=mock_mission_id)

@pytest.fixture(name="mission_service")
def mission_service_fixture(executor_fixture: ThreadPoolExecutor) -> MissionService:
    """Fixture for a fresh MissionService instance with injected executor."""
    return MissionService(executor=executor_fixture)

# Add fixtures for other components as they are developed

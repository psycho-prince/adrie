"""
Configuration and fixtures for pytest.
"""

import pytest
from httpx import AsyncClient
from adrie.main import create_app # Import the factory function
from adrie.api.dependencies import get_mission_registry # This import should now succeed
from adrie.infrastructure.mission_registry import MissionRegistry
from adrie.services.environment_service import EnvironmentService
from adrie.services.risk_service import RiskService
from adrie.services.agent_service import AgentService
from adrie.services.planner_service import PlannerService
from adrie.services.prioritization_service import PrioritizationService
from adrie.services.explainability_service import ExplainabilityService
from adrie.services.metrics_service import MetricsService
from adrie.services.mission_service import MissionService
from adrie.services.metrics_service import MetricsService
from uuid import uuid4, UUID
from typing import Generator, AsyncGenerator, Tuple
from concurrent.futures import ThreadPoolExecutor
import asyncio

@pytest.fixture
async def clear_mission_registry() -> AsyncGenerator[MissionRegistry, None]:
    """Provides a fresh MissionRegistry instance for each test and clears it afterwards."""

    test_registry = MissionRegistry() # Create a new instance
    await test_registry.clear() # Ensure it's empty to start
    yield test_registry # Provide this instance to dependent fixtures

    await test_registry.clear() # Clear it after the test

@pytest.fixture
def mock_get_mission_registry(clear_mission_registry: MissionRegistry):
    """Overrides the get_mission_registry dependency to use the test fixture."""
    # This fixture now correctly receives the yielded MissionRegistry instance

    return clear_mission_registry

@pytest.fixture(name="test_app")
async def test_app_fixture(mock_get_mission_registry: MissionRegistry) -> AsyncGenerator[AsyncClient, None]:
    """Fixture for FastAPI TestClient, managing application lifespan and dependency overrides."""
    app_instance = create_app() # Get a fresh app instance
    # Override the dependency for get_mission_registry
    app_instance.dependency_overrides[get_mission_registry] = lambda: mock_get_mission_registry
    async with app_instance.router.lifespan_context(app_instance): # Use the new app instance
        async with AsyncClient(app=app_instance, base_url="http://test") as client:
            yield client
    # Clear the overrides after the test is done
    app_instance.dependency_overrides.clear()

@pytest.fixture(name="executor_fixture")
def executor_fixture() -> Generator[ThreadPoolExecutor, None, None]:
    """Fixture for a ThreadPoolExecutor instance."""
    executor = ThreadPoolExecutor(max_workers=1) # Use a small number of workers for testing
    yield executor
    executor.shutdown(wait=True)

# @pytest.fixture(autouse=False) # This fixture is now replaced by clear_mission_registry yielding the instance
# async def clear_mission_registry() -> AsyncGenerator[None, None]:
#     """Clears mission_registry before and after each test to ensure isolation."""
#     await mission_registry.clear()
#     yield
#     await mission_registry.clear()

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
def mission_service_fixture(
    executor_fixture: ThreadPoolExecutor,
    mock_get_mission_registry: MissionRegistry # Accept the mock registry
) -> MissionService:
    """Fixture for a fresh MissionService instance with injected executor and registry."""
    return MissionService(executor=executor_fixture, mission_registry=mock_get_mission_registry)

# Add fixtures for other components as they are developed

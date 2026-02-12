"""
Configuration and fixtures for pytest.
"""

import pytest
from httpx import AsyncClient
from app.api.main import app as fastapi_app
from app.environment.engine import EnvironmentEngine
from app.risk.model import RiskModel
from app.agents.engine import AgentCoordinationEngine
from app.planner.engine import PlanningEngine
from app.prioritization.model import VictimPrioritizationModel
from app.explainability.service import ExplainabilityService
from app.metrics.engine import MetricsEngine
from app.api.main import adrie_instances # Import global state for testing
from uuid import uuid4

@pytest.fixture(name="test_app")
async def test_app_fixture():
    """Fixture for FastAPI TestClient."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client

@pytest.fixture(autouse=True)
def clear_adrie_instances():
    """Clears adrie_instances before each test to ensure isolation."""
    adrie_instances.clear()
    yield
    adrie_instances.clear()

@pytest.fixture(name="mock_mission_id")
def mock_mission_id_fixture():
    """Fixture for a consistent mock mission ID."""
    return uuid4()

@pytest.fixture(name="environment_engine")
def environment_engine_fixture(mock_mission_id):
    """Fixture for a fresh EnvironmentEngine instance."""
    return EnvironmentEngine(mission_id=mock_mission_id)

@pytest.fixture(name="risk_model")
def risk_model_fixture(environment_engine):
    """Fixture for a fresh RiskModel instance."""
    return RiskModel(environment_engine=environment_engine)

@pytest.fixture(name="agent_coordination_engine")
def agent_coordination_engine_fixture(environment_engine):
    """Fixture for a fresh AgentCoordinationEngine instance."""
    return AgentCoordinationEngine(environment_engine=environment_engine)

@pytest.fixture(name="planning_engine")
def planning_engine_fixture(environment_engine, risk_model):
    """Fixture for a fresh PlanningEngine instance."""
    return PlanningEngine(environment_engine=environment_engine, risk_model=risk_model)

@pytest.fixture(name="victim_prioritization_model")
def victim_prioritization_model_fixture(environment_engine, risk_model):
    """Fixture for a fresh VictimPrioritizationModel instance."""
    return VictimPrioritizationModel(environment_engine=environment_engine, risk_model=risk_model)

@pytest.fixture(name="explainability_service")
def explainability_service_fixture():
    """Fixture for a fresh ExplainabilityService instance."""
    return ExplainabilityService()

@pytest.fixture(name="metrics_engine")
def metrics_engine_fixture(mock_mission_id):
    """Fixture for a fresh MetricsEngine instance."""
    return MetricsEngine(mission_id=mock_mission_id)

# Add fixtures for other components as they are developed

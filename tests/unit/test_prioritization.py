"""
Unit tests for the VictimPrioritizationModel module.
"""

import pytest
from uuid import uuid4
from adrie.services.environment_service import EnvironmentService
from adrie.services.risk_service import RiskService
from adrie.services.prioritization_service import PrioritizationService
from adrie.models.models import Victim, InjurySeverity, Coordinate, VictimStatus, NodeRisk, RiskLevel, PrioritizationConfig, SimulateRequest
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor # Import ThreadPoolExecutor

@pytest.fixture
async def initialized_env_and_risk(environment_engine: EnvironmentService, risk_model: RiskService, executor_fixture: ThreadPoolExecutor) -> Tuple[EnvironmentService, RiskService]:
    """Fixture to provide an initialized environment and risk model."""
    request = SimulateRequest(map_size=10, hazard_intensity_factor=0.5, num_victims=0, num_agents=0, seed=42)
    await environment_engine.initialize_environment(request)
    # Manually set a risk map for predictability
    for x in range(environment_engine.grid_size):
        for y in range(environment_engine.grid_size):
            coord = Coordinate(x=x, y=y)
            # Create a gradient of risk: higher risk at (0,0)
            total_risk = max(0.0, 1.0 - ((x + y) / (environment_engine.grid_size * 2)))
            risk_level = risk_model._get_risk_level(total_risk)
            environment_engine.current_risk_map[coord] = NodeRisk(
                coordinate=coord, total_risk=total_risk, dominant_hazard=None, risk_level=risk_level
            )
    return environment_engine, risk_model

@pytest.mark.asyncio
async def test_prioritization_model_initialization(initialized_env_and_risk: Tuple[EnvironmentService, RiskService], executor_fixture: ThreadPoolExecutor) -> None:
    """Test if the PrioritizationService initializes correctly."""
    env, risk = initialized_env_and_risk
    model = PrioritizationService(env, risk, executor=executor_fixture)
    assert model.env == env
    assert model.risk_model == risk
    assert isinstance(model.config, PrioritizationConfig)

@pytest.mark.asyncio
async def test_prioritize_victims_empty_list(initialized_env_and_risk: Tuple[EnvironmentService, RiskService], executor_fixture: ThreadPoolExecutor) -> None:
    """Test prioritization with an empty list of victims."""
    env, risk = initialized_env_and_risk
    model = PrioritizationService(env, risk, executor=executor_fixture)
    prioritized = await model.prioritize_victims([])
    assert len(prioritized) == 0

@pytest.mark.asyncio
async def test_prioritize_single_victim(initialized_env_and_risk: Tuple[EnvironmentService, RiskService], executor_fixture: ThreadPoolExecutor) -> None:
    """Test prioritization of a single victim."""
    env, risk = initialized_env_and_risk
    model = PrioritizationService(env, risk, executor=executor_fixture)

    victim = Victim(
        id=uuid4(),
        location=Coordinate(x=5, y=5), # Medium risk area
        injury_severity=InjurySeverity.SEVERE,
        time_since_incident_minutes=30,
        estimated_survival_window_minutes=120,
        accessibility_risk=0.3, # Initial, will be overridden by risk_model
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        is_rescued=False,
        assigned_agent_id=None
    )
    victims = [victim]
    prioritized = await model.prioritize_victims(victims)

    assert len(prioritized) == 1
    assert prioritized[0].id == victim.id
    assert 0.0 < prioritized[0].priority_score <= 1.0 # Score should be calculated

@pytest.mark.asyncio
async def test_prioritize_multiple_victims(initialized_env_and_risk: Tuple[EnvironmentService, RiskService], executor_fixture: ThreadPoolExecutor) -> None:
    """Test prioritization with multiple victims with varying attributes."""
    env, risk = initialized_env_and_risk
    model = PrioritizationService(env, risk, executor=executor_fixture)

    # Victim 1: High severity, short survival, medium accessibility risk
    victim1 = Victim(
        id=uuid4(),
        location=Coordinate(x=1, y=1), # High risk area (lower accessibility score)
        injury_severity=InjurySeverity.CRITICAL,
        time_since_incident_minutes=90,
        estimated_survival_window_minutes=120,
        accessibility_risk=0.8,
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        is_rescued=False,
        assigned_agent_id=None
    )
    # Victim 2: Medium severity, longer survival, low accessibility risk
    victim2 = Victim(
        id=uuid4(),
        location=Coordinate(x=8, y=8), # Low risk area (higher accessibility score)
        injury_severity=InjurySeverity.MODERATE,
        time_since_incident_minutes=10,
        estimated_survival_window_minutes=360,
        accessibility_risk=0.1,
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        is_rescued=False,
        assigned_agent_id=None
    )
    # Victim 3: Severe, medium survival, medium accessibility risk
    victim3 = Victim(
        id=uuid4(),
        location=Coordinate(x=5, y=5), # Medium risk area
        injury_severity=InjurySeverity.SEVERE,
        time_since_incident_minutes=60,
        estimated_survival_window_minutes=240,
        accessibility_risk=0.4,
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        is_rescued=False,
        assigned_agent_id=None
    )

    victims = [victim1, victim2, victim3]
    prioritized = await model.prioritize_victims(victims)

    # Verify sorting: Victim1 (critical) should generally be highest, Victim2 (moderate) lowest
    # Exact scores depend on weights and formula, but relative order should be consistent.
    assert len(prioritized) == 3
    assert prioritized[0].priority_score >= prioritized[1].priority_score
    assert prioritized[1].priority_score >= prioritized[2].priority_score

    # Critical victim should have higher score than moderate, given reasonable weights
    assert prioritized[0].id == victim1.id
    assert prioritized[2].id == victim2.id

    # Check scores are within valid range
    for v in prioritized:
        assert 0.0 <= v.priority_score <= 1.0

@pytest.mark.asyncio
async def test_prioritize_rescued_victim(initialized_env_and_risk: Tuple[EnvironmentService, RiskService], executor_fixture: ThreadPoolExecutor) -> None:
    """Test that rescued victims are not prioritized."""
    env, risk = initialized_env_and_risk
    model = PrioritizationService(env, risk, executor=executor_fixture)

    victim_rescued = Victim(
        id=uuid4(),
        location=Coordinate(x=1, y=1),
        injury_severity=InjurySeverity.CRITICAL,
        time_since_incident_minutes=10,
        estimated_survival_window_minutes=60,
        accessibility_risk=0.1,
        is_rescued=True,
        status=VictimStatus.SAFE,
        priority_score=0.0,
        assigned_agent_id=None
    )
    victim_not_rescued = Victim(
        id=uuid4(),
        location=Coordinate(x=5, y=5),
        injury_severity=InjurySeverity.SEVERE,
        time_since_incident_minutes=20,
        estimated_survival_window_minutes=120,
        accessibility_risk=0.2,
        is_rescued=False,
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        assigned_agent_id=None
    )

    victims = [victim_rescued, victim_not_rescued]
    prioritized = await model.prioritize_victims(victims)

    assert len(prioritized) == 2
    # Rescued victim should have 0 priority score and be last
    assert prioritized[0].id == victim_not_rescued.id
    assert prioritized[0].priority_score > 0.0
    assert prioritized[1].id == victim_rescued.id
    assert prioritized[1].priority_score == 0.0

@pytest.mark.asyncio
async def test_prioritization_with_custom_config(initialized_env_and_risk: Tuple[EnvironmentService, RiskService], executor_fixture: ThreadPoolExecutor) -> None:
    """Test prioritization with a custom configuration."""
    env, risk = initialized_env_and_risk
    custom_config = PrioritizationConfig(
        severity_weight=0.1,
        time_sensitivity_weight=0.8, # Emphasize time over severity
        accessibility_risk_weight=0.1,
        num_agents_available_weight=0.0
    )
    model = PrioritizationService(env, risk, executor=executor_fixture, config=custom_config)

    # Victim 1: High severity, but long survival window
    victim1 = Victim(
        id=uuid4(),
        location=Coordinate(x=5, y=5),
        injury_severity=InjurySeverity.CRITICAL,
        time_since_incident_minutes=10,
        estimated_survival_window_minutes=300, # Long survival
        accessibility_risk=0.2,
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        is_rescued=False,
        assigned_agent_id=None
    )
    # Victim 2: Medium severity, but very short survival window
    victim2 = Victim(
        id=uuid4(),
        location=Coordinate(x=5, y=5),
        injury_severity=InjurySeverity.MODERATE,
        time_since_incident_minutes=80,
        estimated_survival_window_minutes=100, # Short survival
        accessibility_risk=0.2,
        status=VictimStatus.TRAPPED,
        priority_score=0.0,
        is_rescued=False,
        assigned_agent_id=None
    )

    victims = [victim1, victim2]
    prioritized = await model.prioritize_victims(victims)

    assert len(prioritized) == 2
    # With high time_sensitivity_weight, victim2 should be prioritized over victim1
    assert prioritized[0].id == victim2.id
    assert prioritized[1].id == victim1.id

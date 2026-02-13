"""
Unit tests for the RiskModel module.
"""

import pytest
from adrie.services.environment_service import EnvironmentService
from adrie.services.risk_service import RiskService
from adrie.models.models import SimulateRequest, Coordinate, Hazard, HazardType, NodeRisk, RiskLevel
from uuid import uuid4

@pytest.mark.asyncio
async def test_risk_model_initialization(risk_model: RiskService) -> None:
    """Test if the RiskModel initializes correctly with hazard weights."""
    assert risk_model.hazard_weights is not None
    assert HazardType.FIRE in risk_model.hazard_weights
    assert risk_model.env is not None

@pytest.mark.asyncio
async def test_recalculate_risk_map_no_hazards(environment_engine: EnvironmentService, risk_model: RiskService) -> None:
    """Test risk map calculation when there are no hazards."""
    request = SimulateRequest(map_size=5, hazard_intensity_factor=0.0, num_victims=0, num_agents=0, seed=None)
    await environment_engine.initialize_environment(request)
    
    risk_map = await risk_model.recalculate_risk_map()
    
    assert len(risk_map) == 25 # 5x5 grid
    for coord, node_risk in risk_map.items():
        assert node_risk.total_risk == 0.0
        assert node_risk.risk_level == RiskLevel.LOW
        assert node_risk.dominant_hazard is None

@pytest.mark.asyncio
async def test_recalculate_risk_map_with_hazards(environment_engine: EnvironmentService, risk_model: RiskService) -> None:
    """Test risk map calculation with some hazards."""
    request = SimulateRequest(map_size=10, hazard_intensity_factor=0.5, num_victims=0, num_agents=0, seed=42)
    await environment_engine.initialize_environment(request)
    
    # Manually add a specific hazard for predictable testing
    hazard_coord = Coordinate(x=5, y=5)
    fire_hazard = Hazard(
        id=uuid4(),
        type=HazardType.FIRE,
        location=hazard_coord,
        intensity=0.8,
        radius=2,
        dynamic=True,
        risk_factor=0.8
    )
    environment_engine.hazards[fire_hazard.id] = fire_hazard

    risk_map = await risk_model.recalculate_risk_map()

    # Check the hazard's center and its immediate neighbors
    center_risk = risk_map[hazard_coord]
    assert center_risk.total_risk > 0.0
    assert center_risk.dominant_hazard == HazardType.FIRE

    # Check a direct neighbor
    neighbor_coord = Coordinate(x=5, y=6)
    neighbor_risk = risk_map[neighbor_coord]
    assert neighbor_risk.total_risk > 0.0
    assert neighbor_risk.dominant_hazard == HazardType.FIRE # Due to propagation or radius

    # Check a node far from the hazard
    far_coord = Coordinate(x=0, y=0)
    far_risk = risk_map[far_coord]
    assert far_risk.total_risk >= 0.0 # Could be slightly > 0 due to propagation, but much lower
    assert far_risk.total_risk < center_risk.total_risk
    
    # Ensure some nodes have higher risk levels
    assert any(node.risk_level != RiskLevel.LOW for node in risk_map.values())

@pytest.mark.asyncio
async def test_get_risk_at_coordinate(environment_engine: EnvironmentService, risk_model: RiskService) -> None:
    """Test retrieving risk for a specific coordinate."""
    request = SimulateRequest(map_size=5, hazard_intensity_factor=0.7, num_victims=0, num_agents=0, seed=1)
    await environment_engine.initialize_environment(request)
    await risk_model.recalculate_risk_map()

    coord_with_risk = Coordinate(x=2, y=2)
    risk_info = risk_model.get_risk_at_coordinate(coord_with_risk)
    assert risk_info is not None
    assert isinstance(risk_info, NodeRisk)

    non_existent_coord = Coordinate(x=100, y=100)
    assert risk_model.get_risk_at_coordinate(non_existent_coord) is None

@pytest.mark.asyncio
async def test_probabilistic_collapse_model(environment_engine: EnvironmentService, risk_model: RiskService) -> None:
    """Test the probabilistic collapse model (stub)."""
    request = SimulateRequest(map_size=5, hazard_intensity_factor=0.7, num_victims=0, num_agents=0, seed=1)
    await environment_engine.initialize_environment(request)
    await risk_model.recalculate_risk_map() # Ensure risk map is populated

    # Test a coordinate that likely has low risk
    low_risk_coord = Coordinate(x=0, y=0)
    low_risk_prob = risk_model.probabilistic_collapse_model(low_risk_coord)
    assert low_risk_prob == 0.05

    # Test a coordinate that might have high risk (if a hazard is near)
    # This test is less deterministic due to random hazard placement,
    # but we can at least ensure it returns a float.
    high_risk_prob = risk_model.probabilistic_collapse_model(Coordinate(x=2,y=2))
    assert isinstance(high_risk_prob, float)
    assert 0.0 <= high_risk_prob <= 1.0

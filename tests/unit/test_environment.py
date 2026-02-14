"""
Unit tests for the EnvironmentEngine module.
"""

import pytest
from uuid import UUID
from services.environment_service import EnvironmentService
from models.models import SimulateRequest, Coordinate, HazardType, VictimStatus, InjurySeverity

@pytest.mark.asyncio
async def test_environment_initialization(environment_engine: EnvironmentService) -> None:
    """Test if the environment initializes correctly."""
    request = SimulateRequest(map_size=10, hazard_intensity_factor=0.5, num_victims=5, num_agents=2, seed=42)
    await environment_engine.initialize_environment(request)

    assert environment_engine.grid_size == 10
    assert len(environment_engine.grid) == 100 # 10x10 grid
    assert len(environment_engine.hazards) > 0
    assert len(environment_engine.victims) == 5
    assert environment_engine._initialized is True

    with pytest.raises(RuntimeError, match="Environment already initialized"):
        await environment_engine.initialize_environment(request) # Should not allow re-initialization

@pytest.mark.asyncio
async def test_get_grid_node(environment_engine: EnvironmentService) -> None:
    """Test retrieving a specific grid node."""
    request = SimulateRequest(map_size=5, hazard_intensity_factor=0.5, num_victims=1, num_agents=1, seed=None)
    await environment_engine.initialize_environment(request)

    coord = Coordinate(x=2, y=2)
    node = environment_engine.get_grid_node(coord)
    assert node is not None
    assert node.coordinate == coord
    assert node.is_passable is True

    non_existent_coord = Coordinate(x=100, y=100)
    assert environment_engine.get_grid_node(non_existent_coord) is None

@pytest.mark.asyncio
async def test_update_hazard_intensity(environment_engine: EnvironmentService) -> None:
    """Test updating a hazard's intensity."""
    request = SimulateRequest(map_size=5, hazard_intensity_factor=1.0, num_victims=0, num_agents=0, seed=1)
    await environment_engine.initialize_environment(request)

    initial_hazards = environment_engine.get_all_hazards()
    assert len(initial_hazards) > 0
    hazard_to_update = initial_hazards[0]
    
    new_intensity = 0.99
    updated_hazard = environment_engine.update_hazard_intensity(hazard_to_update.id, new_intensity)
    assert updated_hazard is not None
    assert updated_hazard.intensity == new_intensity
    assert environment_engine.hazards[hazard_to_update.id].intensity == new_intensity

    # Test updating non-existent hazard
    non_existent_hazard_id = UUID('00000000-0000-0000-0000-000000000000')
    assert environment_engine.update_hazard_intensity(non_existent_hazard_id, 0.5) is None

@pytest.mark.asyncio
async def test_update_victim_status(environment_engine: EnvironmentService) -> None:
    """Test updating a victim's status."""
    request = SimulateRequest(map_size=5, hazard_intensity_factor=0.5, num_victims=1, num_agents=0, seed=1)
    await environment_engine.initialize_environment(request)

    initial_victims = environment_engine.get_all_victims()
    assert len(initial_victims) == 1
    victim_to_update = initial_victims[0]
    
    assert victim_to_update.status == VictimStatus.TRAPPED
    assert victim_to_update.is_rescued is False

    updated_victim = environment_engine.update_victim_status(victim_to_update.id, VictimStatus.SAFE)
    assert updated_victim is not None
    assert updated_victim.status == VictimStatus.SAFE
    assert updated_victim.is_rescued is True
    assert environment_engine.victims[victim_to_update.id].status == VictimStatus.SAFE

    # Test updating non-existent victim
    non_existent_victim_id = UUID('00000000-0000-0000-0000-000000000000')
    assert environment_engine.update_victim_status(non_existent_victim_id, VictimStatus.SAFE) is None

@pytest.mark.asyncio
async def test_get_neighbors(environment_engine: EnvironmentService) -> None:
    """Test getting valid neighbors for a coordinate."""
    request = SimulateRequest(map_size=3, hazard_intensity_factor=0.5, num_victims=0, num_agents=0, seed=None)
    await environment_engine.initialize_environment(request)

    # Center coordinate (1,1)
    center_coord = Coordinate(x=1, y=1)
    neighbors = environment_engine.get_neighbors(center_coord)
    assert len(neighbors) == 4
    assert Coordinate(x=1, y=0) in neighbors
    assert Coordinate(x=1, y=2) in neighbors
    assert Coordinate(x=0, y=1) in neighbors
    assert Coordinate(x=2, y=1) in neighbors

    # Corner coordinate (0,0)
    corner_coord = Coordinate(x=0, y=0)
    neighbors = environment_engine.get_neighbors(corner_coord)
    assert len(neighbors) == 2
    assert Coordinate(x=0, y=1) in neighbors
    assert Coordinate(x=1, y=0) in neighbors

    # Edge coordinate (0,1)
    edge_coord = Coordinate(x=0, y=1)
    neighbors = environment_engine.get_neighbors(edge_coord)
    assert len(neighbors) == 3
    assert Coordinate(x=0, y=0) in neighbors
    assert Coordinate(x=0, y=2) in neighbors
    assert Coordinate(x=1, y=1) in neighbors

@pytest.mark.asyncio
async def test_reset_environment(environment_engine: EnvironmentService) -> None:
    """Test resetting the environment."""
    request = SimulateRequest(map_size=10, hazard_intensity_factor=0.5, num_victims=5, num_agents=2, seed=42)
    await environment_engine.initialize_environment(request)

    assert environment_engine.grid_size == 10
    assert environment_engine._initialized is True

    environment_engine.reset()
    assert environment_engine.grid_size == 0
    assert not environment_engine.grid
    assert not environment_engine.hazards
    assert not environment_engine.victims
    assert environment_engine._initialized is False

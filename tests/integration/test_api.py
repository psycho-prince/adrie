"""
Integration tests for the ADRIE FastAPI endpoints.
These tests use a test client to simulate HTTP requests to the API.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID
from adrie.models.models import SimulateRequest, SimulateResponse, PlanRequest, PlanResponse, ExplanationType
from adrie.infrastructure.mission_registry import mission_registry # Import mission_registry
from adrie.models.models import Mission, MissionStatus, AgentType, AgentCapability, Coordinate
from adrie.services.environment_service import EnvironmentService # Import EnvironmentService
from adrie.services.agent_service import AgentService # Import AgentService

@pytest.mark.asyncio
async def test_root_endpoint(test_app: AsyncClient) -> None:
    """Test the root endpoint for basic connectivity."""
    response = await test_app.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to ADRIE API"
    assert "version" in response.json()
    assert "status" in response.json()

@pytest.mark.asyncio
async def test_simulate_disaster_success(test_app: AsyncClient) -> None:
    """Test successful disaster simulation initiation."""
    request_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 2,
        "num_agents": 1
    }
    response = await test_app.post("/simulate", json=request_payload)
    assert response.status_code == 201
    
    response_data = SimulateResponse(**response.json())
    assert isinstance(response_data.mission_id, UUID)
    assert response_data.message == "Simulation initiated successfully."

    # Verify internal state for the mission
    mission_state = await mission_registry.get_mission_data(response_data.mission_id)
    assert mission_state is not None
    assert isinstance(mission_state["environment_service"], EnvironmentService)
    assert mission_state["mission"].status == MissionStatus.IN_PROGRESS
    assert len(mission_state["environment_service"].get_all_victims()) == request_payload["num_victims"]
    assert len(mission_state["agent_service"].get_all_agents()) == request_payload["num_agents"]


@pytest.mark.asyncio
async def test_simulate_disaster_conflict(test_app: AsyncClient) -> None:
    """Test trying to simulate with an existing mission ID."""
    # First, create a mission
    request_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 2,
        "num_agents": 1,
        "mission_id": str(UUID("a1a2a3a4-b1b2-c1c2-d1d2-e1e2e3e4e5e6")) # Specific ID for testing
    }
    response = await test_app.post("/simulate", json=request_payload)
    assert response.status_code == 201

    # Try to create another mission with the same ID
    response_conflict = await test_app.post("/simulate", json=request_payload)
    assert response_conflict.status_code == 409
    assert "already exists" in response_conflict.json()["detail"]

@pytest.mark.asyncio
async def test_plan_generation_success(test_app: AsyncClient) -> None:
    """Test successful rescue plan generation."""
    # First, initiate a simulation
    simulate_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 1,
        "num_agents": 1
    }
    simulate_response = await test_app.post("/simulate", json=simulate_payload)
    mission_id = SimulateResponse(**simulate_response.json()).mission_id

    # Then, request a plan
    plan_payload = {
        "planning_objective": "minimize_risk_exposure",
        "replan": False
    }
    response = await test_app.post(f"/plan/{mission_id}", json=plan_payload)
    assert response.status_code == 200

    response_data = PlanResponse(**response.json())
    assert isinstance(response_data.plan_id, UUID)
    assert response_data.mission_id == mission_id
    assert len(response_data.agent_plans) > 0 # At least one agent should have a plan
    assert len(response_data.victims_prioritized_order) > 0
    assert response_data.message == "Plan generated successfully."

@pytest.mark.asyncio
async def test_plan_generation_mission_not_found(test_app: AsyncClient) -> None:
    """Test plan generation for a non-existent mission."""
    non_existent_mission_id = UUID('00000000-0000-0000-0000-000000000000')
    plan_payload = {
        "planning_objective": "minimize_risk_exposure",
        "replan": False
    }
    response = await test_app.post(f"/plan/{non_existent_mission_id}", json=plan_payload)
    assert response.status_code == 404
    assert "Mission with ID" in response.json()["detail"]
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_metrics_success(test_app: AsyncClient) -> None:
    """Test fetching mission metrics."""
    # First, initiate a simulation
    simulate_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 1,
        "num_agents": 1
    }
    simulate_response = await test_app.post("/simulate", json=simulate_payload)
    mission_id = SimulateResponse(**simulate_response.json()).mission_id

    # Then, fetch metrics
    response = await test_app.get(f"/metrics/{mission_id}")
    assert response.status_code == 200
    
    metrics_data = response.json()
    assert metrics_data["mission_id"] == str(mission_id)
    assert "total_rescue_time_seconds" in metrics_data
    assert "predicted_lives_saved" in metrics_data

@pytest.mark.asyncio
async def test_get_metrics_mission_not_found(test_app: AsyncClient) -> None:
    """Test fetching metrics for a non-existent mission."""
    non_existent_mission_id = UUID('00000000-0000-0000-0000-000000000000')
    response = await test_app.get(f"/metrics/{non_existent_mission_id}")
    assert response.status_code == 404
    assert "Mission with ID" in response.json()["detail"]
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_explain_victim_prioritization_success(test_app: AsyncClient) -> None:
    """Test getting explanation for victim prioritization."""
    # First, initiate a simulation with victims
    simulate_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 1,
        "num_agents": 1
    }
    simulate_response = await test_app.post("/simulate", json=simulate_payload)
    mission_id = SimulateResponse(**simulate_response.json()).mission_id

    # Get a victim ID from the simulated environment
    mission_state = await mission_registry.get_mission_data(mission_id)
    env_service: EnvironmentService = mission_state["environment_service"]
    victims = env_service.get_all_victims()
    assert len(victims) > 0
    victim_id = victims[0].id

    # Then, request an explanation for victim prioritization
    response = await test_app.get(f"/explain/{mission_id}/{ExplanationType.VICTIM_PRIORITIZATION.value}",
                                 params={"decision_id": str(victim_id)})
    assert response.status_code == 200
    
    explanation_data = response.json()
    assert explanation_data["mission_id"] == str(mission_id)
    assert explanation_data["explanation_type"] == ExplanationType.VICTIM_PRIORITIZATION.value
    assert "human_readable_summary" in explanation_data
    assert "structured_explanation_json" in explanation_data

@pytest.mark.asyncio
async def test_get_explain_mission_summary_success(test_app: AsyncClient) -> None:
    """Test getting mission summary explanation."""
    # First, initiate a simulation
    simulate_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 1,
        "num_agents": 1
    }
    simulate_response = await test_app.post("/simulate", json=simulate_payload)
    mission_id = SimulateResponse(**simulate_response.json()).mission_id

    # Then, request a plan (required for mission summary for now)
    plan_payload = {
        "planning_objective": "minimize_risk_exposure",
        "replan": False
    }
    await test_app.post(f"/plan/{mission_id}", json=plan_payload)


    # Then, request an explanation for mission summary
    response = await test_app.get(f"/explain/{mission_id}/{ExplanationType.MISSION_SUMMARY.value}")
    assert response.status_code == 200
    
    explanation_data = response.json()
    assert explanation_data["mission_id"] == str(mission_id)
    assert explanation_data["explanation_type"] == ExplanationType.MISSION_SUMMARY.value
    assert "human_readable_summary" in explanation_data
    assert "structured_explanation_json" in explanation_data

@pytest.mark.asyncio
async def test_get_explain_mission_not_found(test_app: AsyncClient) -> None:
    """Test explanation request for a non-existent mission."""
    non_existent_mission_id = UUID('00000000-0000-0000-0000-000000000000')
    response = await test_app.get(f"/explain/{non_existent_mission_id}/{ExplanationType.VICTIM_PRIORITIZATION.value}",
                                 params={"decision_id": str(UUID(int=0))}) # Dummy decision_id
    assert response.status_code == 404
    assert "Mission with ID" in response.json()["detail"]
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_explain_victim_not_found(test_app: AsyncClient) -> None:
    """Test explanation for non-existent victim."""
    # First, initiate a simulation
    simulate_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 0, # Ensure no victims
        "num_agents": 1
    }
    simulate_response = await test_app.post("/simulate", json=simulate_payload)
    mission_id = SimulateResponse(**simulate_response.json()).mission_id

    non_existent_victim_id = UUID('00000000-0000-0000-0000-000000000000')
    response = await test_app.get(f"/explain/{mission_id}/{ExplanationType.VICTIM_PRIORITIZATION.value}",
                                 params={"decision_id": str(non_existent_victim_id)})
    assert response.status_code == 404
    assert "Victim with ID" in response.json()["detail"]
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_explain_missing_decision_id_for_prioritization(test_app: AsyncClient) -> None:
    """Test explanation for victim prioritization without providing decision_id."""
    # First, initiate a simulation
    simulate_payload = {
        "map_size": 10,
        "hazard_intensity_factor": 0.5,
        "num_victims": 1,
        "num_agents": 1
    }
    simulate_response = await test_app.post("/simulate", json=simulate_payload)
    mission_id = SimulateResponse(**simulate_response.json()).mission_id

    response = await test_app.get(f"/explain/{mission_id}/{ExplanationType.VICTIM_PRIORITIZATION.value}")
    assert response.status_code == 400
    assert "decision_id (victim ID) is required" in response.json()["detail"]

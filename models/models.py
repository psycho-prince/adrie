"""Core data models for the ADRIE system,
defined using Pydantic for data validation and serialization.

These models represent the fundamental entities and data structures
used throughout the application.
"""

from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
)

from core.config import settings  # Import settings

# --- Basic Geometric Models ---


class Coordinate(BaseModel):
    """Represents a 2D coordinate in the disaster grid."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    x: NonNegativeInt = Field(..., description="X-coordinate on the grid.")
    y: NonNegativeInt = Field(..., description="Y-coordinate on the grid.")

    def __lt__(self, other: "Coordinate") -> bool:
        if self.x < other.x:
            return True
        if self.x == other.x and self.y < other.y:
            return True
        return False

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Coordinate):
            return NotImplemented
        return self.x == other.x and self.y == other.y


class GridNode(BaseModel):
    """Represents a single node (cell) in the disaster grid."""

    model_config = ConfigDict(extra="forbid")
    coordinate: Coordinate = Field(
        ..., description="The (x, y) coordinate of the grid node."
    )
    is_passable: bool = Field(
        True, description="Whether the node can be traversed by agents."
    )
    elevation: int = Field(
        0, description="Elevation of the node, for 3D pathfinding considerations."
    )


# --- Hazard and Risk Models ---


class HazardType(str, Enum):
    """Defines different types of hazards present in the environment."""

    FIRE = "fire"
    COLLAPSE = "collapse"
    FLOOD = "flood"
    GAS_LEAK = "gas_leak"
    DEBRIS = "debris"


class Hazard(BaseModel):
    """Represents an active hazard in the disaster environment."""

    model_config = ConfigDict(extra="forbid")
    id: UUID4 = Field(..., description="Unique identifier for the hazard.")
    type: HazardType = Field(..., description="The type of hazard.")
    location: Coordinate = Field(..., description="The grid coordinate of the hazard.")
    intensity: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Intensity of the hazard (0.0 to 1.0)."
    )
    radius: NonNegativeInt = Field(1, description="Radius of effect for the hazard.")
    dynamic: bool = Field(
        True, description="Whether the hazard's properties can change over time."
    )
    risk_factor: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Normalized risk factor contributed by this hazard."
    )


class RiskLevel(str, Enum):
    """Defines categories for overall risk at a grid node or path segment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NodeRisk(BaseModel):
    """Represents the calculated risk at a specific grid node."""

    model_config = ConfigDict(extra="forbid")
    coordinate: Coordinate = Field(..., description="The coordinate of the node.")
    total_risk: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Aggregate risk score for the node (0.0 to 1.0)."
    )
    dominant_hazard: Optional[HazardType] = Field(
        None, description="The primary hazard contributing to the risk."
    )
    risk_level: RiskLevel = Field(
        ..., description="Categorized risk level for the node."
    )


# --- Victim Models ---


class InjurySeverity(str, Enum):
    """Categorizes the severity of a victim's injuries."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class VictimStatus(str, Enum):
    """Describes the current status of a victim."""

    TRAPPED = "trapped"
    INJURED = "injured"
    SAFE = "safe"
    DECEASED = "deceased"
    UNKNOWN = "unknown"


class Victim(BaseModel):
    """Represents a victim in the disaster scenario."""

    model_config = ConfigDict(extra="forbid")
    id: UUID4 = Field(..., description="Unique identifier for the victim.")
    location: Coordinate = Field(
        ..., description="The current grid coordinate of the victim."
    )
    injury_severity: InjurySeverity = Field(
        ..., description="Severity of the victim's injuries."
    )
    time_since_incident_minutes: PositiveInt = Field(
        ..., description="Time elapsed since the incident for the victim."
    )
    estimated_survival_window_minutes: PositiveInt = Field(
        ..., description="Estimated remaining survival time."
    )
    status: VictimStatus = Field(
        VictimStatus.TRAPPED, description="Current status of the victim."
    )
    accessibility_risk: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Risk associated with reaching this victim."
    )
    priority_score: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        0.0, description="Calculated priority score for rescue (0.0 to 1.0)."
    )
    is_rescued: bool = Field(False, description="True if the victim has been rescued.")
    assigned_agent_id: Optional[UUID4] = Field(
        None, description="ID of the agent assigned to this victim."
    )


# --- Agent Models ---


class AgentType(str, Enum):
    """Defines different types of rescue agents."""

    ROBOTIC_ARM = "robotic_arm"
    DRONE = "drone"
    SEARCH_DOG = "search_dog"
    HUMAN_RESCUER = "human_rescuer"
    UGV = "unmanned_ground_vehicle"


class AgentStatus(str, Enum):
    """Describes the current operational status of an agent."""

    IDLE = "idle"
    MOVING = "moving"
    SEARCHING = "searching"
    RESCUING = "rescuing"
    RETURNING_TO_BASE = "returning_to_base"
    DAMAGED = "damaged"
    OFFLINE = "offline"


class AgentCapability(str, Enum):
    """Capabilities an agent might possess."""

    SEARCH_VICTIMS = "search_victims"
    EXTRACT_VICTIMS = "extract_victims"
    CLEAR_DEBRIS = "clear_debris"
    ASSESS_HAZARDS = "assess_hazards"
    CARRY_SUPPLIES = "carry_supplies"


class Agent(BaseModel):
    """Represents a rescue agent in the system."""

    model_config = ConfigDict(extra="forbid")
    id: UUID4 = Field(..., description="Unique identifier for the agent.")
    name: str = Field(..., description="Human-readable name of the agent.")
    type: AgentType = Field(..., description="The type of rescue agent.")
    current_location: Coordinate = Field(
        ..., description="The current grid coordinate of the agent."
    )
    status: AgentStatus = Field(
        AgentStatus.IDLE, description="Current operational status of the agent."
    )
    capabilities: List[AgentCapability] = Field(
        ..., description="List of capabilities the agent possesses."
    )
    battery_level: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        1.0, description="Current battery/energy level (0.0 to 1.0)."
    )
    health: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        1.0, description="Current health/integrity level (0.0 to 1.0)."
    )
    assigned_victim_id: Optional[UUID4] = Field(
        None, description="ID of the victim currently assigned to this agent."
    )
    current_path: List[Coordinate] = Field(
        [], description="List of coordinates representing the agent's current path."
    )
    risk_exposure_tolerance: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        0.7, description="Maximum risk exposure agent can tolerate."
    )


# --- Mission and Plan Models ---


class MissionStatus(str, Enum):
    """Status of an overall disaster response mission."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Mission(BaseModel):
    """Represents a disaster response mission."""

    model_config = ConfigDict(extra="forbid")
    id: UUID4 = Field(..., description="Unique identifier for the mission.")
    name: str = Field(..., description="Name or description of the mission.")
    status: MissionStatus = Field(
        MissionStatus.PENDING, description="Current status of the mission."
    )
    start_time: str = Field(
        ..., description="Timestamp when the mission started (ISO 8601 format)."
    )
    end_time: Optional[str] = Field(
        None, description="Timestamp when the mission ended (ISO 8601 format)."
    )
    environment_id: UUID4 = Field(
        ..., description="ID of the environment this mission operates in."
    )
    assigned_agent_ids: List[UUID4] = Field(
        [], description="IDs of agents participating in this mission."
    )
    victims_identified: List[UUID4] = Field(
        [], description="IDs of victims identified in this mission."
    )
    victims_rescued: List[UUID4] = Field(
        [], description="IDs of victims successfully rescued."
    )


class AgentTask(BaseModel):
    """Represents a single task for an agent within a plan."""

    model_config = ConfigDict(extra="forbid")
    type: str = Field(
        ..., description="Type of task (e.g., 'move', 'rescue', 'search')."
    )
    target_location: Optional[Coordinate] = Field(
        None, description="Target coordinate for the task."
    )
    victim_id: Optional[UUID4] = Field(
        None, description="Victim associated with the task, if any."
    )
    path_to_target: List[Coordinate] = Field(
        [], description="Planned path for the agent to reach the target."
    )
    expected_risk_exposure: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        0.0, description="Expected risk for this task."
    )
    estimated_time_seconds: PositiveInt = Field(
        ..., description="Estimated time to complete the task."
    )


class AgentPlan(BaseModel):
    """Represents a planned sequence of tasks for a single agent."""

    model_config = ConfigDict(extra="forbid")
    agent_id: UUID4 = Field(..., description="ID of the agent this plan is for.")
    tasks: List[AgentTask] = Field(
        ..., description="Ordered list of tasks for the agent."
    )
    total_estimated_time_seconds: PositiveInt = Field(
        ..., description="Total estimated time for the entire plan."
    )
    total_expected_risk: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Total expected risk for the entire plan."
    )


class Plan(BaseModel):
    """Represents a comprehensive disaster response plan for multiple agents."""

    model_config = ConfigDict(extra="forbid")
    id: UUID4 = Field(..., description="Unique identifier for the plan.")
    mission_id: UUID4 = Field(
        ..., description="ID of the mission this plan belongs to."
    )
    timestamp: str = Field(
        ..., description="Timestamp when the plan was generated (ISO 8601 format)."
    )
    agent_plans: List[AgentPlan] = Field(
        ..., description="Plans for each individual agent."
    )
    victims_to_rescue_order: List[UUID4] = Field(
        ..., description="Ordered list of victim IDs to be rescued."
    )
    overall_risk_score: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Overall risk score of the plan."
    )
    overall_efficiency_score: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Overall efficiency score of the plan."
    )


# --- Explainability Models ---


class ExplanationType(str, Enum):
    """Types of explanations provided by the LLM module."""

    VICTIM_PRIORITIZATION = "victim_prioritization"
    ROUTE_SELECTION = "route_selection"
    MISSION_SUMMARY = "mission_summary"
    TRADE_OFF_ANALYSIS = "trade_off_analysis"
    TASK_DECOMPOSITION = "task_decomposition"


class ExplainabilityOutput(BaseModel):
    """Structured output from the LLM Explainability Module."""

    model_config = ConfigDict(extra="forbid")
    explanation_id: UUID4 = Field(
        ..., description="Unique identifier for the explanation."
    )
    mission_id: UUID4 = Field(
        ..., description="ID of the mission related to this explanation."
    )
    explanation_type: ExplanationType = Field(
        ..., description="The type of explanation generated."
    )
    decision_context: Dict[str, Any] = Field(
        ..., description="The structured data that formed the basis of the decision."
    )
    human_readable_summary: str = Field(
        ...,
        description=(
            "A concise, human-readable summary of the decision "
            "and its rationale."
        ),
    ),
    structured_explanation_json: Dict[str, Any] = Field(
        ..., description="Detailed, structured explanation in JSON format."
    )
    timestamp: str = Field(
        ...,
        description="Timestamp when the explanation was generated (ISO 8601 format).",
    )


# --- Metrics Models ---


class MetricType(str, Enum):
    """Types of metrics tracked by the system."""

    TOTAL_RESCUE_TIME = "total_rescue_time"
    AGGREGATE_RISK_EXPOSURE = "aggregate_risk_exposure"
    AGENT_UTILIZATION = "agent_utilization"
    EFFICIENCY_INDEX = "efficiency_index"
    PREDICTED_LIVES_SAVED = "predicted_lives_saved"
    VICTIMS_RESCUED_COUNT = "victims_rescued_count"
    HAZARD_MITIGATED_COUNT = "hazard_mitigated_count"


class Metric(BaseModel):
    """Represents a single tracked metric."""

    model_config = ConfigDict(extra="forbid")
    name: MetricType = Field(..., description="The name of the metric.")
    value: float = Field(..., description="The value of the metric.")
    unit: Optional[str] = Field(
        None,
        description="The unit of measurement for the metric (e.g., 'seconds', '%').",
    )
    timestamp: str = Field(
        ..., description="Timestamp when the metric was recorded (ISO 8601 format)."
    )
    mission_id: Optional[UUID4] = Field(
        None, description="Associated mission ID, if applicable."
    )


class MetricsSummary(BaseModel):
    """A summary of key performance indicators and metrics
    for a mission or overall system.
    """

    model_config = ConfigDict(extra="forbid")
    mission_id: Optional[UUID4] = Field(
        None, description="ID of the mission the metrics pertain to."
    )
    total_rescue_time_seconds: Optional[PositiveInt] = Field(
        None, description="Total time taken for rescue operations."
    )
    average_agent_risk_exposure: Optional[Annotated[float, Field(ge=0.0, le=1.0)]] = (
        Field(None, description="Average risk exposure across all agents.")
    )
    agent_utilization_percentage: Optional[Annotated[float, Field(ge=0.0, le=1.0)]] = (
        Field(None, description="Percentage of time agents were active.")
    )
    efficiency_index: Optional[Annotated[float, Field(ge=0.0)]] = Field(
        None, description="Calculated efficiency index."
    )
    predicted_lives_saved: Optional[NonNegativeInt] = Field(
        None, description="Estimated number of lives saved."
    )
    victims_rescued_count: Optional[NonNegativeInt] = Field(
        None, description="Total number of victims rescued."
    )
    active_agents_count: Optional[NonNegativeInt] = Field(
        None, description="Number of agents actively involved."
    )
    # Add more business-facing KPIs as needed
    additional_metrics: Dict[str, Any] = Field(
        {}, description="Any additional, custom metrics."
    )


# --- Request and Response Models for API (examples) ---


class SimulateRequest(BaseModel):
    """Request model for initiating a disaster simulation."""

    model_config = ConfigDict(extra="forbid")
    map_size: PositiveInt = Field(
        50, description="Size of the square grid map (e.g., 50x50)."
    )
    hazard_intensity_factor: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        0.5, description="Overall intensity factor for hazard generation."
    )
    num_victims: NonNegativeInt = Field(
        10, description="Number of victims to generate."
    )
    num_agents: NonNegativeInt = Field(
        3, description="Number of rescue agents to deploy."
    )
    seed: Optional[int] = Field(
        None, description="Optional seed for reproducible environment generation."
    )


class SimulateResponse(BaseModel):
    """Response model after initiating a disaster simulation."""

    model_config = ConfigDict(extra="forbid")
    mission_id: UUID4 = Field(..., description="Unique ID of the initiated mission.")
    message: str = Field(
        "Simulation initiated successfully.", description="Status message."
    )


class PlanRequest(BaseModel):
    """Request model for generating a rescue plan."""

    model_config = ConfigDict(extra="forbid")
    mission_id: UUID4 = Field(..., description="The ID of the mission to plan for.")
    planning_objective: str = Field(
        "minimize_risk_exposure",
        description=(
            "Primary objective for planning (e.g., 'minimize_time', "
            "'minimize_risk_exposure', 'maximize_lives_saved')."
        ),
    )
    replan: bool = Field(
        False,
        description="Whether this is a re-planning request "
        "due to environmental changes.",
    )


class PlanResponse(BaseModel):
    """Response model containing the generated rescue plan."""

    model_config = ConfigDict(extra="forbid")
    plan_id: UUID4 = Field(..., description="Unique ID of the generated plan.")
    mission_id: UUID4 = Field(..., description="ID of the mission the plan belongs to.")
    agent_plans: List[AgentPlan] = Field(
        ..., description="Detailed plans for each agent."
    )
    victims_prioritized_order: List[UUID4] = Field(
        ..., description="Ordered list of victim IDs based on priority."
    )
    message: str = Field("Plan generated successfully.", description="Status message.")


class ExplanationRequest(BaseModel):
    """Request model for generating explanations."""

    model_config = ConfigDict(extra="forbid")
    mission_id: UUID4 = Field(
        ..., description="The ID of the mission to generate an explanation for."
    )
    explanation_type: ExplanationType = Field(
        ..., description="The type of explanation requested."
    )
    decision_id: Optional[UUID4] = Field(
        None, description="Optional ID of a specific decision to explain."
    )


class PrioritizationConfig(BaseModel):
    """Configuration for the victim prioritization scoring function."""

    model_config = ConfigDict(extra="forbid")
    severity_weight: float = Field(
        settings.PRIORITIZATION_SEVERITY_WEIGHT,
        ge=0.0,
        le=1.0,
        description="Weight for injury severity.",
    )
    time_sensitivity_weight: float = Field(
        settings.PRIORITIZATION_TIME_SENSITIVITY_WEIGHT,
        ge=0.0,
        le=1.0,
        description="Weight for time sensitivity (survival window).",
    )
    accessibility_risk_weight: float = Field(
        settings.PRIORITIZATION_ACCESSIBILITY_RISK_WEIGHT,
        ge=0.0,
        le=1.0,
        description="Weight for accessibility risk.",
    )
    num_agents_available_weight: float = Field(
        settings.PRIORITIZATION_NUM_AGENTS_AVAILABLE_WEIGHT,
        ge=0.0,
        le=1.0,
        description="Weight for number of agents available.",
    )

    # Thresholds for severity scaling
    severity_critical_score: float = settings.PRIORITIZATION_SEVERITY_CRITICAL_SCORE
    severity_severe_score: float = settings.PRIORITIZATION_SEVERITY_SEVERE_SCORE
    severity_moderate_score: float = settings.PRIORITIZATION_SEVERITY_MODERATE_SCORE
    severity_mild_score: float = settings.PRIORITIZATION_SEVERITY_MILD_SCORE

    # Other factors can be added here
    # e.g., "children_present_bonus": 0.2

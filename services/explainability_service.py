import datetime
import json
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.exceptions import (
    InvalidExplanationRequestException,
    MissionNotFoundException,
    ServiceInitializationException,
    VictimNotFoundException, # New import
    AgentNotFoundException, # New import
)
from explainability.llm_interface import LLMInterface, MockLLM
from infrastructure.mission_registry import MissionRegistry # Import the class
from models.models import (
    Agent,
    Coordinate,
    ExplainabilityOutput,
    ExplanationType,
    Mission,
    Plan,
    Victim,
)


class ExplainabilityService:
    """The Explainability Service integrates with LLMs.

    Generates human-readable and structured explanations for various ADRIE decisions.
    """
    def __init__(self, llm_interface: Optional[LLMInterface] = None, mission_registry: Optional[MissionRegistry] = None):
        """Initialize the ExplainabilityService.

        Args:
            llm_interface (Optional[LLMInterface]): An instance of an LLM interface.
                                                    Defaults to MockLLM if not provided.
            mission_registry (Optional[MissionRegistry]): An instance of the MissionRegistry.
        """
        self.llm = llm_interface if llm_interface else MockLLM()
        self.mission_registry = mission_registry

    async def generate_victim_prioritization_explanation(
        self,
        mission: Mission,
        victim: Victim,
        all_victims: List[Victim],
        decision_context: Dict[str, Any],
    ) -> ExplainabilityOutput:
        """Generate an explanation for why a specific victim was prioritized.

        Args:
            mission (Mission): The current mission object.
            victim (Victim): The victim that was prioritized.
            all_victims (List[Victim]): All victims in the current scenario for context.
            decision_context (Dict[str, Any]): Additional context for the decision.

        Returns:
            ExplainabilityOutput: The structured explanation output.

        """
        prompt = self._create_victim_prioritization_prompt(
            mission, victim, all_victims, decision_context
        )
        (
            human_readable_summary,
            structured_explanation,
        ) = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.VICTIM_PRIORITIZATION,
            decision_context=decision_context,
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp(),
        )

    async def generate_route_selection_explanation(
        self,
        mission: Mission,
        agent: Agent,
        plan_segment: List[Coordinate],  # The specific route segment being explained
        reasoning_context: Dict[str, Any],
    ) -> ExplainabilityOutput:
        """Generate an explanation for why a specific agent route was selected.

        Args:
            mission (Mission): The current mission object.
            agent (Agent): The agent whose route is being explained.
            plan_segment (List[Coordinate]): The specific path or segment to explain.
            reasoning_context (Dict[str, Any]): Context including risks,
                                                alternative paths considered, etc.

        Returns:
            ExplainabilityOutput: The structured explanation output.

        """
        prompt = self._create_route_selection_prompt(
            mission, agent, plan_segment, reasoning_context
        )
        (
            human_readable_summary,
            structured_explanation,
        ) = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.ROUTE_SELECTION,
            decision_context=reasoning_context,
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp(),
        )

    async def generate_mission_summary(
        self,
        mission: Mission,
        final_plan: Plan,
        metrics_summary: Dict[str, Any],
        key_decisions: List[Dict[str, Any]],
    ) -> ExplainabilityOutput:
        """Generate a human-readable summary for a completed mission.

        Args:
            mission (Mission): The completed mission object.
            final_plan (Plan): The final plan executed during the mission.
            metrics_summary (Dict[str, Any]): Summary of mission performance metrics.
            key_decisions (List[Dict[str, Any]]): List of critical decisions
                                                   made during the mission.

        Returns:
            ExplainabilityOutput: The structured explanation output.

        """
        prompt = self._create_mission_summary_prompt(
            mission, final_plan, metrics_summary, key_decisions
        )
        (
            human_readable_summary,
            structured_explanation,
        ) = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.MISSION_SUMMARY,
            decision_context={
                "mission": mission.model_dump(mode="json"),
                "final_plan": final_plan.model_dump(mode="json"),
                "metrics_summary": metrics_summary,
                "key_decisions": key_decisions,
            },
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp(),
        )

    async def generate_trade_off_explanation(
        self, mission: Mission, trade_off_context: Dict[str, Any]
    ) -> ExplainabilityOutput:
        """Generate an explanation for trade-offs made (e.g., high-risk vs high-severity).

        Args:
            mission (Mission): The current mission object.
            trade_off_context (Dict[str, Any]): Context describing the trade-off
                                                situation.

        Returns:
            ExplainabilityOutput: The structured explanation output.

        """
        prompt = self._create_trade_off_prompt(mission, trade_off_context)
        (
            human_readable_summary,
            structured_explanation,
        ) = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.TRADE_OFF_ANALYSIS,
            decision_context=trade_off_context,
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp(),
        )

    def _create_victim_prioritization_prompt(
        self,
        mission: Mission,
        victim: Victim,
        all_victims: List[Victim],
        decision_context: Dict[str, Any],
    ) -> str:
        """Create a detailed prompt for victim prioritization."""
        return (
            f"Explain why Victim ID {victim.id} at {victim.location.x},{victim.location.y} "
            f"was prioritized. Its injury severity is {victim.injury_severity}, "
            f"estimated survival window {victim.estimated_survival_window_minutes} minutes, "
            f"and current accessibility risk {victim.accessibility_risk:.2f}. "
            f"The calculated priority score was {victim.priority_score:.2f}. "
            f"Other victims in consideration had scores like {[(v.id, v.priority_score) for v in all_victims if v.id != victim.id][:3]}."
            f"Mission context: {mission.name} (ID: {mission.id}). "
            f"Decision factors: {json.dumps(decision_context)}"
        )

    def _create_route_selection_prompt(
        self,
        mission: Mission,
        agent: Agent,
        plan_segment: List[Coordinate],
        reasoning_context: Dict[str, Any],
    ) -> str:
        """Create a detailed prompt for route selection."""
        return (
            f"Explain why agent {agent.name} (ID: {agent.id}) was assigned the route "
            f"starting at {plan_segment[0].x},{plan_segment[0].y} to {plan_segment[-1].x},{plan_segment[-1].y}. "
            f"The agent's capabilities are {agent.capabilities}. "
            f"Risk along the path: {reasoning_context.get('path_risks', 'N/A')}. "
            f"Alternative routes considered: {reasoning_context.get('alternatives', 'N/A')}. "
            f"Mission context: {mission.name} (ID: {mission.id})."
        )

    def _create_mission_summary_prompt(
        self,
        mission: Mission,
        final_plan: Plan,
        metrics_summary: Dict[str, Any],
        key_decisions: List[Dict[str, Any]],
    ) -> str:
        """Create a detailed prompt for a mission summary."""
        return (
            f"Generate a human-readable summary for mission '{mission.name}' (ID: {mission.id}). "
            f"Status: {mission.status}. Start time: {mission.start_time}. "
            f"Victims rescued: {len(mission.victims_rescued)}. "
            f"Key metrics: {json.dumps(metrics_summary)}. "
            f"Overall plan risk: {final_plan.overall_risk_score:.2f}. "
            f"Key decisions during mission: {json.dumps(key_decisions)}. "
            "Focus on key outcomes, challenges, and agent performance."
        )

    def _create_trade_off_prompt(
        self, mission: Mission, trade_off_context: Dict[str, Any]
    ) -> str:
        """Create a detailed prompt for trade-off explanations."""
        return (
            f"Explain a critical trade-off decision made during mission '{mission.name}' (ID: {mission.id}). "
            f"The situation involved: {trade_off_context.get('situation', 'N/A')}. "
            f"Options considered: {trade_off_context.get('options', 'N/A')}. "
            f"The chosen option was {trade_off_context.get('chosen_option', 'N/A')} with rationale: {trade_off_context.get('rationale', 'N/A')}. "
            "Detail the ethical and operational implications of this choice."
        )

    def _get_current_timestamp(self) -> str:
        """Returns the current UTC timestamp in ISO 8601 format."""
        return datetime.datetime.utcnow().isoformat() + "Z"

    def reset(self) -> None:
        """Resets the explainability service's internal state if any."""
        print("ExplainabilityService reset.")

    async def get_explanation_output(
        self,
        mission_id: UUID,
        explanation_type: ExplanationType,
        decision_id: Optional[UUID] = None,
    ) -> ExplainabilityOutput:

        # Use self.mission_registry instead of importing a global one
        if not self.mission_registry:
            raise ServiceInitializationException(
                service_name="ExplainabilityService",
                detail="MissionRegistry not initialized for ExplainabilityService."
            )

        """Provides an explanation for critical decisions or a summary for a mission.
        - `explanation_type`: Type of explanation requested (e.g., VICTIM_PRIORITIZATION, ROUTE_SELECTION, MISSION_SUMMARY, TRADE_OFF_ANALYSIS).
        - `decision_id`: Optional ID of a specific decision to explain (e.g., victim ID for prioritization).
        """

        mission = await self.mission_registry.get_mission(mission_id)
        env_service = await self.mission_registry.get_environment_service(mission_id)

        # Placeholder for building decision context based on explanation_type
        decision_context: Dict[str, Any] = {}
        explanation_output: ExplainabilityOutput

        if explanation_type == ExplanationType.VICTIM_PRIORITIZATION:
            if not decision_id:
                raise InvalidExplanationRequestException(
                    detail="decision_id (victim ID) is required for victim prioritization explanation."
                )

            victim = env_service.victims.get(decision_id)
            if not victim:
                raise VictimNotFoundException(decision_id)  # Changed exception

            # Example context, would be richer with actual decision logic
            decision_context = {
                "victim_id": str(victim.id),
                "injury_severity": victim.injury_severity.value,
                "time_sensitivity": victim.time_since_incident_minutes,
                "survival_window": victim.estimated_survival_window_minutes,
                "accessibility_risk": victim.accessibility_risk,
                "priority_score": victim.priority_score,
            }
            explanation_output = await self.generate_victim_prioritization_explanation(
                mission, victim, env_service.get_all_victims(), decision_context
            )
        elif explanation_type == ExplanationType.MISSION_SUMMARY:
            mission_data = await self.mission_registry.get_mission_data(mission_id)
            current_plan = mission_data.get("current_plan")
            if not current_plan:
                raise MissionNotFoundException(
                    mission_id
                )  # Consider a more specific exception like PlanNotFoundException
            metrics_service = await self.mission_registry.get_metrics_service(mission_id)
            metrics_summary = await metrics_service.get_metrics_summary(
                mission
            )
            # key_decisions would be pulled from a log of decisions
            explanation_output = await self.generate_mission_summary(
                mission,
                current_plan,
                metrics_summary.model_dump(mode="json"),
                [],  # Empty list for key_decisions for now
            )
        elif explanation_type == ExplanationType.ROUTE_SELECTION:
            if not decision_id:
                raise InvalidExplanationRequestException(
                    detail="decision_id (agent ID or plan ID) is required for route selection explanation."
                )

            mission_data = await self.mission_registry.get_mission_data(mission_id)
            agent_service = mission_data["agent_service"]
            current_plan = mission_data.get("current_plan")

            if not current_plan:
                raise MissionNotFoundException(
                    mission_id
                )  # Consider PlanNotFoundException

            # Find the agent and its plan
            agent_plan = next(
                (ap for ap in current_plan.agent_plans if ap.agent_id == decision_id),
                None,
            )
            if not agent_plan or not agent_plan.tasks:
                raise InvalidExplanationRequestException(
                    detail=f"Agent plan for ID {decision_id} not found or has no tasks."
                )

            agent_obj = agent_service.get_agent(decision_id)
            if not agent_obj:
                raise AgentNotFoundException( # Changed exception
                    decision_id
                )
            # For simplicity, explain the first task's path
            first_task = agent_plan.tasks[0]
            plan_segment = (
                first_task.path_to_target
                if first_task.path_to_target
                else [agent_obj.current_location, first_task.target_location]
            )

            reasoning_context = {
                "agent_id": str(agent_obj.id),
                "task_type": first_task.type,
                "target_location": first_task.target_location.model_dump()
                if first_task.target_location
                else None,
                "expected_risk": first_task.expected_risk_exposure,
                # In a real system, this would include alternative paths considered, risk scores, etc.
            }
            explanation_output = await self.generate_route_selection_explanation(
                mission, agent_obj, plan_segment, reasoning_context
            )
        elif explanation_type == ExplanationType.TRADE_OFF_ANALYSIS:
            if not decision_id:
                trade_off_context = {
                    "situation": "Prioritizing high-risk, low-severity victim over low-risk, high-severity victim.",
                    "options_considered": [
                        "Rescue high-risk, low-severity",
                        "Rescue low-risk, high-severity",
                    ],
                    "chosen_option": "Rescue high-risk, low-severity",
                    "rationale": "Mitigating immediate environmental threat to agent safety was deemed paramount.",
                }
            else:
                trade_off_context = {
                    "situation": f"Trade-off related to decision ID {decision_id} was made.",
                    "details": "Specific details of the trade-off would be fetched here.",
                }

            explanation_output = await self.generate_trade_off_explanation(
                mission, trade_off_context
            )
        else:
            raise InvalidExplanationRequestException(
                detail=f"Unsupported explanation type: {explanation_type.value}"
            )

        return explanation_output

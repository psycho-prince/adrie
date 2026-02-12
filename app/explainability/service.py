"""
The Explainability Service integrates with LLMs to generate human-readable and structured
explanations for various ADRIE decisions.
"""

import json
from uuid import uuid4
from typing import Dict, Any, Tuple

from app.core.models import ExplanationType, ExplainabilityOutput, Coordinate, Agent, Victim, Mission, Plan
from app.explainability.interface import LLMInterface, MockLLM

class ExplainabilityService:
    """
    Service responsible for generating explanations using an underlying LLM.
    It formats prompts, calls the LLM, and processes its responses into
    structured ExplainabilityOutput.
    """

    def __init__(self, llm_interface: Optional[LLMInterface] = None):
        """
        Initializes the ExplainabilityService.

        Args:
            llm_interface (Optional[LLMInterface]): An instance of an LLM interface.
                                                    Defaults to MockLLM if not provided.
        """
        self.llm = llm_interface if llm_interface else MockLLM()

    async def generate_victim_prioritization_explanation(
        self,
        mission: Mission,
        victim: Victim,
        all_victims: List[Victim],
        decision_context: Dict[str, Any]
    ) -> ExplainabilityOutput:
        """
        Generates an explanation for why a specific victim was prioritized.

        Args:
            mission (Mission): The current mission object.
            victim (Victim): The victim that was prioritized.
            all_victims (List[Victim]): All victims in the current scenario for context.
            decision_context (Dict[str, Any]): Additional context for the decision.

        Returns:
            ExplainabilityOutput: The structured explanation output.
        """
        prompt = self._create_victim_prioritization_prompt(mission, victim, all_victims, decision_context)
        human_readable_summary, structured_explanation = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.VICTIM_PRIORITIZATION,
            decision_context=decision_context,
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp()
        )

    async def generate_route_selection_explanation(
        self,
        mission: Mission,
        agent: Agent,
        plan_segment: List[Coordinate], # The specific route segment being explained
        reasoning_context: Dict[str, Any]
    ) -> ExplainabilityOutput:
        """
        Generates an explanation for why a specific agent route was selected.

        Args:
            mission (Mission): The current mission object.
            agent (Agent): The agent whose route is being explained.
            plan_segment (List[Coordinate]): The specific path or segment to explain.
            reasoning_context (Dict[str, Any]): Context including risks, alternative paths considered, etc.

        Returns:
            ExplainabilityOutput: The structured explanation output.
        """
        prompt = self._create_route_selection_prompt(mission, agent, plan_segment, reasoning_context)
        human_readable_summary, structured_explanation = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.ROUTE_SELECTION,
            decision_context=reasoning_context,
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp()
        )

    async def generate_mission_summary(
        self,
        mission: Mission,
        final_plan: Plan,
        metrics_summary: Dict[str, Any],
        key_decisions: List[Dict[str, Any]]
    ) -> ExplainabilityOutput:
        """
        Generates a human-readable summary for a completed mission.

        Args:
            mission (Mission): The completed mission object.
            final_plan (Plan): The final plan executed during the mission.
            metrics_summary (Dict[str, Any]): Summary of mission performance metrics.
            key_decisions (List[Dict[str, Any]]): List of critical decisions made during the mission.

        Returns:
            ExplainabilityOutput: The structured explanation output.
        """
        prompt = self._create_mission_summary_prompt(mission, final_plan, metrics_summary, key_decisions)
        human_readable_summary, structured_explanation = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.MISSION_SUMMARY,
            decision_context={
                "mission": mission.model_dump(),
                "final_plan": final_plan.model_dump(),
                "metrics_summary": metrics_summary,
                "key_decisions": key_decisions
            },
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp()
        )

    async def generate_trade_off_explanation(
        self,
        mission: Mission,
        trade_off_context: Dict[str, Any]
    ) -> ExplainabilityOutput:
        """
        Generates an explanation for trade-offs made (e.g., high-risk vs high-severity).

        Args:
            mission (Mission): The current mission object.
            trade_off_context (Dict[str, Any]): Context describing the trade-off situation.

        Returns:
            ExplainabilityOutput: The structured explanation output.
        """
        prompt = self._create_trade_off_prompt(mission, trade_off_context)
        human_readable_summary, structured_explanation = await self.llm.generate_explanation(prompt)

        return ExplainabilityOutput(
            explanation_id=uuid4(),
            mission_id=mission.id,
            explanation_type=ExplanationType.TRADE_OFF_ANALYSIS,
            decision_context=trade_off_context,
            human_readable_summary=human_readable_summary,
            structured_explanation_json=structured_explanation,
            timestamp=self._get_current_timestamp()
        )

    def _create_victim_prioritization_prompt(
        self,
        mission: Mission,
        victim: Victim,
        all_victims: List[Victim],
        decision_context: Dict[str, Any]
    ) -> str:
        """Helper to create a detailed prompt for victim prioritization."""
        # This prompt would be much more detailed in a real system,
        # including all relevant factors from the victim and environment.
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
        reasoning_context: Dict[str, Any]
    ) -> str:
        """Helper to create a detailed prompt for route selection."""
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
        key_decisions: List[Dict[str, Any]]
    ) -> str:
        """Helper to create a detailed prompt for a mission summary."""
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
        self,
        mission: Mission,
        trade_off_context: Dict[str, Any]
    ) -> str:
        """Helper to create a detailed prompt for trade-off explanations."""
        return (
            f"Explain a critical trade-off decision made during mission '{mission.name}' (ID: {mission.id}). "
            f"The situation involved: {trade_off_context.get('situation', 'N/A')}. "
            f"Options considered: {trade_off_context.get('options', 'N/A')}. "
            f"The chosen option was {trade_off_context.get('chosen_option', 'N/A')} with rationale: {trade_off_context.get('rationale', 'N/A')}. "
            "Detail the ethical and operational implications of this choice."
        )

    def _get_current_timestamp(self) -> str:
        """Returns the current UTC timestamp in ISO 8601 format."""
        import datetime
        return datetime.datetime.utcnow().isoformat() + "Z"

    def reset(self) -> None:
        """Resets the explainability service's internal state if any."""
        print("ExplainabilityService reset.")

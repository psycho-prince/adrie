from __future__ import annotations

import json
from typing import Any, Dict, Optional

from loguru import logger

GEMINI_API_KEY: Optional[str] = None
GEMINI_MODEL_NAME: str = "gemini-2.0-flash-exp"


class GeminiPlanner:
    """Interface to Google's Gemini model for plan generation.

    Uses the Gemini API to generate a complete mission plan based on
    the provided scenario data.
    """

    def __init__(self) -> None:
        """Initialize the GeminiPlanner with API credentials.

        Note: This class requires the GEMINI_API_KEY environment variable to be set.
        """

        try:
            import google.generativeai as genai  # type: ignore[import-untyped]
        except ImportError as e:
            raise ImportError(
                "The 'google-generativeai' package is required for GeminiPlanner. "
                "Install it with: pip install google-generativeai"
            ) from e

        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        else:
            logger.warning(
                "GEMINI_API_KEY is not set. GeminiPlanner will not be able to generate plans."
            )

        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)

    def generate_plan(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a mission plan by sending the scenario data to the Gemini model.

        Args:
            scenario_data: A dictionary representing the disaster scenario, including
                           grid size, victims, hazards, and agents.

        Returns:
            A dictionary containing the generated plan, explanation, and metrics.
            Returns an error dictionary if the API call fails.
        """
        prompt = json.dumps(scenario_data, indent=2)

        logger.info("Generating plan with Gemini... This may take a moment.")

        try:
            response = self.model.generate_content(prompt)
            plan_data = json.loads(response.text)
            logger.success("Successfully generated and parsed plan from Gemini.")
            return plan_data
        except Exception as e:
            logger.error(f"Error communicating with Gemini API or parsing response: {e}")
            logger.error(f"Failed response text: {getattr(response, 'text', 'N/A')}")
            return {
                "error": "Failed to generate plan from Gemini.",
                "details": str(e),
            }


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Cannot run example: GEMINI_API_KEY is not set.")
    else:
        test_scenario = {
            "grid_size": [20, 20],
            "victims": [
                {"id": "v1", "x": 2, "y": 3, "risk": 0.9, "type": "drowning", "status": "unattended"},
                {"id": "v2", "x": 15, "y": 12, "risk": 0.6, "type": "injured", "status": "unattended"},
                {"id": "v3", "x": 8, "y": 18, "risk": 0.95, "type": "fire", "status": "unattended"},
            ],
            "hazards": [
                {"type": "flood", "area": [[0, 0], [5, 5]]},
                {"type": "fire_spread", "area": [[7, 15], [10, 20]]},
            ],
            "agents": [
                {"id": "A1", "type": "MedicalBot", "start_x": 0, "start_y": 0, "capacity": 1},
                {"id": "A2", "type": "FireBot", "start_x": 19, "start_y": 19, "capacity": 1},
            ],
        }

        planner = GeminiPlanner()
        generated_plan = planner.generate_plan(test_scenario)

        print("\n--- Gemini Generated Plan ---")
        print(json.dumps(generated_plan, indent=2))
        print("---------------------------")

        if "explanation" in generated_plan:
            print("\n--- Explanation ---")
            print(generated_plan["explanation"])
            print("-------------------")

        if "plan" in generated_plan:
            print("\n--- Plan Steps ---")
            for agent_plan in generated_plan["plan"]:
                print(
                    f"Agent {agent_plan['agent_id']} "
                    f"(Priority: {agent_plan['priority']}, ETA: {agent_plan['eta']}s):"
                )
                for step in agent_plan["steps"]:
                    if step["action"] == "move":
                        print(f"  - Move to {step['to']}")
                    elif step["action"] == "rescue":
                        print(f"  - Rescue victim {step['victim_id']}")
            print("-------------------")

        if "error" in generated_plan:
            print(f"\nError: {generated_plan['error']}")

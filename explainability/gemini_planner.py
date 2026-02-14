
import google.generativeai as genai
import os
import json
from typing import Dict, Any
from loguru import logger

# Configure the Gemini API key
# It's recommended to load this from an environment variable for security
try:
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)
except (ImportError, ValueError) as e:
    logger.warning(f"{e} - Gemini Planner will not be available.")
    GEMINI_API_KEY = None


class GeminiPlanner:
    """
    An AI-powered mission planner using Google Gemini for generating ethical,
    risk-optimized rescue plans for disaster response scenarios.
    """
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        if not GEMINI_API_KEY:
            raise ConnectionError("Gemini API key is not configured. Cannot initialize GeminiPlanner.")
        
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"},
            system_instruction="""
You are an elite disaster response AI coordinator powered by Gemini. Given: a disaster grid scenario (JSON format with size, victims, hazards, and agents). Your mission is to generate an ethical, risk-optimized multi-agent rescue plan.

**Priorities:**
1.  **Ethical Triage:** Prioritize victims at imminent risk (e.g., 'drowning', 'fire', 'collapse') above all else.
2.  **Risk Minimization:** Minimize total risk exposure for both victims and agents.
3.  **Efficiency:** Calculate the most efficient paths (e.g., using A*) to complete rescues as quickly as possible.

**Output Schema:**
You MUST output a strict JSON object. Do not output any other text or markdown. The JSON object must conform to this schema:
{
  "plan": [
    {
      "agent_id": "string",
      "steps": [
        {
          "action": "move",
          "to": [int, int]
        },
        {
          "action": "rescue",
          "victim_id": "string"
        }
      ],
      "priority": "string (e.g., 'High', 'Medium', 'Low')",
      "eta": "integer (seconds)"
    }
  ],
  "explanation": "A detailed, step-by-step chain-of-thought reasoning for the generated plan. Explain the ethical considerations, the priority of each agent's tasks, and the trade-offs made. Be verbose and transparent.",
  "estimated_total_time": "integer (seconds)",
  "risk_reduction_pct": "float"
}
"""
        )
        logger.info(f"Gemini Planner initialized with model: {model_name}")

    def generate_plan(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a mission plan by sending the scenario data to the Gemini model.

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
            # The response.text should be a JSON string based on the prompt
            plan_data = json.loads(response.text)
            logger.success("Successfully generated and parsed plan from Gemini.")
            return plan_data
        except Exception as e:
            logger.error(f"Error communicating with Gemini API or parsing response: {e}")
            logger.error(f"Failed response text: {getattr(response, 'text', 'N/A')}")
            return {
                "error": "Failed to generate plan from Gemini.",
                "details": str(e)
            }

# Example Usage (for testing)
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Cannot run example: GEMINI_API_KEY is not set.")
    else:
        test_scenario = {
            "grid_size": [20, 20],
            "victims": [
                {"id": "v1", "x": 2, "y": 3, "risk": 0.9, "type": "drowning", "status": "unattended"},
                {"id": "v2", "x": 15, "y": 12, "risk": 0.6, "type": "injured", "status": "unattended"},
                {"id": "v3", "x": 8, "y": 18, "risk": 0.95, "type": "fire", "status": "unattended"}
            ],
            "hazards": [
                {"type": "flood", "area": [[0,0], [5,5]]},
                {"type": "fire_spread", "area": [[7,15], [10,20]]}
            ],
            "agents": [
                {"id": "A1", "type": "MedicalBot", "start_x": 0, "start_y": 0, "capacity": 1},
                {"id": "A2", "type": "FireBot", "start_x": 19, "start_y": 19, "capacity": 1}
            ]
        }
        
        planner = GeminiPlanner()
        generated_plan = planner.generate_plan(test_scenario)
        
        print("
--- Gemini Generated Plan ---")
        print(json.dumps(generated_plan, indent=2))
        print("---------------------------
")

        if "explanation" in generated_plan:
            print("--- Explanation ---")
            print(generated_plan["explanation"])
            print("-------------------
")

        if "plan" in generated_plan:
            print("--- Plan Steps ---")
            for agent_plan in generated_plan["plan"]:
                print(f"Agent {agent_plan['agent_id']} (Priority: {agent_plan['priority']}, ETA: {agent_plan['eta']}s):")
                for step in agent_plan['steps']:
                    if step['action'] == 'move':
                        print(f"  - Move to {step['to']}")
                    elif step['action'] == 'rescue':
                        print(f"  - Rescue victim {step['victim_id']}")
            print("------------------
")
            
        if "error" in generated_plan:
            print(f"Error: {generated_plan['error']}")


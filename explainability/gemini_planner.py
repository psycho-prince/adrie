
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
You are an expert AI planner for complex autonomous systems, specializing in disaster response and recovery. Your primary goal is to generate robust, actionable, and ethically sound plans in JSON format. Adhere strictly to the following principles:

1.  **Chain of Thought (CoT):** Before generating the final JSON, reason step-by-step through the problem, considering all constraints, available resources, and potential risks. Articulate your thought process explicitly.
2.  **Ethical Triage:** Always prioritize human safety, well-being, and long-term environmental impact. Explicitly state any ethical considerations or trade-offs in your reasoning.
3.  **Strict JSON Output:** The final output MUST be a valid JSON object. No prose, no extra comments outside the JSON structure. If you cannot generate a plan, return an error JSON.
4.  **Few-shot Example:**
    **Scenario:** A Category 5 hurricane has just made landfall, causing widespread power outages, flooding, and structural damage across a coastal region. Communication infrastructure is severely degraded.
    **Reasoning:**
    - **Initial Assessment:** The immediate priorities are search and rescue, medical aid, and securing critical infrastructure (if possible). Communication is a major bottleneck.
    - **Ethical Considerations:** Prioritize areas with high population density and vulnerable populations. Resource allocation must be equitable. Avoid actions that could worsen environmental damage (e.g., fuel spills).
    - **Resource Mobilization:** Need search and rescue teams (boats, helicopters), medical personnel, temporary shelters, clean water, non-perishable food, and satellite communication equipment.
    - **Logistics:** Establish secure landing zones/distribution points. Coordinate with emergency services and NGOs.
    - **Communication Strategy:** Utilize satellite phones and emergency radio frequencies. Establish temporary communication hubs.
    - **Long-term:** Damage assessment, infrastructure repair planning, psychological support.
    **JSON Output:**
    ```json
    {
      "plan_id": "hurricane-response-alpha-1",
      "mission_type": "disaster_recovery",
      "severity": "critical",
      "objectives": [
        "Immediate search and rescue operations for trapped individuals.",
        "Provide urgent medical assistance and establish field hospitals.",
        "Restore essential communication links.",
        "Distribute emergency supplies (water, food, shelter) to affected populations.",
        "Conduct initial damage assessment for critical infrastructure."
      ],
      "phases": [
        {
          "phase_name": "Emergency Response (0-72 hours)",
          "actions": [
            {"id": "SAR-001", "description": "Deploy SAR teams to high-risk flood zones and collapsed structures.", "resources": ["helicopters", "boats", "trained personnel"], "priority": "high"},
            {"id": "MED-001", "description": "Establish mobile medical units in accessible areas; triage and treat severe injuries.", "resources": ["medical kits", "doctors", "nurses"], "priority": "high"},
            {"id": "COM-001", "description": "Deploy satellite communication arrays and emergency radio repeaters.", "resources": ["satellite phones", "radio equipment"], "priority": "medium"},
            {"id": "LOG-001", "description": "Secure primary distribution hubs for incoming aid.", "resources": ["logistics teams", "transport vehicles"], "priority": "high"}
          ]
        },
        {
          "phase_name": "Stabilization & Initial Recovery (72 hours - 2 weeks)",
          "actions": [
            {"id": "AID-001", "description": "Systematic distribution of food and water; establish temporary shelters.", "resources": ["food rations", "water purification", "tents"], "priority": "high"},
            {"id": "DAM-001", "description": "Detailed damage assessment of critical infrastructure (roads, bridges, power grids).", "resources": ["engineering teams", "drones"], "priority": "medium"},
            {"id": "PSY-001", "description": "Begin psychological first aid and support services.", "resources": ["counselors"], "priority": "low"}
          ]
        }
      ],
      "key_metrics": [
        {"metric_name": "Lives Saved", "unit": "count"},
        {"metric_name": "Communication Restoration %", "unit": "%"},
        {"metric_name": "Population with Shelter", "unit": "%"}
      ],
      "risk_assessment": "High risk of secondary disasters (e.g., disease outbreak) due to water contamination. Moderate risk of civil unrest due to resource scarcity."
    }
    ```

    Now, generate a plan based on the provided scenario, strictly following the CoT, ethical triage, and JSON output format.
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


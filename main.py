from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
import random # Needed for mock seed

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Hypothetical placeholder for simulation/plan/metrics logic
simulation_data: Dict[str, Any] = {}

@app.get("/")
async def read_root():
    return HTMLResponse("<h1>Adrie API is running. Visit /simulation for the interactive dashboard.</h1>")

@app.get("/simulation", response_class=HTMLResponse)
async def simulation_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adrie Simulation Dashboard</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <h1>Adrie Simulation Dashboard</h1>

            <section class="controls">
                <button id="start-sim-btn">Initiate New Simulation</button>
                <button id="generate-plan-btn" disabled>Generate Plan</button>
            </section>

            <section class="status-kpis">
                <h2>Simulation Status</h2>
                <p>Mission ID: <span id="mission-id">N/A</span></p>
                <p>Status: <span id="status">Idle</span></p>
                <div class="kpis">
                    <h3>Key Performance Indicators</h3>
                    <p>Success Rate: <span id="kpi-success-rate">N/A</span></p>
                    <p>Time Taken: <span id="kpi-time-taken">N/A</span></p>
                    <!-- Add more KPIs as needed -->
                </div>
            </section>

            <section class="plan-output">
                <h2>Generated Plan</h2>
                <pre id="plan-json">No plan generated yet.</pre>
            </section>
        </div>
        <script type="module" src="/static/main.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/simulate")
async def simulate_endpoint(request: Request):
    # In a real scenario, this would trigger a background task or service
    body = await request.json()
    map_size = body.get("map_size", 50)
    hazard_intensity_factor = body.get("hazard_intensity_factor", 0.5)
    num_victims = body.get("num_victims", 10)
    num_agents = body.get("num_agents", 3)
    seed = body.get("seed", random.randint(0, 100000)) # Use random if not provided

    mission_id = f"sim-{len(simulation_data) + 1}-{seed}"
    simulation_data[mission_id] = {
        "status": "running",
        "kpis": {"success_rate": 0, "time_taken": 0},
        "plan": None,
        "input_params": {
            "map_size": map_size,
            "hazard_intensity_factor": hazard_intensity_factor,
            "num_victims": num_victims,
            "num_agents": num_agents,
            "seed": seed
        }
    }
    return {"mission_id": mission_id, "status": "running", "message": "Simulation initiated with parameters."}

@app.get("/metrics")
async def get_metrics_endpoint(mission_id: str):
    if mission_id not in simulation_data:
        return {"error": "Mission ID not found"}, 404
    
    current_status = simulation_data[mission_id]["status"]
    current_kpis = simulation_data[mission_id]["kpis"]

    # Simulate progress
    if current_status == "running":
        import random
        current_kpis["success_rate"] = round(min(1.0, current_kpis["success_rate"] + random.uniform(0.03, 0.08)), 2)
        current_kpis["time_taken"] = round(current_kpis["time_taken"] + random.randint(10, 30), 0) # Simulate longer time
        if current_kpis["success_rate"] >= 0.95 and current_kpis["time_taken"] >= 100: # Simulate completion with a bit more logic
            simulation_data[mission_id]["status"] = "completed"
            
    return {"mission_id": mission_id, "status": simulation_data[mission_id]["status"], "kpis": simulation_data[mission_id]["kpis"]}

@app.post("/plan/{mission_id}") # Changed to accept mission_id in path
async def generate_plan_endpoint(mission_id: str, request: Request):
    if not mission_id or mission_id not in simulation_data:
        return {"error": "Invalid Mission ID"}, 400

    body = await request.json()
    planning_objective = body.get("planning_objective", "minimize_risk_exposure")
    replan = body.get("replan", False)

    # Mock plan generation
    if simulation_data[mission_id]["plan"] is None or replan:
        simulation_data[mission_id]["plan"] = {
            "mission": mission_id,
            "objective": planning_objective,
            "description": f"This is a mock plan generated for simulation {mission_id} with objective: {planning_objective}.",
            "steps": [
                {"step_number": 1, "action": "Prioritize highest risk victims", "status": "completed"},
                {"step_number": 2, "action": "Formulate strategy based on real-time data", "status": "in_progress"},
                {"step_number": 3, "action": "Execute primary actions for extraction", "status": "pending"}
            ],
            "ethical_review": "Plan prioritizes highest risk victims first, minimizing overall casualties. Trade-offs include longer travel times for lower-risk individuals."
        }
    return {"mission_id": mission_id, "plan": simulation_data[mission_id]["plan"]}

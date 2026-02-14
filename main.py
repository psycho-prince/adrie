from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Hypothetical placeholder for simulation/plan/metrics logic
# In a real app, these would interact with your core/services
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
    # For now, let's mock some data
    body = await request.json()
    mission_id = f"sim-{len(simulation_data) + 1}"
    simulation_data[mission_id] = {
        "status": "running",
        "kpis": {"success_rate": 0, "time_taken": 0},
        "plan": None,
        "input_params": body # Store input parameters if any
    }
    return {"mission_id": mission_id, "status": "running", "message": "Simulation initiated."}

@app.get("/metrics")
async def get_metrics_endpoint(mission_id: str):
    # Mock metrics update
    if mission_id not in simulation_data:
        return {"error": "Mission ID not found"}, 404
    
    current_status = simulation_data[mission_id]["status"]
    current_kpis = simulation_data[mission_id]["kpis"]

    # Simulate progress
    if current_status == "running":
        import random
        current_kpis["success_rate"] = round(min(1.0, current_kpis["success_rate"] + random.uniform(0.05, 0.15)), 2)
        current_kpis["time_taken"] = round(current_kpis["time_taken"] + random.randint(5, 20), 0)
        if current_kpis["success_rate"] >= 0.9: # Simulate completion
            simulation_data[mission_id]["status"] = "completed"
            
    return {"mission_id": mission_id, "status": simulation_data[mission_id]["status"], "kpis": simulation_data[mission_id]["kpis"]}

@app.post("/plan")
async def generate_plan_endpoint(request: Request):
    # In a real scenario, this would use the gemini_planner.py logic
    body = await request.json()
    mission_id = body.get("mission_id")
    if not mission_id or mission_id not in simulation_data:
        return {"error": "Invalid Mission ID"}, 400

    # Mock plan generation
    if simulation_data[mission_id]["plan"] is None:
        simulation_data[mission_id]["plan"] = {
            "mission": mission_id,
            "description": "This is a mock plan generated for the simulation.",
            "steps": [
                {"step_number": 1, "action": "Analyze initial conditions", "status": "completed"},
                {"step_number": 2, "action": "Formulate strategy based on KPIs", "status": "in_progress"},
                {"step_number": 3, "action": "Execute primary actions", "status": "pending"}
            ],
            "ethical_review": "Passed with minor concerns regarding resource allocation."
        }
    return {"mission_id": mission_id, "plan": simulation_data[mission_id]["plan"]}

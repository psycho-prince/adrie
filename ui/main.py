"""
Streamlit UI for ADRIE - Autonomous Disaster Response Intelligence Engine.
Provides a simple interface to interact with the FastAPI backend.
"""

import streamlit as st
import httpx
import json
from typing import Dict, Any, List
from uuid import UUID

# Assuming the FastAPI backend runs on localhost:8000
API_BASE_URL = "http://localhost:8000"

st.set_page_config(layout="wide", page_title="ADRIE UI")

st.title("ADRIE: Autonomous Disaster Response Intelligence Engine")
st.markdown("---")

# --- Session State Initialization ---
if "mission_id" not in st.session_state:
    st.session_state.mission_id = None
if "current_simulation_details" not in st.session_state:
    st.session_state.current_simulation_details = {}
if "current_plan_details" not in st.session_state:
    st.session_state.current_plan_details = {}
if "active_agent_ids" not in st.session_state:
    st.session_state.active_agent_ids = []
if "identified_victim_ids" not in st.session_state:
    st.session_state.identified_victim_ids = []

# --- Helper Functions for API Calls ---
async def call_api(method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generic function to call the FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            if method.lower() == "post":
                response = await client.post(url, json=json_data)
            elif method.lower() == "get":
                response = await client.get(url)
            else:
                st.error(f"Unsupported HTTP method: {method}")
                return {"error": "Unsupported HTTP method"}

            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except httpx.HTTPStatusError as e:
            st.error(f"API Error {e.response.status_code}: {e.response.text}")
            return {"error": f"API Error: {e.response.text}"}
        except httpx.RequestError as e:
            st.error(f"Network Error: {e}")
            return {"error": f"Network Error: {e}"}

# --- Sidebar for Navigation/Actions ---
st.sidebar.header("Actions")
selected_action = st.sidebar.radio(
    "Choose an action:",
    ("Simulate Disaster", "Generate Plan", "View Metrics", "Get Explanation")
)
st.sidebar.markdown("---")

if st.session_state.mission_id:
    st.sidebar.info(f"Active Mission ID: `{st.session_state.mission_id}`")
else:
    st.sidebar.warning("No active mission. Start a simulation!")

# --- Main Content Area ---

if selected_action == "Simulate Disaster":
    st.header("1. Initiate Disaster Simulation")

    with st.form("simulate_form"):
        map_size = st.number_input("Map Size (e.g., 50 for 50x50 grid)", min_value=10, max_value=200, value=50)
        hazard_intensity_factor = st.slider("Hazard Intensity Factor", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
        num_victims = st.number_input("Number of Victims", min_value=1, max_value=50, value=10)
        num_agents = st.number_input("Number of Agents", min_value=1, max_value=10, value=3)
        seed = st.number_input("Random Seed (optional, for reproducibility)", value=None, format="%d")
        
        simulate_submitted = st.form_submit_button("Start Simulation")

    if simulate_submitted:
        st.session_state.mission_id = None # Clear previous mission
        st.session_state.current_simulation_details = {}
        st.session_state.current_plan_details = {}
        st.session_state.active_agent_ids = []
        st.session_state.identified_victim_ids = []

        simulation_request = {
            "map_size": map_size,
            "hazard_intensity_factor": hazard_intensity_factor,
            "num_victims": num_victims,
            "num_agents": num_agents,
        }
        if seed is not None:
            simulation_request["seed"] = seed

        with st.spinner("Initiating simulation..."):
            response = await call_api("post", "/simulate", simulation_request)
            if "mission_id" in response:
                st.session_state.mission_id = UUID(response["mission_id"])
                st.success(f"Simulation started! Mission ID: `{st.session_state.mission_id}`")
                st.session_state.current_simulation_details = response
                
                # Fetch initial agents and victims for display (requires new API endpoints or enhanced /simulate)
                # For now, let's assume we can get this info directly from the environment engine within API
                # This needs to be better handled in the actual API design.
                # Placeholder for direct API calls to get agents/victims
                # If the API doesn't expose these directly after simulate, we'd need to mock or extend.
                st.session_state.active_agent_ids = [f"Agent-{i+1}" for i in range(num_agents)] # Mock
                st.session_state.identified_victim_ids = [f"Victim-{i+1}" for i in range(num_victims)] # Mock


            else:
                st.error("Failed to start simulation.")
    
    if st.session_state.mission_id:
        st.subheader("Current Simulation Details")
        st.json(st.session_state.current_simulation_details)
        st.write(f"Map Size: {map_size}x{map_size}")
        st.write(f"Hazards Intensity: {hazard_intensity_factor}")
        st.write(f"Number of Victims: {num_victims}")
        st.write(f"Number of Agents: {num_agents}")


elif selected_action == "Generate Plan":
    st.header("2. Generate Rescue Plan")

    if not st.session_state.mission_id:
        st.warning("Please initiate a simulation first.")
    else:
        with st.form("plan_form"):
            planning_objective = st.selectbox(
                "Planning Objective:",
                ("minimize_risk_exposure", "minimize_time", "maximize_lives_saved"),
                help="Select the primary objective for the planning algorithm."
            )
            replan = st.checkbox("Re-plan (if environmental changes occurred)", value=False)
            plan_submitted = st.form_submit_button("Generate Plan")

        if plan_submitted:
            plan_request = {
                "planning_objective": planning_objective,
                "replan": replan
            }
            with st.spinner(f"Generating plan for mission `{st.session_state.mission_id}`..."):
                response = await call_api("post", f"/plan/{st.session_state.mission_id}", plan_request)
                if "plan_id" in response:
                    st.success(f"Plan generated! Plan ID: `{response['plan_id']}`")
                    st.session_state.current_plan_details = response
                else:
                    st.error("Failed to generate plan.")
        
        if st.session_state.current_plan_details:
            st.subheader("Current Plan Details")
            st.json(st.session_state.current_plan_details)
            st.write(f"Total Agents in Plan: {len(st.session_state.current_plan_details.get('agent_plans', []))}")
            st.write(f"Victims Prioritized Order: {st.session_state.current_plan_details.get('victims_prioritized_order', [])}")
            # Visualizations would go here (heatmap, agent routes)

elif selected_action == "View Metrics":
    st.header("3. View Mission Metrics")

    if not st.session_state.mission_id:
        st.warning("No active mission to view metrics for.")
    else:
        if st.button(f"Fetch Metrics for Mission `{st.session_state.mission_id}`"):
            with st.spinner("Fetching metrics..."):
                response = await call_api("get", f"/metrics/{st.session_state.mission_id}")
                if "error" not in response:
                    st.success("Metrics fetched successfully!")
                    st.json(response)
                else:
                    st.error("Failed to fetch metrics.")

elif selected_action == "Get Explanation":
    st.header("4. Get Explainable AI Output")

    if not st.session_state.mission_id:
        st.warning("No active mission to get explanations for.")
    else:
        explanation_type = st.selectbox(
            "Select Explanation Type:",
            ("VICTIM_PRIORITIZATION", "MISSION_SUMMARY", "ROUTE_SELECTION", "TRADE_OFF_ANALYSIS"),
            help="Choose the type of decision or event to explain."
        )
        decision_id_str = st.text_input("Enter Decision ID (e.g., Victim ID for prioritization, optional)", value="")
        decision_id = UUID(decision_id_str) if decision_id_str else None

        if st.button(f"Get Explanation for Mission `{st.session_state.mission_id}`"):
            endpoint = f"/explain/{st.session_state.mission_id}/{explanation_type}"
            params = {}
            if decision_id:
                params["decision_id"] = str(decision_id) # API expects string UUID

            with st.spinner(f"Generating explanation for {explanation_type} ..."):
                # For GET requests with query parameters, httpx.AsyncClient().get(url, params=params)
                # However, the call_api currently only supports POST with json_data or GET without params.
                # Let's adjust call_api or directly call httpx for explanation.
                # For now, will use the json_data for simplicity assuming the API handles it as body/params
                response = {}
                try:
                    full_url = f"{API_BASE_URL}{endpoint}"
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(full_url, params=params)
                        resp.raise_for_status()
                        response = resp.json()
                except httpx.HTTPStatusError as e:
                    st.error(f"API Error {e.response.status_code}: {e.response.text}")
                    response = {"error": f"API Error: {e.response.text}"}
                except httpx.RequestError as e:
                    st.error(f"Network Error: {e}")
                    response = {"error": f"Network Error: {e}"}

                if "error" not in response:
                    st.success("Explanation generated!")
                    st.subheader("Human-Readable Summary:")
                    st.write(response.get("human_readable_summary", "No summary available."))
                    st.subheader("Structured Explanation (JSON):")
                    st.json(response.get("structured_explanation_json", {}))
                else:
                    st.error("Failed to get explanation.")

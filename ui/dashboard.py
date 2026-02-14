
import streamlit as st
import requests
import pandas as pd
import time
from typing import Dict, Any

# Assuming visualizer is in the same directory or accessible
from visualizer import render_simulation_grid, create_empty_grid
from explainability.gemini_planner import GeminiPlanner

# --- Configuration ---
st.set_page_config(layout="wide", page_title="ADRIE Mission Control")
API_BASE_URL = "https://adrie-api.onrender.com"  # Use the deployed Render API
# API_BASE_URL = "http://127.0.0.1:8000" # Use for local API testing

# --- Helper Functions ---
def get_api_data(endpoint: str) -> Dict[str, Any]:
    """Fetches data from the FastAPI backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return {}

def post_api_data(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Posts data to the FastAPI backend."""
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return {}

# --- App State Management ---
if 'mission_data' not in st.session_state:
    st.session_state.mission_data = None
if 'gemini_plan' not in st.session_state:
    st.session_state.gemini_plan = None
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False

# --- Sidebar ---
with st.sidebar:
    st.title("ADRIE")
    st.markdown("Autonomous Disaster Response & Intelligence Engine")
    st.info("**Startup Pitch:** In the chaos of disaster, every second counts. ADRIE uses AI to coordinate rescue robots, creating life-saving plans in moments. We replace confusion with clarity, turning first responders into super-responders. ADRIE is the future of emergency management.")
    
    st.header("Mission Controls")
    if st.button("Load New Disaster Scenario", key="load"):
        with st.spinner("Requesting new disaster scenario from ADRIE API..."):
            st.session_state.mission_data = get_api_data("simulate")
            st.session_state.gemini_plan = None # Reset plan
            st.session_state.simulation_running = False

    if st.session_state.mission_data:
        st.success("Scenario Loaded!")
        
        if st.button("Generate Plan with Gemini", key="plan"):
            with st.spinner("🛰️ Calling Gemini for an optimal rescue plan... This is advanced AI, it might take a moment!"):
                try:
                    planner = GeminiPlanner()
                    # Prepare data for Gemini
                    scenario_for_gemini = {
                        "grid_size": st.session_state.mission_data.get('grid_size'),
                        "victims": st.session_state.mission_data.get('victims', []),
                        "hazards": st.session_state.mission_data.get('hazards', []),
                        "agents": st.session_state.mission_data.get('agents', []),
                    }
                    st.session_state.gemini_plan = planner.generate_plan(scenario_for_gemini)
                except Exception as e:
                    st.error(f"Failed to initialize or run Gemini Planner: {e}")

    if st.session_state.gemini_plan:
        if st.button("Run Simulation Step", key="step"):
            with st.spinner("Running one step of the simulation..."):
                step_response = post_api_data(f"simulate/{st.session_state.mission_data['mission_id']}/step", {})
                if step_response and "error" not in step_response:
                    # Update the state of agents and victims from the simulation step response
                    st.session_state.mission_data['agents'] = step_response.get('agents', st.session_state.mission_data['agents'])
                    st.session_state.mission_data['victims'] = step_response.get('victims', st.session_state.mission_data['victims'])
                    st.success(f"Simulation step {step_response.get('step')} complete.")
                else:
                    st.error("Failed to run simulation step.")

# --- Main Dashboard ---
st.header("Mission Dashboard")

# Create columns for layout
col_viz, col_metrics = st.columns([3, 1])

with col_viz:
    st.subheader("Live Simulation Grid")
    viz_placeholder = st.empty()

    if st.session_state.mission_data:
        # Initial Render
        fig = render_simulation_grid(
            grid_size=st.session_state.mission_data['grid_size'],
            victims=st.session_state.mission_data['victims'],
            agents=st.session_state.mission_data['agents'],
            hazards=st.session_state.mission_data['hazards'],
            plan=st.session_state.gemini_plan
        )
        viz_placeholder.plotly_chart(fig, use_container_width=True)
    else:
        # Show empty grid
        fig = create_empty_grid((20, 20))
        viz_placeholder.plotly_chart(fig, use_container_width=True)


with col_metrics:
    st.subheader("Mission KPIs")
    if st.session_state.mission_data:
        metrics = st.session_state.mission_data.get('metrics', {})
        st.metric("Victims Detected", len(st.session_state.mission_data.get('victims', [])))
        st.metric("Agents Deployed", len(st.session_state.mission_data.get('agents', [])))
        st.metric("Avg. Risk Level", f"{metrics.get('average_risk', 0):.2%}")
        st.metric("Est. Time to Evac", f"{metrics.get('estimated_time_to_evac', 0) / 60:.1f} min")
    else:
        st.info("Load a scenario to view KPIs.")

# --- Gemini Plan Explanation Section ---
if st.session_state.gemini_plan:
    st.header("Gemini-Powered Rescue Plan")
    if "error" in st.session_state.gemini_plan:
        st.error(f"**Plan Generation Failed:** {st.session_state.gemini_plan.get('details')}")
    else:
        with st.expander("Show Gemini's Plan & Reasoning", expanded=True):
            explanation = st.session_state.gemini_plan.get("explanation", "No explanation provided.")
            st.info(f"**Gemini's Reasoning:** {explanation}")
            
            st.subheader("Agent Tasking")
            plan_df = []
            for p in st.session_state.gemini_plan.get('plan', []):
                plan_df.append({
                    "Agent ID": p.get('agent_id'),
                    "Priority": p.get('priority'),
                    "ETA (s)": p.get('eta'),
                    "Task Count": len(p.get('steps', []))
                })
            st.table(pd.DataFrame(plan_df))
            
            st.subheader("Raw Plan Data")
            st.json(st.session_state.gemini_plan)

# --- Instructions ---
st.info(
    """
    **How to use:**
    1.  Click **'Load New Disaster Scenario'** to get a random simulation from the backend.
    2.  The grid will show victims (red 'x'), agents (blue circles), and hazards (shaded areas).
    3.  Click **'Generate Plan with Gemini'** to have the AI create and explain a rescue strategy.
    4.  The agent paths and the AI's reasoning will appear.
    """
)

# ADRIE: Autonomous Disaster Response Intelligence Engine

## Table of Contents
1. [Introduction](#introduction)
2. [System Objective](#system-objective)
3. [Architecture Overview](#architecture-overview)
4. [Core Intelligence Modules](#core-intelligence-modules)
5. [LLM Explainability Module](#llm-explainability-module)
6. [API Layer](#api-layer)
7. [UI Layer](#ui-layer)
8. [Metrics & Business KPIs](#metrics--business-kpis)
9. [Installation](#installation)
10. [Usage](#usage)
11. [Running Tests](#running-tests)
12. [API Examples](#api-examples)
13. [Code Quality & Standards](#code-quality--standards)
14. [Contributing](#contributing)
15. [License](#license)

## 1. Introduction
The Autonomous Disaster Response Intelligence Engine (ADRIE) is a production-ready AI system designed to act as a scalable enterprise-grade intelligence layer for robotics disaster response. It focuses on risk-aware, multi-agent planning in dynamic disaster environments to optimize rescue operations and provide transparent, explainable decisions.

## 2. System Objective
ADRIE aims to:
- Simulate dynamic disaster grid environments with evolving hazards.
- Detect and prioritize victims based on ethical considerations and urgency.
- Generate risk-weighted optimal plans for multiple rescue agents.
- Coordinate agents to avoid collisions and resolve route conflicts.
- Utilize LLM-based reasoning for task decomposition, ethical prioritization explanations, and human-readable mission briefings.
- Provide explainable AI outputs for every decision made.
- Track performance metrics and business KPIs to assess operational efficiency and impact.

## 3. Architecture Overview
ADRIE is built with a clean, modular, and scalable architecture, adhering to Clean Architecture and SOLID principles. It's designed as a deployable AI platform using Python 3.11+, FastAPI backend, Pydantic models, and an asynchronous architecture where appropriate.

**Project Structure:**
```
adrie/
├── app/                  # Core application logic
│   ├── core/             # Shared models, utilities, and common interfaces
│   ├── environment/      # Disaster environment simulation and hazard modeling
│   ├── risk/             # Risk assessment and propagation
│   ├── agents/           # Rescue agent definitions and behaviors
│   ├── planner/          # Path planning and multi-objective optimization
│   ├── prioritization/   # Victim prioritization logic
│   ├── explainability/   # LLM-based explanation generation
│   ├── metrics/          # Performance tracking and KPI calculation
│   └── api/              # FastAPI application and endpoint definitions
├── ui/                   # User Interface (Streamlit or React)
├── tests/                # Unit and integration tests
├── configs/              # Configuration files (.env, config.py)
├── logs/                 # Structured log outputs
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── judging_alignment.md  # Alignment with judging criteria
└── .env.example          # Example environment variables
```

## 4. Core Intelligence Modules

### 4.1. Environment Engine
-   Procedural disaster map generation.
-   Dynamic hazard intensity modeling (fire, collapse, flood).
-   Configurable grid sizes.
-   Real-time risk recalculation based on environmental changes.

### 4.2. Risk Modeling Layer
-   Hazard weight normalization.
-   Probabilistic collapse modeling.
-   Risk propagation to adjacent nodes, influencing path planning.

### 4.3. Multi-Agent Coordination Engine
-   Manages multiple rescue agents.
-   Task allocation via auction-based or heuristic models.
-   Collision avoidance mechanisms.
-   Route conflict resolution strategies.

### 4.4. Planning Engine
-   Risk-weighted A* algorithm for pathfinding.
-   Multi-objective optimization considering time, risk exposure, and energy cost.
-   Dynamic re-planning capabilities in response to changing hazards or new information.

### 4.5. Victim Prioritization Model
-   A configurable and extensible scoring function.
-   Incorporates injury severity, time sensitivity, estimated survival window, and accessibility risk.

## 5. LLM Explainability Module
An abstract interface layer for LLM integration, allowing for flexible model provider swapping. The LLM is used to:
-   Explain the rationale behind victim prioritization decisions.
-   Justify selected agent routes.
-   Generate human-readable mission summaries.
-   Describe trade-offs (e.g., risk vs. severity) in decision-making.
-   Implemented via an `ExplainabilityService` class that accepts structured decision data and generates structured JSON explanations and human-readable summaries.

## 6. API Layer
Built with FastAPI, offering robust and documented endpoints:
-   `POST /simulate`: Initiate a disaster simulation.
-   `POST /plan`: Request a rescue plan for agents.
-   `GET /metrics`: Retrieve operational metrics and KPIs.
-   `GET /explain/{mission_id}`: Get explainable AI outputs for specific missions.
All responses are structured JSON, adhering to Pydantic models, with automatic OpenAPI documentation.

## 7. UI Layer
A simple, professional user interface to visualize and interact with ADRIE. Currently planned with Streamlit for rapid prototyping:
-   Heatmap visualization of disaster environment and hazards.
-   Overlay of agent routes and positions.
-   Priority table for victims.
-   Metrics dashboard for real-time monitoring of KPIs.

## 8. Metrics & Business KPIs
ADRIE tracks critical performance indicators:
-   Total rescue time.
-   Aggregate risk exposure for agents and missions.
-   Agent utilization rates.
-   Overall efficiency index.
-   Predicted lives saved (a key business-facing metric).
A dedicated endpoint provides a business-facing summary of these metrics.

## 9. Installation

### Prerequisites
-   Python 3.11+
-   `pip` (Python package installer)

### Steps
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/adrie.git
    cd adrie
    ```
    *(Note: Replace `https://github.com/your-repo/adrie.git` with the actual repository URL once available)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy the example environment file and populate it with your specific settings (e.g., API keys for LLM providers).
    ```bash
    cp .env.example .env
    # Open .env and fill in details
    ```

## 10. Usage

### Running the FastAPI Backend
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```
The API documentation will be available at `http://127.0.0.1:8000/docs`.

### Running the Streamlit UI (Placeholder)
*(This section will be detailed once the UI is implemented)*
```bash
streamlit run ui/main.py
```

## 11. Running Tests
ADRIE uses `pytest` for unit and integration testing.

```bash
pytest tests/
```

## 12. API Examples

### Simulate Disaster
```bash
curl -X POST "http://localhost:8000/simulate" -H "Content-Type: application/json" -d '{
  "map_size": 50,
  "hazard_intensity": 0.7,
  "num_victims": 10,
  "num_agents": 3
}'
```

### Request Plan
```bash
curl -X POST "http://localhost:8000/plan" -H "Content-Type: application/json" -d '{
  "mission_id": "some_simulation_id",
  "planning_params": {
    "objective": "minimize_risk_exposure"
  }
}'
```

### Get Metrics
```bash
curl -X GET "http://localhost:8000/metrics"
```

### Get Explanation
```bash
curl -X GET "http://localhost:8000/explain/your_mission_id"
```

## 13. Code Quality & Standards
-   **Clean Architecture & SOLID Principles:** Enforced throughout the codebase.
-   **Strict Typing:** All Python code uses comprehensive type hints.
-   **Docstrings:** Every module, class, and function includes clear docstrings.
-   **Separation of Concerns:** Distinct modules handle specific functionalities.
-   **Production Logging:** Structured logging implemented for traceability and debugging.
-   **Error Handling:** Robust error handling mechanisms.
-   **Async where appropriate:** Leveraging Python's `asyncio` for I/O bound operations.
-   **Configuration:** Environment-specific settings managed via `.env` files and a central `config.py`.

## 14. Contributing
Contributions are welcome! Please refer to the `CONTRIBUTING.md` (to be created) for guidelines.

## 15. License
This project is licensed under the MIT License. See the `LICENSE` (to be created) file for details.

# ADRIE — Autonomous Disaster Response Intelligence Engine
**From AI-Powered Plans to Real-Time 3D Simulation: The Future of Coordinated Rescue.**

---

ADRIE is not just a disaster response tool; it's a strategic AI engine designed to bring order to chaos. In the critical moments after a disaster, every second counts. ADRIE transforms response operations by generating risk-aware, optimized multi-agent rescue plans and visualizing them in a live, interactive 3D environment. We're building the "digital twin" for disaster sites, enabling commanders to make intelligent, data-driven decisions that save lives.

[![ADRIE Simulation UI](https://i.imgur.com/your-image-url.png)](https://adrie-api.onrender.com/simulation) 
*(

### 🚀 The Vision: From API to Action

While many systems can *plan*, ADRIE *shows*. Our powerful FastAPI backend is complemented by a dynamic **3D simulation built with Three.js**. This isn't just a feature—it's the core of our vision.

*   **For Commanders:** See the disaster site, understand the risks, and watch the rescue plan unfold in real-time.
*   **For AI Researchers:** A powerful testbed for multi-agent coordination and pathfinding algorithms.
*   **For Hackathon Judges:** A tangible, "wow-factor" demonstration that goes beyond a conceptual API.

---

### 🏆 Hackathon Impact Statement

**ADRIE is a top-5 contender because it combines technical depth, a clear business case, and profound human impact.**

*   **Business Impact**: The global market for disaster response robotics is projected to exceed **$25 billion by 2028**. ADRIE is positioned as an enterprise-grade "mission control" software for this rapidly growing industry. Our modular architecture allows for integration with various hardware (drones, rovers) and a SaaS-based revenue model for emergency services, government agencies, and private security firms.

*   **AI Innovation**: ADRIE is more than a simple pathfinding tool. It's a multi-layered AI system:
    1.  **Risk-Weighted A* Algorithm**: For intelligent, risk-aware pathfinding.
    2.  **Configurable Prioritization Models**: To make ethical and effective decisions on victim rescue order.
    3.  **LLM-Powered Explainability**: To provide human-readable justifications for complex AI decisions (e.g., "Why was this victim prioritized?").
    4.  **Real-Time Simulation**: A "digital twin" of the disaster site for live monitoring and what-if analysis.

*   **Human Impact**: By optimizing rescue plans and minimizing risk to first responders, ADRIE directly contributes to:
    1.  **Saving more lives** by reaching critical victims faster.
    2.  **Protecting our heroes** by routing them away from unnecessary danger.
    3.  **Bringing clarity and efficiency** to the most stressful and chaotic environments imaginable.

---

### 🎮 Live Demo & Usage

**1. Access the 3D Simulation UI:**
Navigate to [**https://adrie-api.onrender.com/simulation**](https://adrie-api.onrender.com/simulation) (or your Render deployment URL).

**2. Start a Simulation:**
Click the "Initiate New Simulation" button. This will call the `/simulate` endpoint and generate a new mission with a 3D environment, hazards, and victims.

**3. Generate a Rescue Plan:**
Once the simulation is ready, click "Generate Rescue Plan". This will call the `/plan` endpoint, and you will see the planned paths for the agents visualized in the 3D scene.

---

### 🛠️ Technical Architecture & Local Setup

ADRIE is built on a modern, robust Python backend with a clean, modular architecture.

*   **Backend**: FastAPI, Pydantic, Gunicorn
*   **Frontend (Simulation)**: Three.js, HTML, CSS, JavaScript
*   **Core Logic**: Multi-agent planning, A* search, risk modeling, and configurable prioritization services.

**Running Locally:**
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/psycho-prince/adrie.git
    cd adrie
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --reload
    ```
5.  **Access the API and Simulation:**
    *   **API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    *   **3D Simulation:** [http://127.0.0.1:8000/simulation](http://127.0.0.1:8000/simulation)

---

### ☁️ Production & Deployment (Render)

ADRIE is configured for seamless deployment on Render.

*   **Repository**: Your GitHub fork
*   **Root Directory**: (leave empty)
*   **Build Command**: `pip install -r requirements.txt`
*   **Start Command**: `gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
*   **Health Check Path**: `/health`

---

### 🗺️ Future Roadmap

*   **Enhanced Simulation**: Integrate a more advanced physics engine and more realistic agent models.
*   **Reinforcement Learning**: Use RL to train agents for even more complex and adaptive behaviors.
*   **Hardware Integration**: Develop connectors for popular robotics platforms (e.g., ROS, DJI drones).
*   **Cloud-Native Scaling**: Deploy on Kubernetes for high-availability, large-scale simulations.

## Quick Demo (after deploy)

Once deployed, you can interact with the Adrie Simulation Dashboard:

1.  Open your browser and navigate to `https://adrie-api.onrender.com/simulation`.
2.  Click the "Initiate New Simulation" button to start a new mission.
3.  Observe the Mission ID, Status, and KPIs updating automatically.
4.  Once the simulation status shows "completed", click the "Generate Plan" button to fetch and display the AI-generated plan.


import * as THREE from 'https://cdn.skypack.dev/three@0.128.0';
import { OrbitControls } from 'https://cdn.skypack.dev/three@0.128.0/examples/jsm/controls/OrbitControls.js';

let scene, camera, renderer, controls;
let missionId = null;

const API_BASE_URL = 'http://127.0.0.1:8000'; // Assuming local server for now

// --- UI Elements ---
const missionIdEl = document.getElementById('mission-id');
const missionStatusEl = document.getElementById('mission-status');
const victimsRescuedEl = document.getElementById('victims-rescued');
const totalVictimsEl = document.getElementById('total-victims');
const startSimBtn = document.getElementById('start-sim-btn');
const generatePlanBtn = document.getElementById('generate-plan-btn');


// --- SCENE INITIALIZATION ---

function init() {
    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a);

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(15, 25, 15);
    camera.lookAt(0, 0, 0);

    // Renderer setup
    const container = document.getElementById('simulation-container');
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(50, 50, 50);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Controls
    controls = new OrbitControls(camera, renderer.domElement);

    // Event Listeners
    window.addEventListener('resize', onWindowResize, false);
    startSimBtn.addEventListener('click', startSimulation);
    generatePlanBtn.addEventListener('click', generatePlan);

    // Initial state
    createGroundPlane(50);
    animate();
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

// --- CORE LOGIC ---

function createGroundPlane(size) {
    const geometry = new THREE.PlaneGeometry(size, size);
    const material = new THREE.MeshStandardMaterial({ color: 0x444444, side: THREE.DoubleSide });
    const plane = new THREE.Mesh(geometry, material);
    plane.rotation.x = -Math.PI / 2;
    plane.receiveShadow = true;
    scene.add(plane);
}

async function startSimulation() {
    console.log("Initiating new simulation...");
    missionStatusEl.textContent = "Initiating...";

    const simConfig = {
        map_size: 50,
        hazard_intensity_factor: 0.5,
        num_victims: 10,
        num_agents: 3,
        seed: Math.floor(Math.random() * 10000)
    };

    try {
        const response = await fetch(`${API_BASE_URL}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(simConfig),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        missionId = data.mission_id;

        // Update UI
        missionIdEl.textContent = missionId;
        missionStatusEl.textContent = "Simulation Ready";
        totalVictimsEl.textContent = simConfig.num_victims;
        generatePlanBtn.disabled = false;
        startSimBtn.textContent = "Start New Simulation";

        // TODO: Fetch and render the environment (hazards, victims, agents)
        console.log("Simulation started with Mission ID:", missionId);

    } catch (error) {
        console.error("Failed to start simulation:", error);
        missionStatusEl.textContent = "Error";
    }
}

async function generatePlan() {
    if (!missionId) return;

    console.log("Generating rescue plan...");
    missionStatusEl.textContent = "Generating Plan...";

    const planConfig = {
        mission_id: missionId,
        planning_objective: "minimize_risk_exposure",
        replan: false,
    };

    try {
        const response = await fetch(`${API_BASE_URL}/plan/${missionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(planConfig),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Plan generated:", data);
        missionStatusEl.textContent = "Plan Generated";
        
        // TODO: Visualize the agent paths
        
    } catch (error) {
        console.error("Failed to generate plan:", error);
        missionStatusEl.textContent = "Error";
    }
}


// --- RUN ---
init();

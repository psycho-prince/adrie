// static/main.js
(function() {
    const startSimBtn = document.getElementById('start-sim-btn');
    const generatePlanBtn = document.getElementById('generate-plan-btn');
    const missionIdSpan = document.getElementById('mission-id');
    const statusSpan = document.getElementById('status');
    const kpiSuccessRateSpan = document.getElementById('kpi-success-rate');
    const kpiTimeTakenSpan = document.getElementById('kpi-time-taken');
    const planJsonPre = document.getElementById('plan-json'); // Corresponds to <pre id="plan-json"> in HTML

    let currentMissionId = null;
    let pollingInterval = null;

    async function startSimulation() {
        startSimBtn.disabled = true;
        generatePlanBtn.disabled = true;
        missionIdSpan.textContent = 'Initiating...';
        statusSpan.textContent = 'Requesting...';
        planJsonPre.textContent = 'No plan generated yet.';
        kpiSuccessRateSpan.textContent = 'N/A';
        kpiTimeTakenSpan.textContent = 'N/A';

        try {
            const seed = Math.floor(Math.random() * 100000); // Generate a random seed
            const simulationParams = {
                map_size: 50,
                hazard_intensity_factor: 0.5,
                num_victims: 10,
                num_agents: 3,
                seed: seed
            };

            const response = await fetch('/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(simulationParams)
            });
            const data = await response.json();

            if (response.ok) {
                currentMissionId = data.mission_id;
                missionIdSpan.textContent = currentMissionId;
                statusSpan.textContent = data.status;
                startPollingMetrics();
                console.log('Simulation started:', data);
            } else {
                alert(`Error starting simulation: ${data.message || response.statusText}`);
                console.error('Error starting simulation:', data);
                resetDashboard();
            }
        } catch (error) {
            alert(`Network error starting simulation: ${error.message}`);
            console.error('Network error starting simulation:', error);
            resetDashboard();
        } finally {
            startSimBtn.disabled = false;
        }
    }

    async function pollMetrics() {
        if (!currentMissionId) return;

        try {
            const response = await fetch(`/metrics?mission_id=${currentMissionId}`);
            const data = await response.json();

            if (response.ok) {
                missionIdSpan.textContent = data.mission_id;
                statusSpan.textContent = data.status;
                kpiSuccessRateSpan.textContent = (data.kpis.success_rate * 100).toFixed(1) + '%';
                kpiTimeTakenSpan.textContent = data.kpis.time_taken + 's';

                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    if (data.status === 'completed') {
                        generatePlanBtn.disabled = false;
                    }
                } else {
                    generatePlanBtn.disabled = true; // Disable if still running
                }
            } else {
                console.error('Error polling metrics:', data);
                clearInterval(pollingInterval);
                pollingInterval = null;
                resetDashboard();
            }
        } catch (error) {
            console.error('Network error polling metrics:', error);
            clearInterval(pollingInterval);
            pollingInterval = null;
            resetDashboard();
        }
    }

    function startPollingMetrics() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        pollingInterval = setInterval(pollMetrics, 5000); // Poll every 5 seconds as requested
        pollMetrics(); // Initial call
    }

    async function generatePlan() {
        if (!currentMissionId) {
            alert('No simulation running or completed to generate a plan for.');
            return;
        }
        generatePlanBtn.disabled = true;
        planJsonPre.textContent = 'Generating plan...';

        try {
            const planParams = {
                planning_objective: "minimize_risk_exposure",
                replan: false
            };
            const response = await fetch(`/plan/${currentMissionId}`, { // Updated endpoint with mission_id
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(planParams)
            });
            const data = await response.json();

            if (response.ok) {
                planJsonPre.textContent = JSON.stringify(data.plan, null, 2);
                console.log('Plan generated:', data.plan);
            } else {
                alert(`Error generating plan: ${data.message || response.statusText}`);
                console.error('Error generating plan:', data);
                planJsonPre.textContent = 'Failed to generate plan.';
            }
        } catch (error) {
            alert(`Network error generating plan: ${error.message}`);
            console.error('Network error generating plan:', error);
            planJsonPre.textContent = 'Failed to generate plan.';
        } finally {
            generatePlanBtn.disabled = false;
        }
    }

    function resetDashboard() {
        currentMissionId = null;
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        missionIdSpan.textContent = 'N/A';
        statusSpan.textContent = 'Idle';
        kpiSuccessRateSpan.textContent = 'N/A';
        kpiTimeTakenSpan.textContent = 'N/A';
        planJsonPre.textContent = 'No plan generated yet.';
        generatePlanBtn.disabled = true;
        startSimBtn.disabled = false;
    }

    startSimBtn.addEventListener('click', startSimulation);
    generatePlanBtn.addEventListener('click', generatePlan);

    // Initial state setup
    resetDashboard();
})();

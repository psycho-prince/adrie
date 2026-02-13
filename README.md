ADRIE — Autonomous Disaster Response Intelligence Engine

Enterprise-grade AI platform for multi-agent disaster response planning, risk-aware routing, and explainable decision intelligence.


---

📚 Table of Contents

1. Overview


2. Features


3. Architecture


4. Project Structure


5. Quick Start


6. Running Locally (All OS)


7. Running in Termux


8. Running with Docker


9. Running Tests


10. API Usage


11. Deploying to Render


12. Troubleshooting


13. Contributing


14. License




---

🧠 Overview

ADRIE is a modular AI system that simulates disaster environments and produces risk-optimized multi-agent rescue plans with full explainability.

It combines:

Multi-agent planning

Risk modeling

Ethical prioritization

Explainable AI

Operational metrics



---

✨ Features

✔ Disaster simulation engine
✔ Risk-weighted A* path planning
✔ Multi-agent coordination
✔ LLM explainability
✔ Metrics & KPIs
✔ Production-ready FastAPI backend
✔ OpenAPI docs


---

🏗 Architecture

ADRIE follows Clean Architecture and SOLID principles.

Core layers:

API Layer — FastAPI endpoints

Services — Business logic

Models — Pydantic schemas

Infrastructure — State & orchestration

Explainability — LLM interface



---

📂 Project Structure

adrie/
 ├── api/
 ├── core/
 ├── explainability/
 ├── infrastructure/
 ├── middleware/
 ├── models/
 ├── services/
 ├── tests/
 ├── ui/
 main.py
 requirements.txt


---

⚡ Quick Start

git clone https://github.com/psycho-prince/adrie.git
cd adrie
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload

Open:

👉 http://127.0.0.1:8000/docs


---

💻 Running Locally (All OS)

🐧 Linux

sudo apt install python3 python3-venv
git clone https://github.com/psycho-prince/adrie.git
cd adrie
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload


---

🍎 macOS

brew install python
git clone https://github.com/psycho-prince/adrie.git
cd adrie
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload


---

🪟 Windows (PowerShell)

git clone https://github.com/psycho-prince/adrie.git
cd adrie
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload


---

📱 Running in Termux (Android)

pkg update
pkg upgrade
pkg install python git clang

git clone https://github.com/psycho-prince/adrie.git
cd adrie

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python -m uvicorn main:app --host 0.0.0.0 --port 8000

Access:

http://127.0.0.1:8000/docs


---

🐳 Running with Docker (Optional)

Build image

docker build -t adrie .

Run container

docker run -p 8000:8000 adrie


---

🧪 Running Tests

pytest

With coverage:

pytest --cov=adrie


---

🔌 API Usage

Start simulation

curl -X POST http://localhost:8000/simulate

Generate plan

curl -X POST http://localhost:8000/plan/{mission_id}

Get metrics

curl http://localhost:8000/metrics/{mission_id}

Explain decision

curl http://localhost:8000/explain/{mission_id}/mission_summary


---

☁️ Deploying to Render

1️⃣ Push repo to GitHub

2️⃣ Create Web Service on Render

Build Command

pip install -r requirements.txt

Start Command

python -m uvicorn main:app --host 0.0.0.0 --port $PORT

Health Check

/health


---

3️⃣ Deploy

After deploy:

👉 https://your-app.onrender.com/docs


---

🧰 Troubleshooting

❌ ModuleNotFoundError: adrie

Run using:

python -m uvicorn main:app


---

❌ Port already in use

kill -9 <PID>


---

❌ Dependencies fail

pip install --upgrade pip
pip install -r requirements.txt


---

🧠 Performance Tips

Use Python 3.11+

Run without --reload in production

Enable async workers for scale



---

🤝 Contributing

1. Fork repo


2. Create feature branch


3. Submit PR




---

📜 License

MIT License


---

🚀 Status

ADRIE is demo-ready and deployable as an AI decision-intelligence platform for disaster response simulations.


---

If you want, I can next:

✅ Write a short hackathon version README
✅ Create a submission description
✅ Generate a demo script
✅ Add a Dockerfile

Just tell me 👍
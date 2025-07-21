
# 🚀 Autonomous AI Agent Infrastructure (LangGraph + Docker + K8s)

This project deploys an **autonomous LangGraph AI assistant** in a **real-world production environment** using:

- 🧠 **LangGraph + OpenAI GPT-4o** for planning and executing tasks
- 🐳 **Docker** for containerized reproducibility
- ☸️ **Kubernetes** for scalable orchestration
- 📊 **Prometheus + Grafana** for resource monitoring
- ❤️ **Health & Readiness Probes** for production-grade reliability

---

## 🧠 Core AI Features
- Accepts a user-defined goal (e.g. `"Build a workout planner"`)
- Estimates number of days needed to complete it
- Breaks it into subtasks automatically
- Executes tasks and reviews progress daily
- Persists memory across sessions (like a real autonomous agent)

---

## ⚙️ Infrastructure Features
- `Dockerfile`: Builds a container for the agent
- `docker-compose.yml`: Optional local monitoring stack (Prometheus + Grafana)
- `deployment.yaml` + `service.yaml`: Kubernetes deployment and exposure configs
- `agent_memory.json`: Mounted volume to persist daily progress
- `/health` and `/ready`: FastAPI endpoints for liveness/readiness probes

---

## 📈 Example Use Cases
- Scalable self-improving learning agents
- Task planners with daily progress tracking
- Deployable AI assistant on cloud or local K8s
- DevOps-style infrastructure for LLM projects

---

## 🗂️ Files Overview
| File | Purpose |
|------|---------|
| `app.py` | Main LangGraph agent logic with FastAPI server |
| `Dockerfile` | Container build for the AI agent |
| `deployment.yaml` | Kubernetes deployment definition |
| `service.yaml` | Kubernetes service (exposes `/health` and `/ready`) |
| `docker-compose.yml` | Launches Grafana + Prometheus stack |
| `prometheus.yml` | Prometheus scrape config |
| `requirements.txt` | Python dependencies |
| `README.md` | You’re reading it! |

---

## ▶️ Run Locally with Docker
```bash
docker build -t langgraph-agent .
docker run -p 8000:8000 -e USER_GOAL="Learn LangGraph" langgraph-agent


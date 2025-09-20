readme = """
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

"""

with open("README.md", "w") as f:
  f.write(readme)
!cat README.md  # to preview

docker_notes = """
# 🐳 Dockerfile Breakdown – LangGraph Agent

## Base Image
`FROM python:3.10-slim`
→ Uses a minimal Python 3.10 Linux-based image to keep size small

## Working Directory
`WORKDIR /app`
→ Creates and sets the working directory to `/app` inside the container

## Copy Project Files
`COPY . .`
→ Copies all local files (app.py, requirements.txt, etc.) into `/app` inside the container

## Install Dependencies
`RUN pip install --no-cache-dir -r requirements.txt`
→ Installs all Python packages listed in `requirements.txt` with no caching to save space

## Start App
`CMD ["python", "app.py"]`
→ Tells Docker what command to run when the container starts

## Runtime
Container is run using:
`docker run --env-file .env -v ${PWD}:/app -it langgraph-agent`
→ Passes in the OpenAI key, links current folder for saving memory, and launches interactively
"""

# Save to file
with open("docker-notes.md", "w") as f:
    f.write(docker_notes.strip())

# Show file contents
!cat docker-notes.md

# Download to your computer
from google.colab import files
files.download("docker-notes.md")

!pip install -q langgraph openai

import json
from langgraph.graph import StateGraph

from getpass import getpass
import os

os.environ["OPENAI_API_KEY"] = getpass("🔑 Enter your OpenAI API Key: ")

import os
import json
from openai import OpenAI
import langgraph
from langgraph.graph import StateGraph

# ✅ User input is now pulled from environment variable
def user_goal_node(state):
    goal = os.getenv("USER_GOAL", "Default Goal")
    print(f"User Goal Provided: {goal}")
    return {**state, "user_goal": goal, "role": "planner"}

client = OpenAI()

def planner_node(state):
    round_num = state.get("round", 1)
    goal = state.get("user_goal", "")
    completed = state.get("subtask_progress", [])

    print(f"📅 Planner: Planning task for Day {round_num}...\n🧠 Goal: {goal}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    f"You are a helpful AI planner. The user's goal is: '{goal}'. "
                    f"They have already completed: {completed}. "
                    "If the goal is fully complete, respond ONLY with: 'GOAL COMPLETE'. "
                    "If not, return ONE next subtask to help complete the goal."
                )},
                {"role": "user", "content": "What should I do next?"}
            ],
            max_tokens=50
        )
        task = response.choices[0].message.content.strip()
    except Exception as e:
        task = f"Error generating task: {e}"

    logs = state.get("log", [])
    logs.append(f"Planned task {round_num}: {task}")

    if "goal complete" in task.lower():
        return {**state, "role": "end", "log": logs}

    return {
        **state,
        "task": task,
        "role": "executor",
        "log": logs
    }

def estimate_difficulty_node(state):
    goal = state.get("user_goal", "")
    print(f"Estimating difficulty for goal: {goal}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are an AI task analyst. Given a user's goal, estimate the number of days needed to accomplish it "
                    "realistically with daily tasks. Respond ONLY with a number between 1 and 10."
                )},
                {"role": "user", "content": f"My goal is: {goal}"}
            ],
            max_tokens=10
        )
        estimated_days = int("".join(filter(str.isdigit, response.choices[0].message.content.strip())))
        print(f"Estimated days: {estimated_days}")
    except Exception as e:
        print(f"Error estimating difficulty: {e}")
        estimated_days = 3

    return {
        **state,
        "max_rounds": estimated_days,
        "role": "planner"
    }

def executor_node(state):
    task = state.get("task", "")
    print(f"Executor: Executing task: {task}")
    try:
        result = eval(task)
    except Exception as e:
        result = f"Error: {e}"
    logs = state.get("log", [])
    logs.append(f"Executed: {task} -> {result}")
    return {
        **state,
        "result": result,
        "role": "reviewer",
        "log": logs
    }

def reviewer_node(state):
    round_num = state.get("round", 1)
    logs = state.get("log", [])
    logs.append(f"Reviewed result of Day {round_num}")
    completed = state.get("subtask_progress", [])
    completed.append(state.get("task", ""))
    return {
        **state,
        "round": round_num + 1,
        "role": "planner",
        "subtask_progress": completed,
        "log": logs
    }

def role_switch_node(state):
    print(f"Switching role to: {state.get('role')}")
    return state

def route_by_role(state):
    return {
        "planner": "planner_node",
        "executor": "executor_node",
        "reviewer": "reviewer_node"
    }.get(state.get("role", ""), "end")

def end_node(state):
    print("Finished")
    print("Final log:", state.get("log", []))
    return state

# 🧠 Build LangGraph structure
builder = StateGraph(dict)
builder.add_node("user_goal_node", user_goal_node)
builder.add_node("estimate_difficulty", estimate_difficulty_node)
builder.add_node("planner_node", planner_node)
builder.add_node("executor_node", executor_node)
builder.add_node("reviewer_node", reviewer_node)
builder.add_node("role_switch", role_switch_node)
builder.add_node("end", end_node)

builder.set_entry_point("user_goal_node")
builder.add_edge("user_goal_node", "estimate_difficulty")
builder.add_edge("estimate_difficulty", "planner_node")
builder.add_edge("planner_node", "role_switch")
builder.add_edge("executor_node", "role_switch")
builder.add_edge("reviewer_node", "role_switch")
builder.add_conditional_edges("role_switch", route_by_role)

graph = builder.compile()

# 🔄 Agent memory persistence
def save_state(state, path="agent_memory.json"):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Memory saved to {path}")

def load_state(path="agent_memory.json"):
    try:
        with open(path, "r") as f:
            state = json.load(f)
        print(f"Memory loaded from {path}")
        return state
    except FileNotFoundError:
        print("No saved memory found, starting fresh.")
        return {"role": "planner", "round": 1, "max_rounds": 3}

# 🧠 Run the agent
state = load_state()

if state.get("role") == "end":
    print("Agent has already completed its tasks. Nothing more to do.")
else:
    try:
        while state.get("role") != "end":
            state = graph.invoke(state, config={"recursion_limit": 25})
            save_state(state)
    except langgraph.errors.GraphRecursionError:
        print("Graph hit recursion limit. Stopping safely.")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading

app = FastAPI()

@app.get("/health")
def health_check():
  return JSONResponse(content={"status": "alive"}, status_code=200)

@app.get("/ready")
def ready_check():
  return JSONResponse(content={"status": "ready"}, status_code=200)

def run_server():
  uvicorn.run(app, host="0.0.0.0", port=8000)

server_thread = threading.Thread(target = run_server)
server_thread.start()

# ✅ Save requirements.txt with all needed packages
with open("requirements.txt", "w") as f:
    f.write("openai>=1.0.0\n")               # OpenAI API access (GPT-4o, etc.)
    f.write("langgraph>=0.0.35\n")           # LangGraph for agent structure
    f.write("python-dotenv>=1.0.0\n")        # For reading API keys from .env
    f.write("fastapi>=0.110.0\n")            # Web server for health/ready endpoints
    f.write("uvicorn[standard]>=0.29.0\n")   # ASGI server to run FastAPI
    f.write("pydantic>=2.0\n")               # Optional: used internally by FastAPI
    f.write("requests>=2.28.0\n")            # Optional: useful for health checks or external calls

# ✅ Display the file content
!cat requirements.txt

# ✅ Download to your computer
from google.colab import files
files.download("requirements.txt")

compose_yaml = '''
version: '3.7'

services:
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    container_name: grafana
    ports:
      - "3000:3000"

'''

# Save the file
with open("docker-compose.yml", "w") as f:
    f.write(compose_yaml.strip())

# Optional: View the contents
!cat docker-compose.yml

# Download the file
from google.colab import files
files.download("docker-compose.yml")

# ✅ Create prometheus.yml with scrape config for your local FastAPI app
prometheus_config = """
global:
  scrape_interval: 10s

scrape_configs:
  - job_name: 'kubernetes-nodes'
    static_configs:
      - targets: ['host.docker.internal:8000']
"""

# ✅ Write it to a file
with open("prometheus.yml", "w") as f:
    f.write(prometheus_config.strip())

# ✅ Display the file content
!cat prometheus.yml

# ✅ Download it to your machine
from google.colab import files
files.download("prometheus.yml")

compose_notes = """
# 🧱 Docker Compose Notes – LangGraph AI Agent

## What I Built

- A multi-container system using Docker Compose
- One container runs my LangGraph agent (`app`)
- One container runs Redis memory (`redis`)
- They are networked and can share memory
- Everything launches with one command: `docker compose up`

## File Breakdown

### docker-compose.yml

- `app` service is built from my Dockerfile
- `redis` uses the official Redis 7 image
- `.env` file loads my OpenAI key
- Volume `. : /app` mounts my local folder

### Dockerfile

- Starts from `python:3.10-slim`
- Copies my code and installs dependencies
- Runs `app.py` by default

## Why It Matters

- This is how real-world AI infra is deployed
- My agent can now scale, split into roles, and run in the cloud
- Redis lets me connect multiple agents or users to shared memory
- I can add databases, APIs, or dashboards next with ease

## How I Run It

- `docker compose up` – run full stack
- `docker compose run --rm --service-ports app` – run interactively with input()
- `docker compose down` – shut down everything

## What I’d Do Next

- Hook my agent's memory into Redis
- Add a second agent (planner + executor)
- Push to GitHub and run CI/CD
"""
with open("compose-notes.md", "w") as f:
    f.write(compose_notes.strip())

from google.colab import files
files.download("compose-notes.md")

# ✅ Write and fix deployment.yaml with correct image and both env variables
deployment = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langgraph-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: langgraph-agent
  template:
    metadata:
      labels:
        app: langgraph-agent
    spec:
      containers:
        - name: langgraph-agent
          image: aaravmehra/langgraph-agent-app:latest
          ports:
            - containerPort: 8000
          env:
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openai-secret
                  key: api-key
            - name: USER_GOAL
              value: "Learn LangGraph"
"""

with open("deployment.yaml", "w") as f:
    f.write(deployment)


# ✅ Write service.yaml
service = """
apiVersion: v1
kind: Service
metadata:
  name: langgraph-service
spec:
  selector:
    app: langgraph-agent
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
"""

with open("service.yaml", "w") as f:
    f.write(service)

# ✅ Download both files for use on your local machine
from google.colab import files
files.download("deployment.yaml")
files.download("service.yaml")

from google.colab import files
files.download("deployment.yaml")
files.download("service.yaml")

# ✅ Replace with your actual OpenAI key
api_key = "sk-...your-real-key..."
user_goal = "Build an AI agent that plans workouts"

# ✅ Save .env
with open(".env", "w") as f:
    f.write(f"OPENAI_API_KEY={api_key}\n")
    f.write(f"USER_GOAL={user_goal}\n")

# ✅ Optional: View contents
!cat .env

# ✅ Optional: Download
from google.colab import files
files.download(".env")

dockerfile_code = '''
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
'''

with open("Dockerfile", "w") as f:
    f.write(dockerfile_code.strip())

# Optional: View contents
!cat Dockerfile

# Download the file
from google.colab import files
files.download("Dockerfile")

code = '''
import os
import json
from openai import OpenAI
import langgraph
from langgraph.graph import StateGraph

# ✅ User input is now pulled from environment variable
def user_goal_node(state):
    goal = os.getenv("USER_GOAL", "Default Goal")
    print(f"User Goal Provided: {goal}")
    return {**state, "user_goal": goal, "role": "planner"}

client = OpenAI()

def planner_node(state):
    round_num = state.get("round", 1)
    goal = state.get("user_goal", "")
    completed = state.get("subtask_progress", [])

    print(f"📅 Planner: Planning task for Day {round_num}...\n🧠 Goal: {goal}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    f"You are a helpful AI planner. The user's goal is: '{goal}'. "
                    f"They have already completed: {completed}. "
                    "If the goal is fully complete, respond ONLY with: 'GOAL COMPLETE'. "
                    "If not, return ONE next subtask to help complete the goal."
                )},
                {"role": "user", "content": "What should I do next?"}
            ],
            max_tokens=50
        )
        task = response.choices[0].message.content.strip()
    except Exception as e:
        task = f"Error generating task: {e}"

    logs = state.get("log", [])
    logs.append(f"Planned task {round_num}: {task}")

    if "goal complete" in task.lower():
        return {**state, "role": "end", "log": logs}

    return {
        **state,
        "task": task,
        "role": "executor",
        "log": logs
    }

def estimate_difficulty_node(state):
    goal = state.get("user_goal", "")
    print(f"Estimating difficulty for goal: {goal}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are an AI task analyst. Given a user's goal, estimate the number of days needed to accomplish it "
                    "realistically with daily tasks. Respond ONLY with a number between 1 and 10."
                )},
                {"role": "user", "content": f"My goal is: {goal}"}
            ],
            max_tokens=10
        )
        estimated_days = int("".join(filter(str.isdigit, response.choices[0].message.content.strip())))
        print(f"Estimated days: {estimated_days}")
    except Exception as e:
        print(f"Error estimating difficulty: {e}")
        estimated_days = 3

    return {
        **state,
        "max_rounds": estimated_days,
        "role": "planner"
    }

def executor_node(state):
    task = state.get("task", "")
    print(f"Executor: Executing task: {task}")
    try:
        result = eval(task)
    except Exception as e:
        result = f"Error: {e}"
    logs = state.get("log", [])
    logs.append(f"Executed: {task} -> {result}")
    return {
        **state,
        "result": result,
        "role": "reviewer",
        "log": logs
    }

def reviewer_node(state):
    round_num = state.get("round", 1)
    logs = state.get("log", [])
    logs.append(f"Reviewed result of Day {round_num}")
    completed = state.get("subtask_progress", [])
    completed.append(state.get("task", ""))
    return {
        **state,
        "round": round_num + 1,
        "role": "planner",
        "subtask_progress": completed,
        "log": logs
    }

def role_switch_node(state):
    print(f"Switching role to: {state.get('role')}")
    return state

def route_by_role(state):
    return {
        "planner": "planner_node",
        "executor": "executor_node",
        "reviewer": "reviewer_node"
    }.get(state.get("role", ""), "end")

def end_node(state):
    print("Finished")
    print("Final log:", state.get("log", []))
    return state

# 🧠 Build LangGraph structure
builder = StateGraph(dict)
builder.add_node("user_goal_node", user_goal_node)
builder.add_node("estimate_difficulty", estimate_difficulty_node)
builder.add_node("planner_node", planner_node)
builder.add_node("executor_node", executor_node)
builder.add_node("reviewer_node", reviewer_node)
builder.add_node("role_switch", role_switch_node)
builder.add_node("end", end_node)

builder.set_entry_point("user_goal_node")
builder.add_edge("user_goal_node", "estimate_difficulty")
builder.add_edge("estimate_difficulty", "planner_node")
builder.add_edge("planner_node", "role_switch")
builder.add_edge("executor_node", "role_switch")
builder.add_edge("reviewer_node", "role_switch")
builder.add_conditional_edges("role_switch", route_by_role)

graph = builder.compile()

# 🔄 Agent memory persistence
def save_state(state, path="agent_memory.json"):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Memory saved to {path}")

def load_state(path="agent_memory.json"):
    try:
        with open(path, "r") as f:
            state = json.load(f)
        print(f"Memory loaded from {path}")
        return state
    except FileNotFoundError:
        print("No saved memory found, starting fresh.")
        return {"role": "planner", "round": 1, "max_rounds": 3}

# 🧠 Run the agent
state = load_state()

if state.get("role") == "end":
    print("Agent has already completed its tasks. Nothing more to do.")
else:
    try:
        while state.get("role") != "end":
            state = graph.invoke(state, config={"recursion_limit": 25})
            save_state(state)
    except langgraph.errors.GraphRecursionError:
        print("Graph hit recursion limit. Stopping safely.")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading

app = FastAPI()

@app.get("/health")
def health_check():
  return JSONResponse(content={"status": "alive"}, status_code=200)

@app.get("/ready")
def ready_check():
  return JSONResponse(content={"status": "ready"}, status_code=200)

def run_server():
  uvicorn.run(app, host="0.0.0.0", port=8000)

server_thread = threading.Thread(target = run_server)
server_thread.start()
'''

with open("app.py", "w") as f:
    f.write(code)

print("✅ Saved as app.py")

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
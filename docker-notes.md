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
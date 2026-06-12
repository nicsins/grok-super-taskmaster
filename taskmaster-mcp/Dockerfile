FROM python:3.12-slim

LABEL org.opencontainers.image.title="taskmaster-mcp"
LABEL org.opencontainers.image.description="High-level TASK orchestrator MCP. Spins up in Podman. Implements /task: {name; param} semantics with symbiotic multi-connector execution (godaddy + vercel etc.). TASK defs storable to local + GitHub."

WORKDIR /app

RUN pip install --no-cache-dir "mcp[cli]" httpx pydantic

COPY server.py /app/server.py
RUN chmod +x /app/server.py

# Mount point for persisted tasks (optional)
VOLUME ["/tasks"]

ENTRYPOINT ["python", "/app/server.py"]

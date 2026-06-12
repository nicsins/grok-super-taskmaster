FROM python:3.12-slim

LABEL org.opencontainers.image.title="godaddy-mcp"
LABEL org.opencontainers.image.description="Podman/OCI runnable MCP server for GoDaddy domain + DNS management. Enables full automated domain-to-hosting connect TASKs when combined with vercel (or other) connectors."
LABEL org.opencontainers.image.source="https://github.com/nicsins/grok-super-taskmaster"

WORKDIR /app

RUN pip install --no-cache-dir "mcp[cli]" httpx pydantic

COPY server.py /app/server.py
RUN chmod +x /app/server.py

ENTRYPOINT ["python", "/app/server.py"]
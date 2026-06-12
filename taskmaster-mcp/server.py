#!/usr/bin/env python3
"""
TaskMaster MCP Server
Podman-spinnable MCP server that provides high-level "TASK" objects.
A TASK is a named, repeatable, multi-connector orchestration that requires only the desired outcome + minimal params (e.g. url).

Example invocation (via model using use_tool or via /task sugar once wired):
  execute_task spec="{connect_domain; my-site.blah}"

It deduces the task, loads any saved TASK definition (from local, github via token, or memory), then executes the full symbiotic flow using direct API calls to the involved connectors (godaddy + vercel primarily).

This eliminates repetitive rhetoric: one compact /task: {name; param} does what previously required paragraphs of "use the vercel connector to..., now use godaddy to set these exact records... verify... "

TASKs are first-class, storable artifacts (JSON) that live in:
- Local ~/.grok/tasks/
- GitHub repo (using GITHUB_TOKEN + github MCP synergy or direct API here)
- Grok memory (via external note or future memory MCP)

The server itself can be registered exactly like godaddy-mcp using podman.

Environment for full power:
  GODADDY_API_KEY / GODADDY_API_SECRET
  VERCEL_TOKEN (for adding domain to project + deploys)
  GITHUB_TOKEN (optional, for persisting TASK definitions to a repo)

Built-in TASKs (always available, can be overridden by saved ones):
- connect_domain
- deploy_and_connect (future)
- etc.

All actions are real HTTP to the provider APIs. No simulation.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("taskmaster")

# Paths inside or outside container. Mount for persistence if desired.
TASK_DIR = Path(os.getenv("TASK_DIR", "/tasks"))
TASK_DIR.mkdir(parents=True, exist_ok=True)

GODADDY_BASE = "https://api.godaddy.com/v1"
VERCEL_BASE = "https://api.vercel.com"

# ---------- Models & Registry ----------

class TaskSpec(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

class TaskDefinition(BaseModel):
    name: str
    description: str
    params_schema: Dict[str, Any]
    steps: List[Dict[str, Any]]  # high level step descriptors or raw tool call templates
    version: str = "1.0.0"

BUILTIN_TASKS: Dict[str, TaskDefinition] = {
    "connect_domain": TaskDefinition(
        name="connect_domain",
        description="Point a custom domain at a Vercel (or compatible) deployment using GoDaddy DNS + Vercel project registration. Requires only the exact domain. Symbiotic: vercel side prep + godaddy DNS effector + verification + vercel domain add.",
        params_schema={"domain": {"type": "string", "required": True}},
        steps=[
            {"action": "ensure_vercel_project_ready", "note": "Use VERCEL_TOKEN or grok_com_vercel tools in outer loop"},
            {"action": "apply_vercel_dns_on_godaddy"},
            {"action": "register_domain_on_vercel"},
            {"action": "verify"},
        ],
        version="1.0.0",
    ),
    "save_task": TaskDefinition(
        name="save_task",
        description="Persist a new or updated TASK definition (JSON) to local registry and optionally GitHub.",
        params_schema={"task_json": {"type": "object"}},
        steps=[{"action": "persist_task_def"}],
    ),
}

def _load_saved_task(name: str) -> Optional[TaskDefinition]:
    p = TASK_DIR / f"{name}.json"
    if p.exists():
        data = json.loads(p.read_text())
        return TaskDefinition(**data)
    return None

def _save_task(defn: TaskDefinition, also_to_github: bool = False, github_repo: Optional[str] = None) -> str:
    p = TASK_DIR / f"{defn.name}.json"
    p.write_text(defn.model_dump_json(indent=2))
    loc = str(p)
    if also_to_github and github_repo and os.getenv("GITHUB_TOKEN"):
        # Real push via GitHub contents API
        _push_task_to_github(defn, github_repo)
        loc += " + github"
    return loc

def _push_task_to_github(defn: TaskDefinition, repo: str, path: Optional[str] = None):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return
    path = path or f"tasks/{defn.name}.json"
    owner, repo_name = repo.split("/", 1) if "/" in repo else (None, repo)
    # Use contents API to create/update
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    content = defn.model_dump_json(indent=2)
    import base64
    b64 = base64.b64encode(content.encode()).decode()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    # Get current sha if exists (for update)
    sha = None
    try:
        r = httpx.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass
    payload = {"message": f"Update TASK {defn.name} via TaskMaster MCP", "content": b64}
    if sha:
        payload["sha"] = sha
    try:
        httpx.put(url, headers=headers, json=payload, timeout=20)
    except Exception as e:
        print(f"GitHub push warning: {e}")

# ---------- Low-level real API helpers (symbiotic implementations) ----------

def _godaddy_auth() -> str:
    k = os.getenv("GODADDY_API_KEY")
    s = os.getenv("GODADDY_API_SECRET")
    if not k or not s:
        raise RuntimeError("GODADDY_API_KEY / GODADDY_API_SECRET required for godaddy actions in TASK")
    return f"sso-key {k}:{s}"

async def _gd(method: str, path: str, json_body: Any = None) -> Any:
    headers = {"Authorization": _godaddy_auth(), "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=40) as c:
        r = await c.request(method, f"{GODADDY_BASE}{path}", headers=headers, json=json_body)
        r.raise_for_status()
        return r.json() if r.text.strip() else {}

def _vercel_auth() -> str:
    t = os.getenv("VERCEL_TOKEN")
    if not t:
        raise RuntimeError("VERCEL_TOKEN required for vercel-side TASK actions (add domain, etc.)")
    return t

async def _vc(method: str, path: str, json_body: Any = None, extra_headers: Optional[Dict] = None) -> Any:
    headers = {"Authorization": f"Bearer {_vercel_auth()}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    async with httpx.AsyncClient(timeout=40) as c:
        r = await c.request(method, f"{VERCEL_BASE}{path}", headers=headers, json=json_body)
        r.raise_for_status()
        return r.json() if r.text.strip() else {}

# ---------- Core TASK executor ----------

async def _execute_connect_domain(domain: str, vercel_project_id_or_slug: Optional[str] = None, team_id: Optional[str] = None) -> Dict[str, Any]:
    """The real symbiotic implementation for connect_domain.
    - Updates GoDaddy DNS with Vercel targets (A @ + CNAME www)
    - If VERCEL_TOKEN and project info, adds the domain to the Vercel project (enables certs, proper routing)
    - Verifies from godaddy side
    Only the domain is strictly required. Everything else deduced or uses env.
    """
    results: Dict[str, Any] = {"task": "connect_domain", "domain": domain, "steps": []}

    # 1. GoDaddy side - the effector (always)
    apex = "76.76.21.21"
    www = "cname.vercel-dns.com."
    try:
        recs = [
            {"type": "A", "name": "@", "data": apex, "ttl": 600},
            {"type": "CNAME", "name": "www", "data": www, "ttl": 600},
        ]
        await _gd("PATCH", f"/domains/{domain}/records", json_body=recs)
        results["steps"].append({"step": "godaddy_dns_applied", "records": recs, "status": "success"})
    except Exception as e:
        results["steps"].append({"step": "godaddy_dns_applied", "error": str(e)})
        raise

    # 2. Vercel side - register the domain on the project if we have token + project hint
    vercel_add_result = None
    if os.getenv("VERCEL_TOKEN"):
        try:
            # Discover project if only slug or use provided
            proj = vercel_project_id_or_slug
            if not proj:
                # Try list and pick first or use env convention; for real use caller should supply
                projs = await _vc("GET", "/v9/projects")
                if projs.get("projects"):
                    proj = projs["projects"][0]["id"]
            if proj:
                # Vercel domain add endpoint (v9 or v10)
                body = {"name": domain}
                if team_id:
                    body["teamId"] = team_id  # sometimes passed in query but here in body for simplicity
                # The canonical is POST /v9/projects/{idOrName}/domains
                vercel_add_result = await _vc("POST", f"/v9/projects/{proj}/domains", json_body=body)
                results["steps"].append({"step": "vercel_domain_registered", "result": vercel_add_result, "status": "success"})
            else:
                results["steps"].append({"step": "vercel_domain_registered", "note": "no project id discovered; user should add manually or pass vercel_project_id_or_slug"})
        except Exception as e:
            results["steps"].append({"step": "vercel_domain_registered", "error": str(e), "note": "DNS is set; add domain in Vercel dashboard for full SSL"})
    else:
        results["steps"].append({"step": "vercel_domain_registered", "note": "VERCEL_TOKEN not provided; DNS updated on godaddy. Call grok_com_vercel tools or supply token for full symbiosis."})

    # 3. Quick verify (godaddy view + note on propagation)
    try:
        current = await _gd("GET", f"/domains/{domain}/records")
        results["steps"].append({"step": "verify_godaddy_view", "records": current})
    except Exception as e:
        results["steps"].append({"step": "verify", "warning": str(e)})

    results["final_note"] = "DNS records applied on GoDaddy. Propagation typically < 60s-5min. If vercel registration succeeded, https://domain should get SSL shortly after adding in project. Re-deploy on vercel if needed (grok_com_vercel__deploy_to_vercel or vercel CLI)."
    results["success"] = True
    return results

# ---------- MCP Tools (the public interface for /task and model use) ----------

@mcp.tool()
async def list_available_tasks() -> List[str]:
    """Discover all TASKs (built-in + any saved in the registry)."""
    saved = [p.stem for p in TASK_DIR.glob("*.json")]
    return list(set(list(BUILTIN_TASKS.keys()) + saved))

@mcp.tool()
async def get_task_definition(name: str) -> Dict[str, Any]:
    """Return the full TASK definition JSON for inspection or editing."""
    defn = _load_saved_task(name) or BUILTIN_TASKS.get(name)
    if not defn:
        raise ValueError(f"Unknown TASK: {name}")
    return defn.model_dump()

@mcp.tool()
async def save_task_definition(task_json: Dict[str, Any], persist_to_github: bool = False, github_repo: str = "nicsins/grok-tasks") -> str:
    """Create or update a reusable TASK definition. Saved locally under TASK_DIR and optionally pushed to the github repo using GITHUB_TOKEN.
    This is how you 'create these tasks any time a potentially repeatable action is conducted'.
    The saved TASK can then be invoked by name via execute_task.
    """
    defn = TaskDefinition(**task_json)
    loc = _save_task(defn, also_to_github=persist_to_github, github_repo=github_repo)
    return f"TASK {defn.name} saved to {loc}"

@mcp.tool()
async def execute_task(spec: str, vercel_project_id_or_slug: Optional[str] = None, team_id: Optional[str] = None, github_repo_for_taskdefs: str = "nicsins/grok-tasks") -> Dict[str, Any]:
    """THE central entrypoint for all high-level multi-connector TASKs.

    spec format (exact as user requested):
      "{connect_domain; my-site.blah}"
      or "{connect_domain; url=my-site.blah; project=prj_xxx}"

    If the gist of the task can be deduced from the name (connect_domain, deploy_and_connect, etc.), it proceeds with minimal additional input.
    The url/domain must be exact.

    This orchestrates the real connectors (godaddy + vercel primarily) in the correct symbiotic order with full automation.
    Only the desired effect + the key param (domain) is required from the caller.
    """
    # Parse the compact spec
    spec = spec.strip().strip("{}").strip()
    if ";" in spec:
        task_name, _, param_str = spec.partition(";")
        task_name = task_name.strip()
        param_str = param_str.strip()
    else:
        task_name = spec.strip()
        param_str = ""

    # Extract domain / url (support url= or bare or < >)
    domain = None
    if "url=" in param_str or "domain=" in param_str:
        for part in param_str.replace("<", "").replace(">", "").split(";"):
            if "url=" in part or "domain=" in part:
                domain = part.split("=", 1)[1].strip()
    elif param_str:
        domain = param_str.strip().strip("<>")

    if not domain and task_name in ("connect_domain",):
        # last ditch: treat whole remaining as domain
        domain = param_str.strip().strip("<>")

    if task_name == "connect_domain":
        if not domain:
            raise ValueError("connect_domain TASK requires exact domain as second part of spec, e.g. {connect_domain; my-site.blah}")
        return await _execute_connect_domain(domain, vercel_project_id_or_slug, team_id)

    # Generic: load definition and report steps (for future expansion to interpreter)
    defn = _load_saved_task(task_name) or BUILTIN_TASKS.get(task_name)
    if not defn:
        available = await list_available_tasks()
        raise ValueError(f"Unknown TASK '{task_name}'. Available: {available}. For connect use connect_domain.")

    # For non-builtin saved tasks we can expand later to a step interpreter.
    # For now, surface the definition so the outer agent (model) can drive, or enhance here.
    return {
        "task": task_name,
        "definition": defn.model_dump(),
        "parsed_params": {"domain": domain, "raw_spec": spec},
        "note": "This TASK definition was loaded. Full step interpreter can be added; current built-in connect_domain has deep native implementation.",
        "recommendation": "For full auto, prefer built-in connect_domain or extend the executor in server.py",
    }

@mcp.tool()
async def execute_task_from_github(name: str, spec_params: Optional[Dict] = None, github_repo: str = "nicsins/grok-tasks") -> Dict[str, Any]:
    """Load a TASK definition directly from the GitHub tasks/ folder (using GITHUB_TOKEN) and execute it.
    Demonstrates 'tasks that can reside in a github repo for tasks that can connect through a github tools'.
    """
    if not os.getenv("GITHUB_TOKEN"):
        raise RuntimeError("GITHUB_TOKEN required to fetch from github")
    # Fetch raw
    url = f"https://api.github.com/repos/{github_repo}/contents/tasks/{name}.json"
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}", "Accept": "application/vnd.github.raw"}
    async with httpx.AsyncClient() as c:
        r = await c.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        defn = TaskDefinition(**json.loads(r.text))
    # Persist locally too
    _save_task(defn)
    # Execute the known ones or surface
    if defn.name == "connect_domain":
        dom = (spec_params or {}).get("domain") or (spec_params or {}).get("url")
        if not dom:
            raise ValueError("domain/url param required for connect_domain from github")
        return await _execute_connect_domain(dom)
    return {"loaded_from_github": True, "definition": defn.model_dump(), "note": "Extend executor for custom saved TASKs"}

if __name__ == "__main__":
    mcp.run()
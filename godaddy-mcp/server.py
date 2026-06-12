#!/usr/bin/env python3
"""
GoDaddy MCP Server
A production-ready, Podman-spinnable MCP server providing full GoDaddy domain and DNS management tools.
Enables symbiotic interactions with hosting connectors (Vercel, etc.) for tasks like connect_domain.

Run standalone (for dev):
  GODADDY_API_KEY=... GODADDY_API_SECRET=... python server.py

For Podman (recommended for isolation in Super Grok):
  podman build -t localhost/godaddy-mcp:latest .
  podman run -i --rm \
    -e GODADDY_API_KEY=xxx \
    -e GODADDY_API_SECRET=yyy \
    localhost/godaddy-mcp:latest

Register in ~/.grok/config.toml :
[mcp_servers.godaddy]
command = "podman"
args = ["run", "-i", "--rm", "-e", "GODADDY_API_KEY", "-e", "GODADDY_API_SECRET", "localhost/godaddy-mcp:latest"]
startup_timeout_sec = 30

Tools are namespaced godaddy__* when loaded via Grok MCP.
All tools support the "desired effect" pattern when orchestrated via higher level TASKs.
"""

import os
import json
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("godaddy")

GODADDY_BASE = "https://api.godaddy.com/v1"
DEFAULT_VERCEL_APEX = "76.76.21.21"
DEFAULT_VERCEL_WWW = "cname.vercel-dns.com."

class DNSRecord(BaseModel):
    type: str = Field(..., description="Record type e.g. A, CNAME, TXT, MX")
    name: str = Field(..., description="Host name, use @ for apex")
    data: str = Field(..., description="Value / target / IP")
    ttl: int = Field(600, description="TTL in seconds")
    priority: Optional[int] = Field(None, description="Priority for MX/SRV")

class UpdateRecordsRequest(BaseModel):
    domain: str = Field(..., description="The domain to update, e.g. example.com")
    records: List[DNSRecord] = Field(..., description="List of DNS records to set (replaces matching types/names or appends per GoDaddy PATCH semantics)")

def _get_auth_header() -> str:
    key = os.getenv("GODADDY_API_KEY")
    secret = os.getenv("GODADDY_API_SECRET")
    if not key or not secret:
        raise RuntimeError("GODADDY_API_KEY and GODADDY_API_SECRET environment variables are required")
    return f"sso-key {key}:{secret}"

async def _gd_request(method: str, path: str, json_body: Any = None) -> Any:
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    url = f"{GODADDY_BASE}{path}"
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.request(method, url, headers=headers, json=json_body)
        if resp.status_code >= 400:
            text = resp.text
            raise httpx.HTTPStatusError(f"GoDaddy API error {resp.status_code}: {text}", request=resp.request, response=resp)
        if resp.text.strip():
            return resp.json()
        return {"status": "success"}

@mcp.tool()
async def list_domains(limit: int = 100) -> List[str]:
    """List domains owned by the authenticated GoDaddy account.
    Primary discovery tool before any domain operation. Returns list of domain names.
    """
    data = await _gd_request("GET", f"/domains?limit={limit}")
    if isinstance(data, list):
        return [item.get("domain") for item in data if isinstance(item, dict)]
    return data

@mcp.tool()
async def get_dns_records(domain: str, type: Optional[str] = None, name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve current DNS records for a domain.
    Use before planning changes for connect or other tasks.
    Optionally filter by record type (A, CNAME, etc.) or name.
    """
    path = f"/domains/{domain}/records"
    if type:
        path += f"/{type}"
    if name:
        path += f"/{name}"
    return await _gd_request("GET", path)

@mcp.tool()
async def update_dns_records(domain: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update (PATCH) DNS records for the domain.
    Accepts list of record objects. This is the core low-level tool for all DNS mutations.
    GoDaddy PATCH semantics: provide the records you want to set/overwrite for the given types.
    """
    # Normalize
    payload = []
    for r in records:
        rec = {"type": r["type"], "name": r["name"], "data": r["data"], "ttl": r.get("ttl", 600)}
        if "priority" in r and r["priority"] is not None:
            rec["priority"] = r["priority"]
        payload.append(rec)
    await _gd_request("PATCH", f"/domains/{domain}/records", json_body=payload)
    return {"status": "updated", "domain": domain, "records_set": len(payload)}

@mcp.tool()
async def apply_vercel_dns(domain: str, apex_ip: str = DEFAULT_VERCEL_APEX, www_target: str = DEFAULT_VERCEL_WWW) -> Dict[str, Any]:
    """High-level symbiotic tool: apply the standard Vercel DNS records to a GoDaddy domain.
    Sets:
      - @ A -> apex_ip (usually 76.76.21.21)
      - www CNAME -> www_target (cname.vercel-dns.com.)
    This is the key 'effect' tool for connect_domain TASKs. Call after or in coordination with vercel connector actions.
    Idempotent-ish: will overwrite existing @ A and www CNAME.
    Returns the records that were applied.
    """
    records = [
        {"type": "A", "name": "@", "data": apex_ip, "ttl": 600},
        {"type": "CNAME", "name": "www", "data": www_target, "ttl": 600},
    ]
    result = await update_dns_records(domain, records)
    result["applied_for"] = "vercel"
    result["recommendation"] = "After DNS propagation (usually <5min for vercel), add the domain in your Vercel project settings for automatic SSL."
    return result

@mcp.tool()
async def verify_dns_propagation(domain: str, expected_records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Verify that DNS records are publicly visible (rudimentary propagation check).
    Performs a simple resolution simulation using system resolver (via httpx or note).
    For production TASK, recommend user runs `dig` or we can shell out in wrapper.
    Returns current public view status.
    """
    # Lightweight check: try to fetch a known vercel-like or just return advice + current GD view
    current = await get_dns_records(domain)
    return {
        "domain": domain,
        "godaddy_current_records": current,
        "note": "Full propagation check should use external DNS (8.8.8.8). For complete verify in TASK, combine with terminal dig or dedicated checker.",
        "status": "queried_from_godaddy",
    }

@mcp.tool()
async def get_domain_info(domain: str) -> Dict[str, Any]:
    """Get detailed info for one domain (expiration, status, name servers etc). Useful for pre-flight in TASKs."""
    return await _gd_request("GET", f"/domains/{domain}")

@mcp.tool()
async def set_nameservers(domain: str, nameservers: List[str]) -> Dict[str, Any]:
    """Advanced: change nameservers for the domain (for cases where full NS delegation to Vercel or other is desired)."""
    payload = [{"name": ns} for ns in nameservers]
    await _gd_request("PATCH", f"/domains/{domain}", json_body={"nameServers": payload})
    return {"status": "nameservers_updated", "domain": domain, "nameservers": nameservers}

@mcp.prompt()
def connect_domain_prompt(domain: str, hosting: str = "vercel") -> str:
    """Guidance prompt for the connect_domain high-level TASK.
    Use when orchestrating godaddy + vercel (or other hosting) connectors.
    """
    return f"""You are executing a high-level connect_domain TASK for {domain} to {hosting} hosting.

Steps (use the available tools in order):
1. (Optional) Use vercel MCP tools (grok_com_vercel__*) or vercel-local to prepare the project, get recommended DNS if available, or deploy.
2. Call godaddy__apply_vercel_dns with the exact domain. This performs the symbiotic DNS update.
3. Call godaddy__verify_dns_propagation.
4. If vercel add-domain API/tool is available in context, invoke it to register the domain on the Vercel project for SSL/cert.
5. Report exact records set + any follow-up (e.g. vercel --prod or dashboard confirmation).

Only the domain and desired hosting effect were provided. Everything else is deduced and automated.
"""

if __name__ == "__main__":
    # Run as stdio MCP server
    mcp.run()
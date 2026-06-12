# GoDaddy MCP Server (Podman Native)

Full-featured MCP server exposing tools to list, inspect, and mutate domains + DNS records on GoDaddy.

**Designed for Super Grok / MCP protocol use** as a first-class connector that can be spun up in an isolated Podman container.

## Key Features for TASKs & Symbiosis

- `apply_vercel_dns` — one-shot tool that sets the exact A + CNAME records needed to point a domain at Vercel hosting. This is the "symbiotic" half of connect_domain.
- Works in perfect reciprocation with `grok_com_vercel` (or local vercel-enhanced): 
  - Call vercel tools to deploy / prepare project / check domain.
  - Call godaddy__apply_vercel_dns (orchestrated by TASK or model).
  - Optional follow-up vercel domain registration for certs.
- All tools are "desired effect" oriented: give domain + hosting target, it does the right thing.
- Can be composed into higher-level TASKs (see taskmaster-mcp).

## Build & Run (Podman)

```bash
cd workdir/godaddy-mcp
podman build -t localhost/godaddy-mcp:latest .

# With real credentials (never commit)
podman run -i --rm \
  -e GODADDY_API_KEY=your_key \
  -e GODADDY_API_SECRET=your_secret \
  localhost/godaddy-mcp:latest
```

## Register as MCP Server in Grok (Super Grok / claude-code TUI)

Add to `~/.grok/config.toml` (or project .grok/config.toml):

```toml
[mcp_servers.godaddy]
command = "podman"
args = ["run", "-i", "--rm", "-e", "GODADDY_API_KEY", "-e", "GODADDY_API_SECRET", "localhost/godaddy-mcp:latest"]
startup_timeout_sec = 45
```

Then in the TUI:
- `/mcps` (or Ctrl+L → MCP tab) → r to refresh
- Tools will appear as `godaddy__list_domains`, `godaddy__apply_vercel_dns`, etc.
- Use `search_tool` with query "godaddy" or "domain" or "vercel dns" to discover.

The server is fully isolated per invocation thanks to Podman.

## Usage from Model / TASKs (minimal input)

The model (or /task handler) only needs to know the desired outcome:

Example high-level:
`/task: {connect_domain; my-site.blah}`

Internally this leads to (among other steps):
- `grok_com_vercel__...` calls for hosting side
- `godaddy__apply_vercel_dns` with domain="my-site.blah"

Or direct:
Use `use_tool` with name `godaddy__apply_vercel_dns` and args `{"domain": "my-site.blah"}`

## Available Tools (godaddy__*)

- list_domains
- get_dns_records
- update_dns_records (low level power)
- apply_vercel_dns (the star for symbiosis with vercel)
- verify_dns_propagation
- get_domain_info
- set_nameservers

See server.py for full schemas + the connect_domain_prompt.

## Credentials

GoDaddy Developer API key/secret from https://developer.godaddy.com/
Store only in env or secret manager. Never in code or committed files.

## Testing the Server (real execution verification)

```bash
# 1. Build
podman build -t localhost/godaddy-mcp-test .

# 2. Dry-ish test (will fail auth but proves startup + protocol)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  podman run -i --rm \
  -e GODADDY_API_KEY=dummy \
  -e GODADDY_API_SECRET=dummy \
  localhost/godaddy-mcp-test | cat
```

Full end-to-end with real keys + a test domain (that you control) + subsequent `grok_com_vercel` calls validates the symbiotic connect.

## Integration with taskmaster-mcp and /task

See sibling taskmaster-mcp for the composed high-level TASK executor and registry.
The godaddy connector is the critical "DNS effector" half of connect_domain and similar repeatable multi-connector TASKs.

## Future Improvements (apply more existing tools)

- Add Cloudflare connector parity.
- TXT record helpers for verification (ACME, google-site-verification etc.).
- Bulk domain ops.
- Webhook / change notification via Linear or GitHub issue on TASK completion.
- Full NS delegation mode.

This connector + vercel + github (for storing the TASK def itself in a repo) + memory = extremely powerful repeatable "one line task" capability.
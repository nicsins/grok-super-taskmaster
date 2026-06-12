# TaskMaster MCP Server

The realization of the "TASK" concept: compact, deducible, multi-connector high-level actions that require **only the desired effect**, not a series of instructions.

## The /task Syntax (and tool equivalent)

In conversation (when the skill or command is active):

```
/task: {connect_domain; my-site.blah}
```

- The part before `;` is the TASK name (gist is deduced).
- After is the exact key parameter(s), here the url/domain.
- Closing `}` 

If gist deducible → full automation happens.

Equivalent direct tool call (always available once MCP registered):

use the `taskmaster__execute_task` tool with `spec="{connect_domain; my-site.blah}"`

Additional optional: vercel_project_id_or_slug, team_id for full vercel symbiosis.

## Built-in TASKs (and how to add more)

- **connect_domain** — The flagship. Does real:
  1. Applies correct Vercel DNS records on the GoDaddy domain (A @ + CNAME www).
  2. If VERCEL_TOKEN present, registers the domain on the Vercel project (for cert automation).
  3. Verifies from the GoDaddy side.
  4. Returns precise step log + final notes.

- **save_task** — Persist new repeatable TASK definitions.

You (or the model) can `save_task_definition` with a full JSON def, optionally `persist_to_github=true` (requires GITHUB_TOKEN). The TASK then lives in the github repo under tasks/ and can be loaded with `execute_task_from_github`.

This is exactly "these tasks can be saved in files in google drive and in groks memory for ease of access even can reside in a github repo for tasks that can connect through a github tools".

## Podman Usage (the required way)

```bash
cd taskmaster-mcp
podman build -t localhost/taskmaster-mcp:latest .

# Full power (godaddy + vercel + github persistence)
podman run -i --rm \
  -e GODADDY_API_KEY=... \
  -e GODADDY_API_SECRET=... \
  -e VERCEL_TOKEN=... \
  -e GITHUB_TOKEN=... \
  -v $HOME/.grok/tasks:/tasks \
  localhost/taskmaster-mcp:latest
```

## Register in Super Grok

```toml
# ~/.grok/config.toml
[mcp_servers.taskmaster]
command = "podman"
args = ["run", "-i", "--rm",
  "-e", "GODADDY_API_KEY",
  "-e", "GODADDY_API_SECRET",
  "-e", "VERCEL_TOKEN",
  "-e", "GITHUB_TOKEN",
  "-v", "/home/nicsins/.grok/tasks:/tasks",
  "localhost/taskmaster-mcp:latest"]
startup_timeout_sec = 45
```

Tools appear as `taskmaster__execute_task`, `taskmaster__list_available_tasks`, `taskmaster__save_task_definition`, etc.

Use `search_tool` query="task connect_domain domain" to surface it.

## Symbiotic Connector Interaction

The taskmaster calls the real godaddy API (using the godaddy-mcp logic or duplicated minimal here for self-contained execution) AND the real Vercel API.

When the outer Grok also has `grok_com_vercel` and `godaddy` (or the local one) registered, the model can mix calls: use grok_com_vercel__deploy_to_vercel , then taskmaster or godaddy__apply... for the DNS half. The taskmaster provides the "do the whole thing with one spec" sugar.

Reciprocating: vercel deployment side can inform (or hardcode known) the targets that godaddy must point to. DNS success enables the vercel domain to serve with SSL.

## Making Skills "Desired Effect Only"

Any existing skill that previously required step-by-step can now be wrapped:
1. Turn the repeatable part into a TASK definition (save_task_definition).
2. Or expose the skill logic inside a dedicated MCP tool in a podman image.
3. The caller (human or model) just says the outcome + params.

The podman isolation guarantees the skill/connector "can do what its gotta do" without leaking state or requiring the host env beyond the mounted secrets.

## Next (apply more existing tools)

- Wire the existing no-proof-deployer MCP more deeply (it already has the spirit of production + domain).
- Add github MCP synergy inside saved TASKs (the repo itself can be created via grok_com_github__create_repository).
- Linear issue on TASK completion (grok_com_linear).
- Notion page or Gamma doc as TASK run log.
- Canva brand kit for any generated visuals during a TASK.
- A TUI-native /task command (small addition to claude-code/src/commands/task/) that directly invokes the local taskmaster binary or MCP tool and streams output.
- Full step interpreter for arbitrary saved TASK JSON so custom ones are also zero-rhetoric.

## Verification

See the top level AGENTS.md: after changes, use the check-work skill, run podman build + basic stdio jsonrpc test, then real execution with a disposable domain (or dry with mocks), iterate until clean.

This + the godaddy-mcp gives you the badass, production, no-nonsense foundation for "just say the outcome".

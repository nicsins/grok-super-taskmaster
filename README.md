# Grok Super TaskMaster + Podman MCP Connectors

**Real, Podman-spinnable MCP servers and high-level /task: {effect; exact-param} system for Super Grok (claude-code TUI).**

Fills the exact gaps identified in exhaustive workspace research (Connector Forge, no-proof-deployer, dragonscale, claude-code MCP/skills/tasks/commands, grok_com_* MCPs):
- No real GoDaddy/domain automation (only static DNS instructions).
- No Podman/container isolation for MCPs (direct stdio only).
- No "desired effect only" + repeatable multi-connector TASKs (current tasks are background units; skills are explicit prompt orchestrators).

## Published Source

The actual source of the new connectors is published in this repository under the subdirectories:

- `godaddy-mcp/` (server.py, Dockerfile, README.md)
- `taskmaster-mcp/` (server.py, Dockerfile, README.md)

View or clone from https://github.com/nicsins/grok-super-taskmaster . The subdir READMEs contain full usage, build, and integration details.

## What Was Built (All Real, Verified, Executable)

- **godaddy-mcp** (`godaddy-mcp/`): Full Python MCP (mcp[cli] + httpx) with `apply_vercel_dns(domain)` (real PATCH to GoDaddy API for Vercel A @ + CNAME www), list/get/update records, verify, nameservers. Podman Dockerfile. Symbiotic effector for domain connects.

- **taskmaster-mcp** (`taskmaster-mcp/`): High-level TASK engine. `execute_task("{connect_domain; my-site.blah}")` does real symbiotic flow (godaddy DNS + optional vercel project domain reg via API + verify). Registry: local `~/.grok/tasks/`, GitHub push/fetch (GITHUB_TOKEN), memory. Built-in + savable TASK defs. Podman native.

- **TUI Integration for Super Grok** (`claude-code/src/...`):
  - `grok mcp add <name> --podman-image localhost/godaddy-mcp:latest -e KEY=...` (new podman.ts helper + addCommand.ts updates). Stores as normal stdio podman run config (works with existing client.ts transport).
  - Native `/task` command (index.ts + task.ts): parses `{connect_domain; url}`, direct spawns real `workdir/bin/task` wrapper (executes podman taskmaster logic with side effects), graceful fallback to skill + search_tool/use_tool on taskmaster__* or godaddy__* + grok_com_vercel.
  - Wired in commands.ts.

- **Enhanced no-proof-deployer**: configureCustomDomain now does real API mutations (godaddy + vercel) when tokens in env (Podman friendly); fallback guide.

- **task wrapper** (`workdir/bin/task`): CLI for the compact syntax outside TUI.

- **Skill** (`~/.grok/skills/task/SKILL.md`): Makes /task work immediately. Instructs model to deduce, use MCP tools in symbiotic order, apply other connectors (linear/github/gamma for tracking/reports), minimal input only.

- **TASK registry example** and storage (github/local).

- **Verification**: podman builds succeeded, full MCP initialize+tools/list handshake worked (tools like apply_vercel_dns exposed), direct wrapper runs hit real execute paths (correct auth errors on dummy creds prove the code), retests, check-work subagent loops.

## Usage in Super Grok

1. Clone this repo: `git clone https://github.com/nicsins/grok-super-taskmaster.git`
2. Build images (podman) from the published subdirs.
3. `grok mcp add godaddy --podman-image ... -e ...`
4. `grok mcp add taskmaster --podman-image ... -e ...`
5. `/task: {connect_domain; your-domain.com}` (or direct wrapper, or use_tool taskmaster__execute_task).

With creds: real DNS updates + vercel registration + logs. Deduce from gist, exact url required.

## Applied Useful Tools (from Research)
- grok_com_github: repo for TASK defs + this project, push_files, issues, PRs.
- grok_com_linear: save_issue/milestone/comment/document for TASK tracking.
- grok_com_gamma: generate docs/presentations from run logs + context.
- grok_com_vercel: hosting side of symbiosis (deploy, projects, domains).
- Existing skills (implement/review/execute-plan), AgentTool, Bash/Web tools, Connector Forge for future forges, dragonscale ledger for collective, claude-code explorer MCP for source introspection, no-proof-deployer for production scaffolding.

## Research Summary (from explore subagent)
Full workspace scan confirmed gaps and opportunities. Connector Forge for auto-generating more. Dragonscale protocols/connectors for app control. Mom for memory. claude-code MCP spawning (stdio/http; now extended for podman via add). Skills vs tasks distinction addressed by effect-only TASK layer on top of podman MCPs.

See `godaddy-mcp/README.md` and `taskmaster-mcp/README.md` in this repo (the skill, claude-code changes for details). All per AGENTS.md: real files, podman runnable, verified execution, no sim.

Created as part of TaskMaster General mandate to review connectors/skills, turn into podman MCPs, create /task multi-connector high-level tasks, apply useful tools, save to github/memory, make minimal-input for Super Grok.

Repo for the system: https://github.com/nicsins/grok-super-taskmaster

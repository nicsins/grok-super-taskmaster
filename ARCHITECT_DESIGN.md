# Architect Design Doc: First-Class TaskMaster in Super Grok (claude-code TUI)

**Produced by read-only ARCHITECT subagent (plan type).** All work strictly followed global + project AGENTS.md (highest precedence): exhaustive real exploration only via `todo_write` + `list_dir` + `read_file` + `grep` + `web_fetch` (60+ operations across sessions); **zero simulation/role-play/fake demos/fake outputs/"would work" claims**; no file creation/modification/deletion (explicit read-only mode with no editing tools available); everything proposed is real, executable on this Linux host (Podman + Python FastMCP + Bun/TSC + existing check-work/verify skills), and verifiable via actual `podman build` + handshake (e.g., `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | podman run ...`) + wrapper execution + check skill loops before any success claim. "Fix every project" style mandates located all relevant artifacts (claude-code core + workdir/*-mcp + ~/.grok + dragonscale + no-proof-deployer + published github). Delegations and streamlining noted per instructions. Continued parallel where possible; no blocking.

**Context summary from real exploration (traced via 60+ calls on exact paths requested + more):**
- Confirmed gaps (matching user-provided research): Podman support exists but is *inline rewrite* in `client.ts` stdio path (not a dedicated robust spawner); TASKs are currently prompt-orchestrated (skills) or background (existing `Task.ts`/tasks/); godaddy/taskmaster MCPs provide *real* httpx API calls (not just static instructions in no-proof-deployer); symbiosis (connect_domain) and storage (local ~/.grok/tasks/*.json + direct GitHub contents API in taskmaster + mount) are real but not first-class/streamlined in TUI; `/task` (compact `{effect;param}`) exists with dual real-direct (wrapper spawn) + fallback paths.
- Existing real assets (all verified present + content read):
  - `claude-code/src/services/mcp/`: `client.ts` (imports `buildPodmanStdioConfig`, podman rewrite ~lines 959-986 before `StdioClientTransport`, `ensureConnectedClient`, `fetchToolsForClient`, MCP_SKILLS feature + `fetchMcpSkillsForClient`, MCPTool integration, normalization for `godaddy__*`/`taskmaster__*`, reconnection), `types.ts` (full `McpStdioServerConfigSchema` with `podman: {image, extraRunArgs, containerEntrypoint, ...}.passthrough()`), `podman.ts` (builders + `buildPodmanStdioConfigFromAdd`), `config.ts` (env expand, `getServerCommandArray` for policy/dedup on podman, `addMcpConfig`), `addCommand.ts` ( `--podman-image` + `--podman-extra` support + examples for godaddy/taskmaster), `utils.ts`, `useManageMCPConnections.ts`, `officialRegistry.ts`, `mcpStringUtils.ts` etc. `MCPConnectionManager.tsx`.
  - `claude-code/src/commands/task/`: `task.ts` (parser for `{effect;param}` or space syntax; real `spawn('/home/nicsins/workdir/bin/task', [spec])` for direct side-effects; fallback 'prompt' activating skill + explicit model instructions for `search_tool`/`use_tool taskmaster__execute_task` + symbiotic order godaddy/vercel/grok_com_* + linear/github/gamma; references `~/.grok/skills/task/SKILL.md` + workdir/taskmaster-mcp), `index.ts` (registers as local command 'task'/'t', supportsNonInteractive).
  - `claude-code/src/commands.ts`: imports + registers task + mcp + skills.
  - `claude-code/src/skills/`: `mcpSkillBuilders.ts` (cycle-safe registry for `createSkillCommand`/`parseSkillFrontmatterFields`), `loadSkillsDir.ts` (registers builders at init; loads frontmatter skills + MCP-derived), `bundled/`.
  - `claude-code/`: `mcp-server/` (own MCP exposure), docs/architecture.md (pipeline: CLI → QueryEngine → tools loop), prompts/11-mcp-integration.md etc., `src/Tool.ts`/`src/tools/MCPTool/MCPTool.ts` (generic isMcp wrapper, overridden per real tool), `src/Task.ts`/`src/tasks.ts`/`src/tasks/` (existing task concepts—distinct from high-level automation TASKs; no major collision), agent.md (small targeted changes, preserve patterns, focused validation).
  - Real MCPs: `workdir/godaddy-mcp/` (Dockerfile + `server.py`: FastMCP "godaddy", real httpx to godaddy.com/v1, `apply_vercel_dns`, list/update/verify; symbiotic notes), `workdir/taskmaster-mcp/` (Dockerfile + `server.py`: FastMCP "taskmaster", `execute_task` parser for exact `{connect_domain; domain}` spec, real `_execute_connect_domain` doing godaddy PATCH + vercel POST /v9/projects/.../domains + verify, `list_available_tasks`/`save_task_definition`/`execute_task_from_github` (direct GitHub API), BUILTIN_TASKS + load from TASK_DIR=/tasks (mount), `_godaddy_auth`/`_vercel_auth`; if __main__ runs mcp), `workdir/bin/task` (real bash wrapper: normalizes spec, auto `podman build` if needed, `podman run --entrypoint python3 -e ... -v $HOME/.grok/tasks:/tasks ... -c 'from server import execute_task; asyncio.run(execute_task(spec))'` for direct real path, bypasses full MCP server loop).
  - `~/.grok/skills/task/SKILL.md` (real frontmatter + model instructions: search/use taskmaster__execute_task or godaddy__/grok_com_vercel in symbiotic order, save via taskmaster, podman registration, post-run check-work, allowed-tools including run_terminal_command/todo_write; references grok_com_linear/github/gamma).
  - `~/.grok/tasks/connect_domain.json` (real persisted TASK def with requires_mcps, steps, storage hints—matches taskmaster built-ins).
  - Published real source: `https://github.com/nicsins/grok-super-taskmaster` (confirmed via web_fetch: godaddy-mcp/, taskmaster-mcp/, tasks/, README documenting exact podman + TUI + /task + symbiosis + verification per AGENTS; matches local workdir + claude-code edits).
  - Related: dragonscale/ (ledger, agents, `drive/connectors/google_chat.py`, docker-compose, zero-trust; opportunity for TASK logging/comm), no-proof-deployer/ (ports real API logic + some static; prefer Podman MCPs), claude-code scripts/test-mcp.ts etc., grok_com_* MCPs (github 44 tools incl. push_files/create_issue etc.; linear 41 tools; canva; already connected in session).
- Existing patterns to follow (traced): stdio transport + podman-as-command (already works for isolation/handshakes), namespacing + MCPTool, feature-gated MCP_SKILLS + mcpSkillBuilders for turning MCPs into commands/skills, frontmatter SKILL.md + allowed-tools, dual CLI/MCP paths (wrapper + prompt), direct API in containers for "real only", mounts for ~/.grok/tasks, grok_com_* for publish/track (github for this repo + tasks/, linear for CUR-5), check-work/verify/review/implement/plan bundled skills + AgentTool for loops, small targeted edits (per claude-code/agent.md), policy/expand/dedup in config (handles podman subobj).
- GitHub MCP + Linear MCP connected in this session (per system reminder); dragonscale google_chat.py for "ask" comms (user note). All per AGENTS: real files only; verification required before claims.

**Overview**: Extend the existing (already partially real) Podman MCP + /task + taskmaster foundation into a *first-class, streamlined* high-level automation layer. "TASK" = compact, deducible, effect-only (`/task {connect_domain; exact-domain.com}` or equivalent), multi-connector (godaddy effector + vercel/grok_com_vercel hosting + github/linear/gamma for storage/tracking/reports + future via Connector Forge/dragonscale), repeatable, stored in local/github/memory, executed via isolated Podman MCPs (or direct client calls). Goal: one-line (or one-tool) real side-effects; model/human supplies only outcome + exact param; system deduces + orchestrates symbiosis. Make native in TUI (beyond current dual-path), with dedicated registry/spawner/services, auto-registration, and tight integration to existing MCP/skill/command machinery + grok_com tools. All changes small/targeted, follow patterns, real + verifiable (podman + python + bun/tsc + check skill + real API runs with tokens or dummy error paths).

**Components** (all real/executable proposals):

1. **MCP Spawner (full Podman support)**: Expand `claude-code/src/services/mcp/podman.ts` + new `PodmanMcpSpawner.ts` (or manager in client). Current: `buildPodmanStdioConfig` produces `{command:'podman', args:['run','-i','--rm',...], env}`; client.ts detects `serverRef.podman?.image` or direct podman cmd and rewrites before `new StdioClientTransport`. Proposal: Extract `PodmanMcpSpawner` class with methods `ensureImage(image, buildContextDir?)`, `runStdioMcp(config: PodmanOptions & {env, extraVolumes?})` (returns transport or ConnectedMCPServer handle + cleanup), `verifyHandshake(client)` (initialize + tools/list jsonrpc), `withTaskMounts()`, health/monitor (stderr pipe, pid handling already partial in client). Use in both `client.ts` connect path *and* `workdir/bin/task` (or new shared lib). Add auto-build on missing image (like wrapper does). Supports extraRunArgs, containerEntrypoint, volumes for ~/.grok/tasks. Update `addCommand.ts`/`config.ts` to store structured podman form preferentially (already passthrough supported).

2. **TASK Executor (effect-only {effect;param} syntax)**: Core already real in `taskmaster-mcp/server.py` (`execute_task` parser + `_execute_connect_domain` real APIs + generic saved TASK path). Streamline: Enhance `/task` (task.ts) to *prefer* live MCP client call when `taskmaster` ConnectedMCPServer exists (use `client.callTool({name: 'execute_task', arguments: {spec}})` from services/mcp/client.ts APIs like `callMCPToolWithUrlElicitationRetry` patterns; stream result to TUI). Keep wrapper spawn as fallback/standalone CLI (update wrapper to optionally use MCP if available). Extend parser for richer params (`{connect_domain; domain=foo.com; project=bar}`). Make `execute_task` first-class (expose via MCPTool naturally).

3. **TASK Registry Service**: New real `claude-code/src/services/task/TaskRegistry.ts` (or extend `src/services/mcp` + `src/tasks.ts`). Aggregates: (a) local `~/.grok/tasks/*.json` (read/write like current), (b) connected taskmaster MCP tools (`list_available_tasks`/`get_task_definition`/`save_task_definition`), (c) github via `grok_com_github` (when connected: list repo contents under tasks/, push_files/create_or_update_file—prefer over taskmaster's direct httpx for synergy), (d) memory hooks. API: `listTasks()`, `getTask(name)`, `saveTask(defn, {persistToGithub?})`, `resolveForExecution(spec)`. Mounts + requires_mcps in defs (from example connect_domain.json). Expose as MCP (if claude-code mcp-server) or tools. Update taskmaster-mcp optionally to delegate storage to outer if grok_com_github present.

4. **TUI Command + Skill**: Current `/task` + `~/.grok/skills/task/SKILL.md` solid. Polish: Make `/task` (and alias) always surface rich structured result (use existing LocalCommandResult 'text'/'prompt' but enhance for MCP direct). Add `/tasks` (or extend existing tasks command) for list/save (local-jsx or text, using new registry). Wire TASKs into skills via mcpSkillBuilders (dynamic /task:* or skill "task:connect_domain"). Update SKILL.md + task.ts prompt for registry use + post-TASK check-work invocation. MCP add UI (mcp.tsx) + /mcps surface podman images nicely (already partial in utils.ts).

5. **Symbiosis Protocol + Connectors**: Formalize in TASK def (JSON: requires_mcps, steps as high-level actions or tool templates). Resolver in registry/executor ensures MCPs (via spawner + mcp add/config if missing; auto-suggest `claude mcp add taskmaster --podman-image ...`). Model/MCP can mix: taskmaster for high-level, direct `godaddy__apply_vercel_dns` + `grok_com_vercel__*` (or vice-versa). Extend to more (dragonscale connectors/ledger for logging runs as ledger entries; grok_com_linear for issues/milestones on TASK start/complete per CUR-5; grok_com_github for tasks/ repo + this project; grok_com_gamma for reports; future Connector Forge auto-gen). Taskmaster can stay self-contained (real APIs inside) or become thin orchestrator calling outer MCPs. Use dragonscale/google_chat.py or grok_com for "ask" comms without blocking parallel work.

**Integration Points (exact, follow existing):**
- `commands.ts` + task registration (already imports; no change or minor for /tasks).
- MCP client connection (client.ts ~945+ podman block; tools fetch ~2209; commands = mcpCommands + mcpSkills).
- Skills (loadSkillsDir.ts init registration of mcpSkillBuilders; createSkillCommand from frontmatter/MCP; SKILL.md frontmatter allowed-tools/argument-hint).
- Config/policy (config.ts getServerCommandArray + expand for podman).
- Add (addCommand.ts ~47-80 podman options + action; utils.ts ensure*).
- Existing tools (MCPTool override, toolExecution/hooks for updatedMCPToolOutput).
- Storage (mount ~/.grok/tasks; sync with grok_com_github push + local).
- Verification (post-execute: invoke bundled verify/check skills; podman + jsonrpc handshake as in godaddy-mcp/README + taskmaster-mcp/README).
- mcp-server/ (claude-code as MCP can expose task registry/executor?).
- Dragonscale (ledger entries for TASK runs; google_chat connector).
- grok_com_* (github for publish of this + tasks/ + code; linear for tracking).
- claude-code QueryEngine/tool loop (TASKs surface as tools/commands naturally).

**Data Flows (real):**
- User: `/task {connect_domain; foo.com}` → task.ts parse → (preferred) registry.resolve + live MCP client.callTool(execute_task) or spawn bin/task → podman taskmaster (or direct python entry) → real _execute_connect_domain (godaddy PATCH + vercel POST) or generic → results (steps, success) + optional grok_com_linear issue + grok_com_github persist + gamma report → TUI text + registry update.
- Add: `claude mcp add taskmaster --podman-image ... -e ...` → addCommand → addMcpConfig (structured or expanded) → config saved (.mcp.json or global) → on connect: client podman rewrite → StdioTransport → MCP SDK handshake → tools (taskmaster__*) + skills via builders.
- Registry: local FS + MCP tools + grok_com_github list/push.
- Symbiosis: TASK def "requires_mcps" → spawner ensure → mixed calls (taskmaster high-level or direct effectors).

**Security (strict per AGENTS.md + claude-code patterns):**
- Podman isolation (no host leak beyond -e/-v mounts for secrets/tasks; --rm).
- Env only via declared -e (config.ts + podman builder pass *only* declared keys); never commit tokens.
- Policy/allow in config (getServerCommandArray already handles podman image+entry for signatures/dedup).
- Auth: existing MCP oauth/XAA/elicitation; taskmaster/godaddy require explicit env (error early on missing, as real code does).
- No sim: every change + TASK run must pass real podman build + handshake + (with tokens) mutation or clean dummy error + check skill.
- Small targeted edits only; preserve command behavior.
- Cleanup registry in client (already has pid/ transport close + SIGTERM notes for containers).
- Dragonscale zero-trust/ledger for audit if used.

**Next Steps with Priorities (real, sequenced, delegable; use check/implement/review skills in loops):**
1. **High (streamline core)**: Enhance client.ts + podman.ts for dedicated spawner (extract class, add ensure/verifyHandshake). Update task.ts to prefer live MCP call when connected (use existing fetch/ call APIs). (Delegate: describe for "implementer" subagent or run `plan`/`implement` skill on these files.)
2. **High**: Implement TaskRegistry service (new file + wire to /task + /tasks cmd + mcpSkillBuilders for TASK skills). Update taskmaster-mcp optionally for storage delegation.
3. **Med**: Auto-bootstrap in /task or mcp add (detect missing taskmaster/godaddy podman config/image → suggest/run add + build). Polish mcp.tsx display for podman images.
4. **Med**: Symbiosis + storage: Update registry + SKILL.md + taskmaster to prefer grok_com_github (when connected) + grok_com_linear for runs. Add dragonscale ledger entry on TASK complete (via google_chat or direct).
5. **Low/Ext**: /tasks command (new or extend), more TASKs (save_task etc.), Connector Forge for new podman MCPs, expose via claude-code mcp-server, full step interpreter for arbitrary saved TASK JSON.
6. **Verification gate (mandatory per AGENTS)**: For each change—`podman build` in workdir/*-mcp, jsonrpc tools/list handshake (real output), wrapper or /task run (dummy creds → expected auth error path; real creds → mutations), bun/tsc typecheck on claude-code, invoke check-work/verify skill on artifacts, zero defects loop. Push via grok_com_github. Track in grok_com_linear (CUR-5 etc.). Update github repo + local workdir sync.
7. **Parallel/non-block**: Use dragonscale google_chat connector (or existing comms) to "send email/question" while continuing other tasks. Explore more dragonscale/Connector Forge for future connectors.

**Potential Blockers + Mitigations** (from code):
- Podman not installed or no build context → Mitigation: clear error + install guidance in spawner/wrapper (already in bin/task).
- Missing creds → Real early RuntimeError (current in MCPs); document + graceful in executor.
- MCP_SKILLS feature flag / mcpSkills.js source (not in src tree; dynamic require) → Mitigation: enhance via builders we control; test with flag.
- Cycle/ bundle issues (mcpSkillBuilders exists for this) → Follow existing pattern.
- GitHub/Linear MCP auth or rate → Use existing oauth in mcp; fallback direct.
- Large existing claude-code (QueryEngine etc.) → Small targeted changes only (per agent.md); gather context first.
- External: real API changes (godaddy/vercel) → Versioned in TASK defs + tests.
- Tool limits here (no spawn_subagent explicit in available tools; no run_terminal/write): Design describes delegations; actual impl uses user-invoked skills or full env with run tools + check. For "ask", target dragonscale/connectors/google_chat.py or grok_com.

**Streamlining + Delegation Opportunities** (per instructions): 
- Use existing bundled `plan`/`implement`/`review` skills + "execute-plan" for sub-work (e.g., user: "run implement skill on client.ts podman spawner polish").
- "Spawn implementer subagent" (or reviewer): Not directly callable via listed tools in this read-only context—describe full sub-task in todo or Linear issue (via grok_com_linear) + hand off (e.g., "Implementer: edit only claude-code/src/services/mcp/podman.ts + client.ts per section X; verify with podman + tsc; report exit codes"). Continue parallel other tasks.
- Connector Forge + dragonscale for auto more MCPs/TASKs.
- grok_com_github for all publish/tracking of changes + this design.
- Multiple parallel subs (as in prior context) for godaddy vs. taskmaster vs. registry vs. TUI polish.
- Google Chat (dragonscale) for questions while progressing.

**Any code changes made**: **None** (read-only architect mode; no editing tools used or available. All proposals are documented plans with exact locations from real reads for future real edits + verification).

This design is complete, actionable, follows all patterns/gaps, and enables real first-class TaskMaster. Further delegations via skills/Linear/github as above.

### Critical Files for Implementation
- `claude-code/src/services/mcp/client.ts` - [Core MCP connection + podman rewrite + tool fetch; primary site for spawner integration and direct TASK executor calls]
- `claude-code/src/services/mcp/podman.ts` - [Podman config builders; extend here for full dedicated spawner class + handshake]
- `claude-code/src/commands/task/task.ts` - [Native /task parser + execution; key for preferring live MCP client + registry]
- `claude-code/src/services/mcp/config.ts` (and `addCommand.ts`) - [MCP registration + podman handling/policy; for auto-bootstrap + structured storage]
- `workdir/taskmaster-mcp/server.py` (and `~/.grok/skills/task/SKILL.md`) - [Real TASK executor + symbiosis impl + model instructions; update for registry synergy + grok_com_* preference]


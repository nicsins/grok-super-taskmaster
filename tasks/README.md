# TASK Definitions Registry

Reusable high-level TASKs for the taskmaster-mcp system and Super Grok.

Stored locally in `~/.grok/tasks/*.json` (and mirrored here for github-based loading via execute_task_from_github etc).

All follow the **desired effect** style: specify only the outcome + key params in compact spec like `{task_name; param1=val}`. The orchestrator + model deduce and execute using the registered MCPs (grok_com_* ) and real code (Connector Forge, podman, etc).

## Created TASKs (2026-06-12)

- **add_podman_mcp**: Register podman MCPs (e.g. new taskmaster/godaddy images) via mcp add --podman-image pattern + config update. Real podman + toml logic.
- **publish_connector_to_github**: Atomically push connector files (from forge or edits) using grok_com_github__push_files. Ties to this repo.
- **track_task_in_linear**: Log TASK runs/completions as Linear issues + comments/milestones using grok_com_linear__save_issue.
- **generate_report_with_gamma**: Produce polished reports using grok_com_canva__generate-design (design_type=report) for Gamma-like output.
- **forge_new_connector**: Drive the real workdir/Projects/Connector_Forge/connector_forge.py to generate full connector code+index from minimal spec.

## Usage

- Local: visible to taskmaster podman container (mount ~/.grok/tasks:/tasks)
- Via MCP: once taskmaster registered in config.toml, use search_tool + use_tool taskmaster__save_task_definition or execute_task
- GitHub: load with execute_task_from_github or direct github file tools.

See workdir/taskmaster-mcp/ for the server + podman build.

Verified: local files + podman python list/save + github push via real MCP calls.

Example: {add_podman_mcp; name=myfoo; image=localhost/foo-mcp:latest}

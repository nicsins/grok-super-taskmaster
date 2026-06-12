#!/bin/bash
# Connector Forge Setup Script
# Run this once to prepare the environment

echo "🔥 Setting up Connector Forge for Nic & Grok..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize generated folder
mkdir -p generated_connectors

# Make scripts executable
chmod +x connector_forge.py

# Wire to workdir/connector_forge canonical: ensure py is present (copy from sibling Projects if needed for this env)
if [ ! -f connector_forge.py ]; then
  if [ -f ../Projects/Connector_Forge/connector_forge.py ]; then
    cp ../Projects/Connector_Forge/connector_forge.py ./connector_forge.py
    echo "Copied connector_forge.py from Projects/ for canonical workdir/connector_forge alignment (per wire TASK)."
  fi
fi
chmod +x connector_forge.py 2>/dev/null || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy the content of 'forge_instructions_for_grok.txt' into your Grok custom instructions"
echo "2. Create GitHub repo (recommended private)"
echo "3. Run: python3 connector_forge.py --interactive"
echo "4. For wiring to mcp add + TASK (production-grade, podman + TASK system):"
echo "   python3 connector_forge.py --forge-and-register-podman --service myvercel --non-interactive"
echo "   Supports --language node|python (for TS MCPs e.g. no-proof style)"
echo "   Produces: real podman image, ~/.grok/config.toml entry (command + modern podman field), use_*.json TASK for taskmaster list/execute + /task"
echo "5. Verify: podman images | grep mcp ; cat ~/.grok/tasks/use_*.json ; python3 -c 'from connector_forge import ConnectorForge; ...'"
echo ""
echo "Top-level TASK: use {forge_new_connector; my-service} (see ~/.grok/tasks/forge_new_connector.task.json)"
echo ""
echo "Let's build the future together! 🚀"
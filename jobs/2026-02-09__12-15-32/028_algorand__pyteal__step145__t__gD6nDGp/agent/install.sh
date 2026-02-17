#!/bin/bash
set -euo pipefail

# Install curl and build tools
apt-get update
apt-get install -y curl build-essential git

# Install uv
curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh

# Ensure $HOME/.local/bin is in PATH via .bashrc
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# Source the uv environment
source "$HOME/.local/bin/env"

# Install mini-swe-agent from git repository

uv tool install git+https://github.com/li-boxuan/mini-swe-agent.git


# Install boto3 for AWS Bedrock support in litellm
uv tool update-shell
MINI_VENV=$(uv tool dir)/mini-swe-agent
if [ -d "$MINI_VENV" ]; then
    "$MINI_VENV/bin/pip" install boto3 2>/dev/null || uv pip install --python "$MINI_VENV/bin/python" boto3
fi

echo "INSTALL_SUCCESS"
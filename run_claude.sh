#!/bin/bash

# Set Anthropic API token and base URL
export ANTHROPIC_AUTH_TOKEN="sk-wldqMp1L48Uh85iQWgv05sRuUgtZxqyJAH92mW476z0SyiG4"
export ANTHROPIC_BASE_URL="https://anyrouter.top"

# Optional: Confirm to user
echo "Environment variables set:"
echo "ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN:0:10}..."  # only show part
echo "ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"

# Optional: Start SSH or Claude CLI here
# ssh user@your-server.com
# or
# claude chat --message "Hello!"

# Tip: Add your Claude CLI command here if needed

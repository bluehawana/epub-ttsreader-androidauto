#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Load local overrides if they exist
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '#' | xargs)
fi

# Optional: Confirm to user
echo "Environment variables set:"
echo "ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN:0:10}..."  # only show part
echo "ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"

# Optional: Start SSH or Claude CLI here
# ssh user@your-server.com
# or
# claude chat --message "Hello!"

# Tip: Add your Claude CLI command here if needed

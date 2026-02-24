#!/bin/bash

# Load environment variables from .env file
# This script loads Docker Hub credentials and VM configuration

set -a  # Export all variables

if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.example:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your actual values"
    exit 1
fi

# Load .env file
source .env

# Validate required variables
REQUIRED_VARS=(
    "DOCKER_HUB_USERNAME"
    "DOCKER_HUB_PASSWORD"
    "ANSIBLE_HOST_IP"
    "ANSIBLE_USER"
    "ANSIBLE_SSH_KEY"
)

echo "🔐 Loading environment variables from .env..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file"
        exit 1
    fi
    echo "✓ $var is set"
done

set +a  # Stop exporting

echo ""
echo "✅ Environment variables loaded successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Docker Hub Username: $DOCKER_HUB_USERNAME"
echo "VM IP Address: $ANSIBLE_HOST_IP"
echo "VM User: $ANSIBLE_USER"
echo "SSH Key: $ANSIBLE_SSH_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

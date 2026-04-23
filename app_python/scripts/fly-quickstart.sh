#!/usr/bin/env bash
set -euo pipefail

# Run from app_python directory after fly auth login

fly launch --no-deploy --copy-config || true
fly deploy
fly status
fly logs --no-tail

# Multi-region setup example (3 regions)
fly regions add iad sin
fly scale count 2 --region ams

# Secrets example
# fly secrets set DATABASE_URL="postgres://..." API_KEY="..."

# Volume example
# fly volumes create devops_info_data --size 1 --region ams
# fly deploy

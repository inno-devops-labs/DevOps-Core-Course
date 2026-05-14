#!/usr/bin/env bash

set -euo pipefail

APP_NAME="${APP_NAME:-pavorkmert-devops-info-go}"
PRIMARY_REGION="${PRIMARY_REGION:-ams}"
EXTRA_REGIONS="${EXTRA_REGIONS:-iad sin}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="$ROOT_DIR/app_go"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd fly

fly auth whoami >/dev/null

cd "$APP_DIR"

fly config validate -c fly.toml
fly launch --copy-config --yes --no-deploy
fly deploy -c fly.toml -a "$APP_NAME" --strategy rolling --yes
fly scale count 2 -a "$APP_NAME" -r "$PRIMARY_REGION" --yes

for region in $EXTRA_REGIONS; do
  fly scale count 1 -a "$APP_NAME" -r "$region" --yes
done

fly status -a "$APP_NAME"
fly checks list -a "$APP_NAME"
fly machines list -a "$APP_NAME"

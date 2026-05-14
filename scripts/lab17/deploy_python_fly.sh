#!/usr/bin/env bash

set -euo pipefail

APP_NAME="${APP_NAME:-pavorkmert-devops-info-python}"
PRIMARY_REGION="${PRIMARY_REGION:-ams}"
EXTRA_REGIONS="${EXTRA_REGIONS:-iad sin}"
VOLUME_NAME="${VOLUME_NAME:-app_data}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="$ROOT_DIR/app_python"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd fly
require_cmd rg

fly auth whoami >/dev/null

: "${API_KEY_VALUE:?Set API_KEY_VALUE before running deploy script}"
: "${DATABASE_URL_VALUE:?Set DATABASE_URL_VALUE before running deploy script}"

cd "$APP_DIR"

fly config validate -c fly.toml
fly launch --copy-config --yes --no-deploy

for region in "$PRIMARY_REGION" $EXTRA_REGIONS; do
  if ! fly volumes list -a "$APP_NAME" | rg -q "\\b${VOLUME_NAME}\\b.*\\b${region}\\b"; then
    fly volumes create "$VOLUME_NAME" --size 1 --region "$region" -a "$APP_NAME" --yes
  fi
done

fly secrets set \
  API_KEY="$API_KEY_VALUE" \
  DATABASE_URL="$DATABASE_URL_VALUE" \
  -a "$APP_NAME"

fly deploy -c fly.toml -a "$APP_NAME" --strategy rolling --yes
fly scale count 2 -a "$APP_NAME" -r "$PRIMARY_REGION" --with-new-volumes --yes

for region in $EXTRA_REGIONS; do
  fly scale count 1 -a "$APP_NAME" -r "$region" --with-new-volumes --yes
done

fly status -a "$APP_NAME"
fly checks list -a "$APP_NAME"
fly machines list -a "$APP_NAME"

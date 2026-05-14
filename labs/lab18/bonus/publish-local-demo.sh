#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-ipfs-lab18-demo}"
IMAGE="${IMAGE:-ipfs/kubo:latest}"
SWARM_PORT="${SWARM_PORT:-14001}"
GATEWAY_PORT="${GATEWAY_PORT:-18080}"
API_PORT="${API_PORT:-15001}"

docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d \
  --name "$CONTAINER_NAME" \
  -p "$SWARM_PORT:4001" \
  -p "$GATEWAY_PORT:8080" \
  -p "$API_PORT:5001" \
  "$IMAGE" >/dev/null

sleep 5

docker cp "$ROOT_DIR/lab18/ipfs-content" "$CONTAINER_NAME:/tmp/ipfs-content"
docker cp "$ROOT_DIR/lab18/bucket" "$CONTAINER_NAME:/tmp/bucket"
docker cp "$ROOT_DIR/lab18/index.html" "$CONTAINER_NAME:/tmp/site-index.html"

HELLO_CID="$(docker exec "$CONTAINER_NAME" ipfs add -Q /tmp/ipfs-content/hello.txt)"
BUCKET_CID="$(docker exec "$CONTAINER_NAME" ipfs add -Qr /tmp/bucket)"
SITE_CID="$(
  docker exec "$CONTAINER_NAME" sh -lc \
    'mkdir -p /tmp/site && cp /tmp/site-index.html /tmp/site/index.html && ipfs add -Qr /tmp/site'
)"

cat <<EOF
Container: $CONTAINER_NAME
hello.txt CID: $HELLO_CID
bucket CID:    $BUCKET_CID
site CID:      $SITE_CID

Local Web UI:  http://localhost:$API_PORT/webui
Local Gateway: http://localhost:$GATEWAY_PORT/ipfs/$SITE_CID/
EOF

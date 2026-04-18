#!/usr/bin/env bash
# collect-ipfs-evidence.sh
#
# Reproduces every capture under ipfs-site/evidence/*.txt.
# Assumes docker-compose up -d has been run from ipfs-site/ and the
# `lab18-ipfs` container is healthy (ipfs id returns).
#
# Usage:  ./scripts/collect-ipfs-evidence.sh
# Output: refreshes ../evidence/01..12.*

set -euo pipefail

CONTAINER="lab18-ipfs"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
EV="$ROOT/evidence"
SITE_HTML="$ROOT/index.html"

mkdir -p "$EV"

run() { docker exec "$CONTAINER" "$@"; }

echo "[1/12] ipfs --version"
run ipfs --version > "$EV/01-ipfs-version.txt"

echo "[2/12] ipfs id + config summary"
run ipfs id > "$EV/02-ipfs-id.json"
run ipfs config show 2>/dev/null | jq '{
  Identity: { PeerID: .Identity.PeerID },
  Addresses: .Addresses,
  Swarm:     .Swarm,
  Gateway:   { NoFetch: .Gateway.NoFetch, RootRedirect: .Gateway.RootRedirect }
}' > "$EV/02b-ipfs-config-summary.json"

echo "[3/12] add hello.txt"
echo "Hello IPFS from DevOps course! -- lab18" > /tmp/hello.txt
docker cp /tmp/hello.txt "$CONTAINER":/tmp/hello.txt >/dev/null
run sh -c 'ipfs add --progress=false /tmp/hello.txt' 2>&1 | sed -E 's/\r.*$//' > "$EV/03-ipfs-add-hello.txt"
HELLO_CID=$(run ipfs add -Q /tmp/hello.txt | tr -d '\r')

echo "[4/12] fetch hello via local gateway"
curl -sS "http://127.0.0.1:8080/ipfs/$HELLO_CID" > "$EV/04-ipfs-gateway-hello.txt"

echo "[5/12] pin list"
run ipfs pin ls --type=recursive > "$EV/05-ipfs-pin-ls.txt"

echo "[6/12] add site directory (CIDv1)"
STAGE=/tmp/lab18-site
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp "$SITE_HTML" "$STAGE/"
run rm -rf /site
docker cp "$STAGE" "$CONTAINER":/site >/dev/null
run sh -c 'ipfs add -r --cid-version=1 --progress=false /site' 2>&1 | sed -E 's/\r.*$//' > "$EV/06-ipfs-add-site.txt"
SITE_CID=$(run ipfs add -rQ --cid-version=1 /site | tr -d '\r')

echo "[7/12] fetch site via local gateway"
{
  curl -sS -o /tmp/site-local.html -w "HTTP %{http_code}  bytes=%{size_download}\n" \
       "http://127.0.0.1:8080/ipfs/$SITE_CID/index.html"
  head -c 200 /tmp/site-local.html
  echo
} > "$EV/07-ipfs-gateway-site.txt"

echo "[8/12] CID determinism"
{
  echo "# Same bytes -> same CID, different bytes -> different CID."
  echo
  echo "\$ echo 'same content' | ipfs add -Q --cid-version=1 --only-hash"
  echo "same content" | docker exec -i "$CONTAINER" ipfs add -Q --cid-version=1 --only-hash
  echo
  echo "\$ echo 'same content' | ipfs add -Q --cid-version=1 --only-hash   # again"
  echo "same content" | docker exec -i "$CONTAINER" ipfs add -Q --cid-version=1 --only-hash
  echo
  echo "\$ echo 'same contentx' | ipfs add -Q --cid-version=1 --only-hash"
  echo "same contentx" | docker exec -i "$CONTAINER" ipfs add -Q --cid-version=1 --only-hash
} > "$EV/08-cid-deterministic.txt"

echo "[9/12] mutability demo"
STAGE2=/tmp/lab18-site-v2
rm -rf "$STAGE2" && mkdir -p "$STAGE2"
sed 's/IPFS via 4EVERLAND/IPFS via 4EVERLAND (rev-2)/' "$SITE_HTML" > "$STAGE2/index.html"
run rm -rf /site-v2
docker cp "$STAGE2" "$CONTAINER":/site-v2 >/dev/null
{
  echo "# Task 5 -- Mutability via new CID"
  echo
  echo "## SHA-256"
  echo "v1: $(shasum -a 256 "$SITE_HTML" | awk '{print $1}')  index.html"
  echo "v2: $(shasum -a 256 "$STAGE2/index.html" | awk '{print $1}')  index.html (rev-2)"
  echo
  echo "## ipfs add -rQ --cid-version=1"
  echo "v1 dir CID: $(run ipfs add -rQ --cid-version=1 --only-hash /site   | tr -d '\r')"
  echo "v2 dir CID: $(run ipfs add -rQ --cid-version=1 --only-hash /site-v2 | tr -d '\r')"
  echo
  echo "# Same path, changed content => new directory CID."
  echo "# IPNS (or 4EVERLAND DNS) gives a stable pointer over these immutable snapshots."
} > "$EV/09-cid-mutability-v2.txt"

echo "[10/12] repo + bandwidth + peer stats"
{
  echo "\$ ipfs repo stat --human"
  run ipfs repo stat --human
  echo
  echo "\$ ipfs stats bw"
  run ipfs stats bw
  echo
  echo "\$ ipfs swarm peers | wc -l"
  run sh -c 'ipfs swarm peers | wc -l'
  echo
  echo "\$ ipfs dag stat $SITE_CID"
  run ipfs dag stat "$SITE_CID" 2>&1 | head -20
} > "$EV/10-ipfs-stats.txt"

echo "[11/12] public gateway reachability (best-effort)"
{
  echo "# The local node is NAT-isolated, so public gateways may not resolve"
  echo "# unpinned-elsewhere CIDs. This motivates Task 4 (4EVERLAND Bucket pinning)."
  echo
  for url in \
      "https://ipfs.io/ipfs/$HELLO_CID" \
      "https://dweb.link/ipfs/$HELLO_CID" \
      "https://ipfs.4everland.link/ipfs/$HELLO_CID" ; do
    echo "\$ curl --max-time 15 -sS -o /dev/null -w '%{http_code}  %{time_total}s  %{url}\n' $url"
    curl --max-time 15 -sS -o /dev/null -w '%{http_code}  %{time_total}s  %{url}\n' "$url" \
      || echo "timeout/fail  $url"
  done
} > "$EV/11-public-gateway-check.txt"

echo "[12/12] WebUI + RPC API reachability"
{
  echo "\$ curl -sI http://127.0.0.1:5001/webui"
  curl -sI http://127.0.0.1:5001/webui | head -10
  echo
  echo "\$ curl -sS -X POST http://127.0.0.1:5001/api/v0/version"
  curl -sS -X POST http://127.0.0.1:5001/api/v0/version
  echo
} > "$EV/12-webui-reachable.txt"

echo
echo "Done. Evidence refreshed in: $EV"
echo "hello.txt CID: $HELLO_CID"
echo "site dir CID: $SITE_CID"

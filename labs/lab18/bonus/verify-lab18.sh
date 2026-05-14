#!/usr/bin/env bash
set -uo pipefail

CID="${1:-}"

if [[ -z "$CID" ]]; then
  echo "Usage: $0 <cid>"
  exit 1
fi

gateways=(
  "http://localhost:8080/ipfs/${CID}/"
  "https://ipfs.4everland.link/ipfs/${CID}/"
  "https://ipfs.io/ipfs/${CID}/"
  "https://dweb.link/ipfs/${CID}/"
)

for url in "${gateways[@]}"; do
  printf '%-60s ' "$url"
  if output="$(curl -sSL --http1.1 --max-time 20 -o /dev/null -w 'HTTP %{http_code}' "$url" 2>&1)"; then
    printf '%s\n' "$output"
  else
    printf 'ERROR: %s\n' "$(tr '\n' ' ' <<<"$output" | sed 's/[[:space:]]\\+/ /g')"
  fi
done

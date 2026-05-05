#!/usr/bin/env bash
set -euo pipefail

# Run from repository root.
mkdir -p labs/lab18/evidence

APP_DIR="labs/lab18/app_python"
EVIDENCE_DIR="labs/lab18/evidence"

cd "$APP_DIR"

# Nix application build evidence.
nix-build > "../../lab18/evidence/01-nix-build-output.txt"
readlink result > "../../lab18/evidence/02-store-path-first.txt"
nix-hash --type sha256 result > "../../lab18/evidence/03-nix-output-hash-first.txt"

rm result
nix-build > "../../lab18/evidence/04-nix-rebuild-output.txt"
readlink result > "../../lab18/evidence/05-store-path-second.txt"
nix-hash --type sha256 result > "../../lab18/evidence/06-nix-output-hash-second.txt"

# Nix Docker image hash evidence.
nix-build docker.nix > "../../lab18/evidence/07-nix-docker-build-output.txt"
shasum -a 256 result > "../../lab18/evidence/08-nix-docker-hash-first.txt"
rm result
nix-build docker.nix > "../../lab18/evidence/09-nix-docker-rebuild-output.txt"
shasum -a 256 result > "../../lab18/evidence/10-nix-docker-hash-second.txt"

cd ../../..

# Traditional Docker evidence from the copied Lab 2 Dockerfile.
docker build -t lab2-app:v1 "$APP_DIR" > "$EVIDENCE_DIR/11-docker-build-v1.txt"
docker inspect lab2-app:v1 | grep Created > "$EVIDENCE_DIR/12-docker-created-v1.txt"
sleep 5
docker build -t lab2-app:v2 "$APP_DIR" > "$EVIDENCE_DIR/13-docker-build-v2.txt"
docker inspect lab2-app:v2 | grep Created > "$EVIDENCE_DIR/14-docker-created-v2.txt"
docker save lab2-app:v1 | shasum -a 256 > "$EVIDENCE_DIR/15-docker-save-hash-v1.txt"
docker save lab2-app:v2 | shasum -a 256 > "$EVIDENCE_DIR/16-docker-save-hash-v2.txt"
docker images | grep -E "lab2-app|devops-info-service-nix" > "$EVIDENCE_DIR/17-docker-images.txt" || true
docker history lab2-app:v1 > "$EVIDENCE_DIR/18-docker-history-lab2.txt"

echo "Evidence collected in $EVIDENCE_DIR"

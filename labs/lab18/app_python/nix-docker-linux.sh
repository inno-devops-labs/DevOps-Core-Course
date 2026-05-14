#!/usr/bin/env bash
# Build the Lab 18 dockerTools tarball when native `nix build .#docker` fails on macOS
# (fakeroot / dyld `_fstat$INODE64` in dockerTools). Uses Nix inside a Linux container.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker: command not found. Install Docker Desktop / Colima first." >&2
  exit 1
fi

echo "Repo: $REPO_ROOT"
echo "Building docker output in Linux (nixos/nix)..."

# Use a path: flake so Nix does not need `git` for git+file evaluation (avoids nix shell + # quoting issues).
docker run --rm -i \
  -v "$REPO_ROOT:/repo" \
  -w /repo/labs/lab18/app_python \
  nixos/nix:latest \
  bash -euxo pipefail -s <<'REMOTE'
export NIX_CONFIG="extra-experimental-features = nix-command flakes"
nix --version
# Absolute path + fragment; # is safe inside "..." for bash.
here="/repo/labs/lab18/app_python"
sys=$(nix eval --impure --raw --expr builtins.currentSystem)
nix build --print-build-logs --accept-flake-config \
  "path:${here}#packages.${sys}.docker"
# Copy tarball onto the bind mount: `result` points at /nix/store/... inside the
# container; that path usually does not exist on the macOS host, so `docker load < result` breaks.
out="$(readlink -f result)"
install -m644 "$out" "/repo/labs/lab18/app_python/devops-info-service-nix.tar.gz"
REMOTE

echo "Done."
echo "  Symlink (may be broken on macOS host): $SCRIPT_DIR/result"
echo "  Host tarball for docker load:          $SCRIPT_DIR/devops-info-service-nix.tar.gz"
ls -la "$SCRIPT_DIR/result" "$SCRIPT_DIR/devops-info-service-nix.tar.gz" 2>/dev/null || true

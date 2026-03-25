#!/usr/bin/env bash
# Build and push Lab 2 image for linux/amd64 and linux/arm64 (Docker Hub) — Option A for Lab 9.
# Run: docker login first
# Env: DOCKER_IMAGE (default mclavrushka/devops-info-service), DOCKER_TAG (latest)
set -euo pipefail

IMAGE="${DOCKER_IMAGE:-mclavrushka/devops-info-service}"
TAG="${DOCKER_TAG:-latest}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Image: ${IMAGE}:${TAG}"
echo "Context: ${ROOT}"
echo "Requires: docker login to Docker Hub"
echo ""

BUILDER="${BUILDX_BUILDER:-multiarch-lab}"

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER" --driver docker-container --bootstrap
fi
docker buildx use "$BUILDER"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${IMAGE}:${TAG}" \
  -f "${ROOT}/Dockerfile" \
  "${ROOT}" \
  --push

echo ""
echo "Done. Verify: docker pull ${IMAGE}:${TAG}"
echo "Kubernetes: kubectl apply -k k8s/"

#!/bin/sh
# Optional Raspberry Pi path (docs/PI_DEPLOYMENT.md): build linux/arm64 and push to the laptop registry over the LAN.
set -eu
IP=${1:?laptop LAN IP}; TAG=${2:-v1-arm64}
docker buildx create --use --name logibridge-builder 2>/dev/null || docker buildx use logibridge-builder
docker buildx build --platform linux/arm64 -f inference/Dockerfile -t "$IP:5000/logibridge:$TAG" --push .

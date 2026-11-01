#!/bin/sh
# Optional, before Ansible run 1: push the image, then remove the container and LOCAL tag so task 5
# visibly pulls. Alert state (/var/lib/logibridge) is NOT deleted.
set -eu
IMG=${1:?image tag}
docker push "$IMG"
docker rm -f logibridge 2>/dev/null || true
docker image rm "$IMG"
echo "Local tag removed; image kept in the registry; alert state kept."

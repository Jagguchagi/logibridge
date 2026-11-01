#!/bin/sh
# One-shot lab setup (Linux/WSL): venv + deps + broker/registry + train/benchmark.
# Usage: LAPTOP_TDP_W=15 sh setup_lab.sh
set -eu
cd "$(dirname "$0")"
: "${LAPTOP_TDP_W:=15}"
export LAPTOP_TDP_W

PY=$(command -v python3.11 || command -v python3)
"$PY" -c 'import sys; assert sys.version_info[:2] <= (3, 11), "Need Python 3.9-3.11 for tensorflow 2.15"'
[ -d .venv ] || "$PY" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

docker compose up -d
python -m scripts.preflight || echo "Preflight reported issues - read the lines above."

sh scripts/build_all.sh
docker build -f inference/Dockerfile -t localhost:5000/logibridge:v1 .
echo "Done. Next: RUNBOOK sections 1b (drift), 2 (OTA), then scripts.run_ansible_twice."

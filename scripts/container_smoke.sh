#!/bin/sh
# Hard gate: every model must load INSIDE the container (TF 2.15 converter vs tflite-runtime 2.14).
# Usage: sh scripts/container_smoke.sh localhost:5000/logibridge:v1
set -eu
IMG=${1:?image tag}
mkdir -p evidence
docker run --rm -v "$PWD/training/models:/models:ro" "$IMG" python -c '
import hashlib
from pathlib import Path
import numpy as np
from inference.runtime import Model
from data_pipeline.preprocessing import validate_pipeline_contract
paths = [Path("/app/model.tflite")] + sorted(Path("/models").glob("*.tflite"))
assert len(paths) >= 4, "expected the baked model plus M1, M2, M3"
for p in paths:
    validate_pipeline_contract(p, "/app/training_stats.npy")
    out = Model(p).predict(np.zeros(6)); assert out.shape == (3,) and np.isfinite(out).all()
    print("PASS", p, "sha256=" + hashlib.sha256(p.read_bytes()).hexdigest(), out.round(3))
' > evidence/container_smoke.txt 2>&1 || { cat evidence/container_smoke.txt; echo "FAIL: reconvert with tensorflow==2.14.* and disclose"; exit 1; }
cat evidence/container_smoke.txt

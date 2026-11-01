"""F3: choose the deployment model from CURRENT measured results.
Gates: accuracy > 88% and Critical recall > 95%; then smallest file, then lowest p95.
Refuses stale results (model, dataset or stats hash changed since benchmarking)."""
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

from optimisation.benchmark import FILES
from data_pipeline.preprocessing import pipeline_sha256, validate_pipeline_contract


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def choose(rows):
    if len(rows) != 3 or {r['variant'] for r in rows} != set(FILES):
        raise ValueError('need exactly one row each for M1, M2, M3')
    ok = []
    for r in rows:
        acc, rec, size = (float(r[k]) for k in ('accuracy_pct', 'critical_recall_pct', 'size_KB'))
        if not all(math.isfinite(v) for v in (acc, rec, size)) or not (0 <= acc <= 100 and 0 <= rec <= 100 and size > 0):
            raise ValueError(f"invalid metrics for {r['variant']}")
        latency = float(r['p95_ms'])
        if not math.isfinite(latency) or latency <= 0:
            raise ValueError('p95 latency must be finite and positive')
        if acc > 88 and rec > 95:
            ok.append(r)
    return min(ok, key=lambda r: (float(r['size_KB']), float(r['p95_ms']))) if ok else None


def main():
    rows = list(csv.DictReader(open('optimisation/results/benchmark_results.csv')))
    meta = json.loads(Path('optimisation/results/benchmark_metadata.json').read_text())
    if meta.get('pipeline_sha256') != pipeline_sha256():
        raise SystemExit('preprocessing changed: rebuild models and benchmark')
    if meta['dataset_sha256'] != sha256('training/data/dataset.npz') or meta['stats_sha256'] != sha256('data_pipeline/training_stats.npy'):
        raise SystemExit('dataset/stats changed since benchmarking: rerun the benchmark')
    for r in rows:
        validate_pipeline_contract(Path('training/models') / FILES[r['variant']])
        if r['model_sha256'] != sha256(Path('training/models') / FILES[r['variant']]):
            raise SystemExit(f"{r['variant']} changed since benchmarking: rerun the benchmark")
    best = choose(rows)
    if best is None:
        raise SystemExit('no variant passes accuracy > 88% and Critical recall > 95%: do not deploy')
    shutil.copyfile(Path('training/models') / FILES[best['variant']], 'inference/model.tflite')
    shutil.copyfile(str(Path('training/models') / FILES[best['variant']]) + '.pipeline.json', 'inference/model.tflite.pipeline.json')
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/model_selection.json').write_text(json.dumps(best, indent=2))
    print(f"selected {best['variant']} -> inference/model.tflite. NEXT: python -m monitoring.drift_monitor --reference")


if __name__ == '__main__':
    main()

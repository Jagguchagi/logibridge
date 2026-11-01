"""F2: five metrics for M1/M2/M3 (10 warm-up + 200 timed runs), plus Critical recall and the C2
3-sigma shifted-stats experiment. Energy = TDP x CPU% x latency (estimate, not a power meter).
Writes benchmark_results.csv, benchmark_metadata.json and an annotated pareto_chart.png."""
import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import psutil
from sklearn.metrics import accuracy_score, recall_score

from data_pipeline.preprocessing import normalize, pipeline_sha256, validate_pipeline_contract
from inference.runtime import Model

FILES = {'M1': 'M1_fp32.tflite', 'M2': 'M2_int8.tflite', 'M3': 'M3_pruned_int8.tflite'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pareto(rows):
    """True for rows not dominated on (lower mean latency, higher accuracy)."""
    return [not any(o['mean_ms'] <= r['mean_ms'] and o['accuracy_pct'] >= r['accuracy_pct'] and
                    (o['mean_ms'] < r['mean_ms'] or o['accuracy_pct'] > r['accuracy_pct']) for o in rows)
            for r in rows]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tdp-w', type=float, required=True, help='documented TDP of your laptop CPU')
    a = p.parse_args()
    if not np.isfinite(a.tdp_w) or a.tdp_w <= 0:
        raise SystemExit('give a positive, documented TDP')
    d = np.load('training/data/dataset.npz')
    s = np.load('data_pipeline/training_stats.npy')
    raw, y = d['X'][d['val']], d['y'][d['val']]
    X, Xs = normalize(raw, s), normalize(raw, np.stack([s[0] + 3 * s[1], s[1]]))
    rows = []
    for name, file in FILES.items():
        path = Path('training/models') / file
        validate_pipeline_contract(path)
        m = Model(path)
        for i in range(10):
            m.predict(X[i % len(X)])
        psutil.cpu_percent(None)
        times = []
        for i in range(200):
            t0 = time.perf_counter()
            m.predict(X[i % len(X)])
            times.append((time.perf_counter() - t0) * 1000)
        cpu = psutil.cpu_percent(None)
        pred = [int(m.predict(x).argmax()) for x in X]
        shifted = [int(m.predict(x).argmax()) for x in Xs]
        rows.append({'variant': name, 'mean_ms': float(np.mean(times)), 'p95_ms': float(np.percentile(times, 95)),
                     'size_KB': path.stat().st_size / 1000, 'accuracy_pct': 100 * accuracy_score(y, pred),
                     'energy_estimate_mJ': a.tdp_w * cpu / 100 * float(np.mean(times)),
                     'critical_recall_pct': 100 * recall_score(y, pred, labels=[2], average=None, zero_division=0)[0],
                     'shifted_stats_accuracy_pct': 100 * accuracy_score(y, shifted),
                     'cpu_pct': cpu, 'model_sha256': sha256(path)})
    out = Path('optimisation/results')
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'benchmark_results.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)
    (out / 'benchmark_metadata.json').write_text(json.dumps({
        'pipeline_sha256': pipeline_sha256(), 'platform': platform.platform(), 'warmups': 10, 'runs': 200, 'tdp_w': a.tdp_w,
        'dataset_sha256': sha256('training/data/dataset.npz'), 'stats_sha256': sha256('data_pipeline/training_stats.npy'),
        'energy': 'TDP x system CPU fraction x mean latency: an estimate, not a measurement'}, indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    front = pareto(rows)
    fig, ax = plt.subplots(figsize=(6, 4))
    for r, on in zip(rows, front):
        ax.scatter(r['mean_ms'], r['accuracy_pct'], marker='o' if on else 'x', s=70)
        ax.annotate(f"{r['variant']} ({r['size_KB']:.1f} KB){' - Pareto' if on else ' - dominated'}",
                    (r['mean_ms'], r['accuracy_pct']), textcoords='offset points', xytext=(6, 4))
    pts = sorted((r['mean_ms'], r['accuracy_pct']) for r, on in zip(rows, front) if on)
    ax.plot(*zip(*pts), linestyle='--')
    ax.axhline(88, color='grey', linewidth=0.8)
    ax.set_xlabel('Mean inference latency (ms)')
    ax.set_ylabel('Validation accuracy (%)')
    ax.set_title('LogiEdge latency vs accuracy (measured)')
    fig.tight_layout()
    fig.savefig(out / 'pareto_chart.png', dpi=150)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()

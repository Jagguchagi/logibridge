"""D1 dataset, generated in-process from the same simulator code that publishes to MQTT.

Durations from the brief: none 20 min (Normal), temp_drift 15 min (Warning), combined 15 min
(Critical). Frozen normalisation stats come from a separate 10-minute clean session (C2).
Split: chronological 80/20 per class. Four overlapping windows are purged at each boundary,
because a window covers 30 s plus up to 8 s of causal filter history (four 10 s steps).
"""
import json
from pathlib import Path

import numpy as np

from data_pipeline.preprocessing import Pipeline
from data_pipeline.simulator import samples

CLASSES = [('none', 1200), ('temp_drift', 900), ('combined', 900)]
PURGE = 4


def windows(mode, seconds, seed):
    p, out = Pipeline(), []
    for stream, msg in samples(mode, seconds, seed):
        out.extend(x for _, x in p.push(stream, msg))
    return np.asarray(out, dtype=np.float32)


def main():
    Path('training/data').mkdir(parents=True, exist_ok=True)
    clean = windows('none', 600, 101)
    np.save('data_pipeline/training_stats.npy',
            np.stack([clean.mean(0), np.maximum(clean.std(0), 1e-6)]).astype(np.float32))
    xs = [windows(m, s, 200 + i) for i, (m, s) in enumerate(CLASSES)]
    train, val, off = [], [], 0
    for x in xs:
        cut = int(0.8 * len(x))
        train += range(off, off + cut - PURGE)
        val += range(off + cut, off + len(x))
        off += len(x)
    X = np.concatenate(xs)
    y = np.concatenate([np.full(len(x), c) for c, x in enumerate(xs)])
    if len(train) < 200:
        raise SystemExit('fewer than 200 training windows: PTQ calibration would be impossible')
    np.savez('training/data/dataset.npz', X=X, y=y, train=np.array(train), val=np.array(val))
    np.save('training/data/reference_clean.npy', windows('none', 3100, 999)[:300])
    summary = {'synthetic': True, 'windows_per_class': [len(x) for x in xs], 'train': len(train),
               'validation': len(val), 'purged_per_class': PURGE,
               'label_note': 'Brief mode labels kept. temp_drift exceeds +3 C after ~38 s, so its later '
                             'windows are physically Critical; the runtime safety rule handles that separately.'}
    Path('training/data/dataset_summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

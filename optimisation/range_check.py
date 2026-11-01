"""Diagnostics: train vs validation feature ranges, INT8 input clipping per variant, disagreement
with M1, and predictions on an unseen vibration-only run (reported separately, not as accuracy)."""
import json
from pathlib import Path

import numpy as np

from data_pipeline.preprocessing import FEATURES, normalize, validate_pipeline_contract, pipeline_sha256
from inference.runtime import Model
from optimisation.benchmark import FILES
from training.generate_dataset import windows


def main():
    d = np.load('training/data/dataset.npz')
    s = np.load('data_pipeline/training_stats.npy')
    tr, va = d['X'][d['train']], d['X'][d['val']]
    out = {'pipeline_sha256': pipeline_sha256(), 'features': FEATURES, 'train_min': tr.min(0).tolist(), 'train_max': tr.max(0).tolist(),
           'val_min': va.min(0).tolist(), 'val_max': va.max(0).tolist(), 'variants': {}}
    X, unseen = normalize(va, s), normalize(windows('vibration', 900, 888), s)
    base = None
    for name, file in FILES.items():
        validate_pipeline_contract(Path('training/models') / file)
        m = Model(Path('training/models') / file)
        pred, clip = [], []
        for x in X:
            pred.append(int(m.predict(x).argmax()))
            clip.append(m.last_clipped.copy())
        pred = np.array(pred)
        base = pred if base is None else base
        up = [int(m.predict(x).argmax()) for x in unseen]
        out['variants'][name] = {'clipped_windows': int(np.any(clip, axis=1).sum()),
                                 'clipped_per_feature': np.sum(clip, axis=0).tolist(),
                                 'disagreements_with_M1': int((pred != base).sum()),
                                 'vibration_only_prediction_counts': np.bincount(up, minlength=3).tolist()}
    Path('optimisation/results').mkdir(parents=True, exist_ok=True)
    Path('optimisation/results/range_check.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()

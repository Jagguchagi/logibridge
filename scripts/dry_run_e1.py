"""Offline feasibility dry run (NO TensorFlow, NO MQTT, NOT assignment evidence).

Trains a scikit-learn MLP with the same 6-32-16-3 ReLU shape as a stand-in for M1, then replays a
simulated timeline (clean -> combined -> clean) through the real Pipeline, Window and analyse_psi
code with simulated time (every 60 s check on the last 100 inferences). It answers two planning
questions before you spend time on the live run:
  1. Is >88% validation accuracy plausible with these features?
  2. How long do the PSI crossing and recovery take, and does that fit a 15-20 minute video?
Output: evidence/dry_run_e1.json, clearly marked as a stand-in. Do NOT report these as results.
Usage: python -m scripts.dry_run_e1 [--inject-s 300]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, recall_score
from sklearn.neural_network import MLPClassifier

from data_pipeline.preprocessing import Pipeline, normalize
from data_pipeline.simulator import schedule_samples
from monitoring.drift_monitor import Window, build_reference
from scripts.analyse_run import analyse_psi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inject-s', type=int, default=300, help='seconds of combined anomaly')
    a = ap.parse_args()
    if a.inject_s <= 0:
        raise ValueError('inject-s must be positive')
    d = np.load('training/data/dataset.npz')
    s = np.load('data_pipeline/training_stats.npy')
    X, y = normalize(d['X'], s), d['y']
    clf = MLPClassifier((32, 16), max_iter=2000, random_state=42).fit(X[d['train']], y[d['train']])
    pred = clf.predict(X[d['val']])
    acc = float(accuracy_score(y[d['val']], pred))
    rec = float(recall_score(y[d['val']], pred, labels=[2], average=None, zero_division=0)[0])

    ref = build_reference(clf.predict_proba(normalize(np.load('training/data/reference_clean.npy'), s)), 'm', 's')
    clean, restore_after = 1800, 1800
    segments = [('none', clean), ('combined', a.inject_s), ('none', restore_after)]
    clock = {'t': 0.0}
    win = Window(ref, 'dry', 'T001', clock=lambda: clock['t'])
    win.last_arrival = None
    pipe, rows, t_now = Pipeline(), [], 0.0
    next_check = 60.0
    for stream, msg in schedule_samples(segments, seed=7):
        clock['t'] = msg['timestamp']
        for end, x in pipe.push(stream, msg):
            p = clf.predict_proba(normalize(x, s).reshape(1, 6))[0]
            win.add({'probabilities': p.tolist(), 'timestamp': end, 'model_sha256': 'm', 'stats_sha256': 's',
                     'run_id': 'dry', 'truck_id': 'T001'})
        while clock['t'] >= next_check:
            values, n, _ = win.check()
            if values:
                rows.append({'epoch': next_check, 'run_id': 'dry', 'truck_id': 'T001', 'model_sha256': 'm',
                             'stats_sha256': 's', 'score': 'normal_probability', 'interval_s': 60,
                             'psi': values['normal_probability'], 'all_scores': values})
            next_check += 60
    events = [{'event': 'mode_change', 'mode': m, 'epoch': float(e), 'run_id': 'dry', 'truck_id': 'T001'}
              for m, e in [('none', 0), ('combined', clean), ('none', clean + a.inject_s)]]
    r = analyse_psi(events, rows)
    out = {'WARNING': 'scikit-learn stand-in with simulated time; NOT TFLite, NOT live MQTT, NOT assignment evidence',
           'standin_val_accuracy': round(acc, 4), 'standin_critical_recall': round(rec, 4),
           'inject_s': a.inject_s, 'e1_pass_in_dry_run': r['e1_pass'],
           'scores': {k: {kk: v[kk] for kk in ('baseline_psi', 'crossing_delay_s', 'peak_psi', 'recovery_delay_s')}
                      for k, v in r['scores'].items()}}
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/dry_run_e1.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()

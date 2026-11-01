"""E1 PSI drift monitor.

Reference: 300 clean Normal windows, bins [0,.25) [.25,.5) [.5,.75) [.75,1], 0.5 pseudo-count per bin.
Monitor: last 100 inferences, PSI every 60 s, prints [LOGIBRIDGE DRIFT ALERT] PSI={v:.3f} when > 0.25.

Confidence score: both are computed and logged every check.
  normal_probability (DEFAULT) = P(Normal)
  max_probability              = top-class probability
The top-class probability does not change when predictions move from confident Normal to confident
Critical (see tests), so the E1 crossing can be missed. Using P(Normal) is a disclosed
interpretation: confirm with the instructor; --score max_probability switches back.
Only inferences from the same model, stats, run and truck as the reference/run are accepted.
"""
import argparse
import hashlib
import json
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from data_pipeline.preprocessing import pipeline_sha256

BINS = [0.0, 0.25, 0.50, 0.75, 1.000001]
SCORES = {'normal_probability': lambda p: float(p[0]), 'max_probability': lambda p: float(np.max(p))}
DEFAULT_SCORE = 'normal_probability'
STALE_S = 120


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distribution(values):
    a = np.asarray(values, dtype=float)
    if a.size == 0 or not np.isfinite(a).all() or (a < -1e-6).any() or (a > 1 + 1e-6).any():
        raise ValueError('scores must be a non-empty set of finite values in [0, 1]')
    n = np.histogram(np.clip(a, 0, 1), BINS)[0].astype(float)
    return (n + 0.5) / (n.sum() + 2.0)


def psi(reference, current):
    r, c = np.asarray(reference, dtype=float), np.asarray(current, dtype=float)
    if r.shape != (4,) or c.shape != (4,) or (r <= 0).any() or (c <= 0).any() \
            or not (np.isclose(r.sum(), 1) and np.isclose(c.sum(), 1)):
        raise ValueError('PSI needs two positive 4-bin distributions summing to 1')
    return float(np.sum((c - r) * np.log(c / r)))


def build_reference(prob_rows, model_sha, stats_sha):
    p = np.asarray(prob_rows, dtype=float)
    if p.shape != (300, 3) or not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(1), 1, atol=.03):
        raise ValueError('E1 requires exactly 300 clean Normal windows of 3 class probabilities')
    return {'count': 300, 'bins': BINS[:-1] + [1.0], 'model_sha256': model_sha, 'model_version': model_sha[:12],
            'stats_sha256': stats_sha, 'default_score': DEFAULT_SCORE,
            'pipeline_sha256': pipeline_sha256(),
            'distributions': {n: distribution([f(r) for r in p]).tolist() for n, f in SCORES.items()}}


class Window:
    """Rolling buffers; rejects other models/stats/runs/trucks, malformed rows and QoS-1 duplicates."""

    def __init__(self, ref, run_id, truck_id='T001', size=100, clock=None, require_pipeline=False):
        self.ref, self.run_id, self.truck_id, self.size = ref, run_id, truck_id, size
        self.require_pipeline = require_pipeline
        self.clock = clock or (lambda: time.monotonic())
        self.last_timestamp = float("-inf")
        self.last_arrival = None
        self.buf = {n: deque(maxlen=size) for n in SCORES}
        self.seen, self.lock, self.rejected = deque(maxlen=500), threading.Lock(), 0

    def add(self, d):
        if not isinstance(d, dict):
            return False
        try:
            p = np.asarray(d['probabilities'], dtype=float)
            t = float(d['timestamp'])
        except (KeyError, TypeError, ValueError):
            return False
        expected = {'model_sha256': self.ref['model_sha256'], 'stats_sha256': self.ref['stats_sha256'],
                    'run_id': self.run_id, 'truck_id': self.truck_id}
        if self.require_pipeline:
            expected['pipeline_sha256'] = self.ref['pipeline_sha256']
        if any(d.get(k) != v for k, v in expected.items()):
            with self.lock:
                self.rejected += 1
            return False
        if p.shape != (3,) or not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() \
                or not np.isclose(p.sum(), 1, atol=0.03) or not np.isfinite(t):
            return False
        with self.lock:
            if t <= self.last_timestamp or t in self.seen:
                return False
            now = self.clock()
            if self.last_arrival is not None and now - self.last_arrival > STALE_S:
                for q in self.buf.values():   # gap: never mix pre-gap and post-gap scores
                    q.clear()
            self.last_timestamp = t
            self.last_arrival = now
            self.seen.append(t)
            for n, f in SCORES.items():
                self.buf[n].append(f(p))
        return True

    def check(self):
        with self.lock:
            snap, bad = {k: list(v) for k, v in self.buf.items()}, self.rejected
        n = len(snap[DEFAULT_SCORE])
        if self.last_arrival is None or self.clock() - self.last_arrival > STALE_S:
            return None, n, bad
        if n < self.size:
            return None, n, bad
        return {k: psi(self.ref['distributions'][k], distribution(v)) for k, v in snap.items()}, n, bad


def write_reference(model_path, stats_path, out):
    from data_pipeline.preprocessing import normalize, validate_pipeline_contract
    from inference.runtime import Model
    validate_pipeline_contract(model_path, stats_path)
    m, s = Model(model_path), np.load(stats_path)
    rows = [m.predict(normalize(w, s)) for w in np.load('training/data/reference_clean.npy')]
    ref = build_reference(rows, sha256(model_path), sha256(stats_path))
    Path(out).write_text(json.dumps(ref, indent=2))
    print(f"wrote {out} for model_version {ref['model_version']}")


def monitor(a):
    import paho.mqtt.client as mqtt
    from data_pipeline.simulator import safe_run_id
    safe_run_id(a.run_id)
    if a.interval != 60:
        print(f'WARNING: interval {a.interval}s is for rehearsal only; the brief requires 60 s and '
              'scripts.analyse_run will not count this run as E1 evidence.', flush=True)
    ref = json.loads(Path(a.reference_path).read_text())
    from data_pipeline.preprocessing import pipeline_sha256
    if ref.get('pipeline_sha256') != pipeline_sha256():
        raise ValueError('Stale preprocessing reference: regenerate reference with rebuilt model')
    win = Window(ref, a.run_id, a.truck_id, require_pipeline=True)
    log = Path('evidence') / a.run_id / 'psi_live.jsonl'
    if log.exists():
        raise SystemExit(f'{log} exists: use a new run id')
    log.parent.mkdir(parents=True, exist_ok=True)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = lambda c, u, f, rc, pr=None: c.subscribe(f'logibridge/trucks/{a.truck_id}/inference', qos=1)

    def on_message(c, u, msg):
        try:
            win.add(json.loads(msg.payload))
        except ValueError:
            pass
    client.on_message = on_message
    client.connect(a.host, 1883)
    client.loop_start()
    print(f"monitoring run {a.run_id}, model {ref['model_version']}, score={a.score}", flush=True)
    try:
        while True:
            time.sleep(a.interval)
            values, n, bad = win.check()
            now = datetime.now(timezone.utc)
            if values is None:
                extra = f' ({bad} rejected: other model/stats/run - check RUN_ID and reference)' if bad else ''
                print(f'{now:%H:%M:%S} PSI warming up {n}/100{extra}', flush=True)
                continue
            sel = values[a.score]
            print(f"{now:%H:%M:%S} PSI={sel:.3f} [{a.score}; normal_probability={values['normal_probability']:.3f}; "
                  f"max_probability={values['max_probability']:.3f}]", flush=True)
            with log.open('a') as f:
                f.write(json.dumps({'epoch': now.timestamp(), 'run_id': a.run_id, 'truck_id': a.truck_id,
                                    'model_sha256': ref['model_sha256'], 'stats_sha256': ref['stats_sha256'],
                                    'pipeline_sha256': ref['pipeline_sha256'], 'score': a.score, 'interval_s': a.interval, 'psi': sel, 'all_scores': values}) + '\n')
            if sel > 0.25:
                print(f'[LOGIBRIDGE DRIFT ALERT] PSI={sel:.3f}', flush=True)
    finally:
        client.loop_stop()
        client.disconnect()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--reference', action='store_true', help='build reference_dist.json and exit')
    p.add_argument('--model', default='inference/model.tflite', help='must be the DEPLOYED model')
    p.add_argument('--stats', default='data_pipeline/training_stats.npy')
    p.add_argument('--reference-path', default='monitoring/reference_dist.json')
    p.add_argument('--run-id', help='same run id as the simulator (printed as RUN_ID=...)')
    p.add_argument('--truck-id', default='T001')
    p.add_argument('--host', default='localhost')
    p.add_argument('--score', choices=sorted(SCORES), default=DEFAULT_SCORE)
    p.add_argument('--interval', type=int, default=60)
    a = p.parse_args()
    if a.reference:
        write_reference(a.model, a.stats, a.reference_path)
    elif not a.run_id:
        raise SystemExit('--run-id is required (copy it from the simulator output)')
    else:
        monitor(a)


if __name__ == '__main__':
    main()

"""Fast rehearsal of the drift monitor and the analyser: about 30 seconds instead of ~35 minutes.
THIS IS NOT EVIDENCE. It publishes synthetic inference messages (built from the identities in
monitoring/reference_dist.json) to the same broker the real monitor listens on, and writes a
simulator-style event log. Because the monitor runs at --interval 1 here, scripts.analyse_run
reports e1_pass = false on purpose; every other field should be true.

Three terminals (broker already running):
    python -m monitoring.drift_monitor --run-id rehearse01 --interval 1
    python -m scripts.rehearse_monitor --run-id rehearse01
    python -m scripts.analyse_run --run-id rehearse01

What to look for: PSI < 0.10 at first, `[LOGIBRIDGE DRIFT ALERT]` after the fault phase, then PSI
back below 0.10. Use a NEW run id for each rehearsal and a different one for the real run.
"""
import argparse
import json
import time
from pathlib import Path

from data_pipeline.simulator import safe_run_id

CLEAN = [1.0, 0.0, 0.0]
CRITICAL = [0.0, 0.0, 1.0]


def inference_payload(ref, run_id, truck_id, timestamp, critical):
    """One inference message with the same fields the real service publishes (those the monitor reads)."""
    probs = CRITICAL if critical else CLEAN
    cls = 2 if critical else 0
    return {'timestamp': timestamp, 'run_id': run_id, 'truck_id': truck_id,
            'model_sha256': ref['model_sha256'], 'stats_sha256': ref['stats_sha256'],
            'pipeline_sha256': ref['pipeline_sha256'], 'probabilities': probs, 'confidence': 1.0,
            'model_class': cls, 'safety_class': 0, 'effective_class': cls, 'rehearsal': True}


def plan(n_clean=110, n_fault=20, n_after=115):
    """(mode, count) phases; 100 clean messages fill the monitor window, the rest drive the fault and recovery."""
    return [('none', n_clean), ('combined', n_fault), ('none', n_after)]


def main():
    import paho.mqtt.client as mqtt
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--truck-id', default='T001')
    p.add_argument('--host', default='localhost')
    p.add_argument('--reference-path', default='monitoring/reference_dist.json')
    p.add_argument('--pause', type=float, default=3.5, help='seconds between phases so the monitor ticks')
    a = p.parse_args()
    run_id = safe_run_id(a.run_id)
    ref = json.loads(Path(a.reference_path).read_text())
    log = Path('evidence') / run_id / 'simulator_events.jsonl'
    if log.exists():
        raise SystemExit(f'{log} exists: use a new --run-id')
    log.parent.mkdir(parents=True, exist_ok=True)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.connect(a.host, 1883)
    c.loop_start()
    ts = time.time() - 5000.0
    try:
        for mode, n in plan():
            event = {'event': 'mode_change', 'mode': mode, 'epoch': time.time(), 'run_id': run_id,
                     'truck_id': a.truck_id, 'synthetic': True, 'rehearsal': True}
            with log.open('a') as f:
                f.write(json.dumps(event) + '\n')
            print(f'phase {mode}: {n} messages', flush=True)
            for _ in range(n):
                ts += 10.0
                c.publish(f'logibridge/trucks/{a.truck_id}/inference',
                          json.dumps(inference_payload(ref, run_id, a.truck_id, ts, mode == 'combined')), qos=1)
                time.sleep(0.03)
            time.sleep(a.pause)
    finally:
        c.loop_stop()
        c.disconnect()
    print('rehearsal finished: now run python -m scripts.analyse_run --run-id ' + run_id)


if __name__ == '__main__':
    main()

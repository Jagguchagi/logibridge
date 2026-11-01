"""C1 sensor simulator. temperature 1 Hz N(4.0, 0.3); vibration_rms 0.5 Hz N(0.45, 0.05);
door_event OPEN/CLOSE. Modes (--anomaly): none | temp_drift (+0.08 C per reading) |
vibration (N(1.2, 0.15)) | combined.

Mid-run switching for E1, without restarting the process:
  --control   listen on logibridge/trucks/{id}/control/anomaly (python -m data_pipeline.control combined)
  --schedule  none:1200,combined:300,none:1500
Every mode change is written with its epoch to evidence/<run-id>/simulator_events.jsonl.
"""
import argparse
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

MODES = ['none', 'temp_drift', 'vibration', 'combined']
DRIFT, VIB = {'temp_drift', 'combined'}, {'vibration', 'combined'}


def parse_schedule(text):
    segments = []
    for part in text.split(','):
        mode, secs = part.strip().split(':')
        if mode not in MODES or int(secs) <= 0:
            raise ValueError(f'bad schedule segment {part!r}')
        segments.append((mode, int(secs)))
    return segments


def safe_run_id(run_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', run_id):
        raise ValueError('run id must be 1-64 letters, digits, - or _')
    return run_id


class Runner:
    def __init__(self, segments, seed=42):
        self.rng = np.random.default_rng(seed)
        self.boundaries, i = {}, 0
        for mode, secs in segments:
            self.boundaries[i] = mode
            i += secs
        self.total = i
        self.mode, self.mode_start, self._pending = segments[0][0], 0, None
        self._lock = threading.Lock()

    def request(self, mode):
        if mode not in MODES:
            raise ValueError(f'unknown mode {mode!r}')
        with self._lock:
            self._pending = mode

    def step(self, i, t):
        with self._lock:
            pending, self._pending = self._pending, None
        event = {'event': 'mode_change', 'mode': self.mode, 'source': 'start'} if i == 0 else None
        if i:
            new, source = (pending, 'control') if pending else (self.boundaries.get(i), 'schedule')
            if new and new != self.mode:
                self.mode, self.mode_start = new, i
                event = {'event': 'mode_change', 'mode': new, 'source': source}
        k = i - self.mode_start
        temp = self.rng.normal(4.0, 0.3) + (0.08 * k if self.mode in DRIFT else 0.0)
        out = [('temperature', {'timestamp': t, 'value': float(temp)})]
        if i % 2 == 0:
            mu, sd = (1.2, 0.15) if self.mode in VIB else (0.45, 0.05)
            out.append(('vibration_rms', {'timestamp': t, 'value': float(max(0.0, self.rng.normal(mu, sd)))}))
        if i % 120 == 0:
            out.append(('door_event', {'timestamp': t, 'value': 'OPEN'}))
        if i % 120 == 8:
            out.append(('door_event', {'timestamp': t, 'value': 'CLOSE'}))
        return out, event


def schedule_samples(segments, seed=42, start=0):
    r = Runner(segments, seed)
    for i in range(r.total):
        yield from r.step(i, float(start + i))[0]


def samples(mode='none', seconds=1200, seed=42, start=0):
    yield from schedule_samples([(mode, seconds)], seed, start)


def main():
    import paho.mqtt.client as mqtt
    p = argparse.ArgumentParser()
    p.add_argument('--anomaly', choices=MODES, default='none')
    p.add_argument('--seconds', type=int, default=1200)
    p.add_argument('--schedule')
    p.add_argument('--control', action='store_true')
    p.add_argument('--truck-id', default='T001')
    p.add_argument('--run-id', default=datetime.now().strftime('run%Y%m%d_%H%M%S'))
    p.add_argument('--host', default='localhost')
    p.add_argument('--seed', type=int, default=42)
    a = p.parse_args()
    run_id = safe_run_id(a.run_id)
    runner = Runner(parse_schedule(a.schedule) if a.schedule else [(a.anomaly, a.seconds)], a.seed)
    base = f'logibridge/trucks/{a.truck_id}'
    log = Path('evidence') / run_id / 'simulator_events.jsonl'
    if log.exists():
        raise SystemExit(f'{log} exists: use a new --run-id so evidence from different runs is never mixed')
    log.parent.mkdir(parents=True, exist_ok=True)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if a.control:
        client.on_connect = lambda c, u, f, rc, pr=None: c.subscribe(base + '/control/anomaly', qos=1)

        def on_message(c, u, msg):
            try:
                runner.request(msg.payload.decode().strip())
            except (ValueError, UnicodeDecodeError) as exc:
                print(f'CONTROL IGNORED: {exc}', flush=True)
        client.on_message = on_message
    client.connect(a.host, 1883)
    client.loop_start()
    print(f'RUN_ID={run_id}', flush=True)
    start = time.time()
    try:
        for i in range(runner.total):
            time.sleep(max(0.0, start + i - time.time()))
            msgs, event = runner.step(i, float(start + i))
            if event:
                event.update(epoch=time.time(), run_id=run_id, truck_id=a.truck_id, synthetic=True)
                line = json.dumps(event)
                print(line, flush=True)
                with log.open('a') as f:
                    f.write(line + '\n')
            for stream, msg in msgs:
                msg.update(run_id=run_id, truck_id=a.truck_id)
                info = client.publish(f'{base}/sensors/{stream}', json.dumps(msg),
                                      qos=1 if stream == 'door_event' else 0)
                if stream == 'door_event':
                    info.wait_for_publish(timeout=5)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == '__main__':
    main()

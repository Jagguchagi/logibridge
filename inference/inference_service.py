"""D2 inference service: MQTT sensors -> preprocessing -> TFLite -> logibridge/trucks/{truck_id}/inference.

Environment: MODEL_PATH (switch variants without rebuild), STATS_PATH, TRUCK_ID, MQTT_HOST,
STATE_DIR (durable outbox), BACKEND_URL (optional sync target), RUN_ID (optional).
RUN_ID: if set, only that simulator run is processed; if unset, the first run seen is latched.
Messages from another run are counted and reported, never silently dropped.
A separate temperature safety rule (|T-4| > 1 Warning, > 3 Critical) escalates alerts but is never
mixed into model metrics: payloads carry model_class, safety_class and effective_class.
"""
import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path

import numpy as np

from data_pipeline.preprocessing import Pipeline, normalize, validate_pipeline_contract, pipeline_sha256
from inference.alert_store import Outbox
from inference.runtime import Model
from inference.safety import safety_class

def safe_run_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise ValueError("invalid run identity")
    return value


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import paho.mqtt.client as mqtt
    truck = os.getenv('TRUCK_ID', 'T001')
    model_path = os.getenv('MODEL_PATH', '/app/model.tflite')
    stats_path = os.getenv('STATS_PATH', '/app/training_stats.npy')
    validate_pipeline_contract(model_path, stats_path)
    model, stats = Model(model_path), np.load(stats_path)
    normalize(np.zeros(6), stats)  # validates the stats file
    mh, sh = sha256(model_path), sha256(stats_path)
    state = Path(os.getenv('STATE_DIR', '/state'))
    state.mkdir(parents=True, exist_ok=True)
    outbox = Outbox(state / 'alerts.sqlite')
    base = f'logibridge/trucks/{truck}'
    s = {'run_id': os.getenv('RUN_ID') or None, 'other_run': 0, 'pipe': Pipeline()}
    lock, stop = threading.Lock(), threading.Event()
    print(json.dumps({'event': 'startup', 'model_path': model_path, 'model_version': mh[:12],
                      'stats_sha256': sh, 'pipeline_sha256': pipeline_sha256(), 'run_id': s['run_id'] or 'latch-first'}), flush=True)

    def on_message(client, userdata, msg):
        try:
            d = json.loads(msg.payload)
            if not isinstance(d, dict) or d.get('truck_id') != truck:
                raise ValueError('missing or mismatched truck identity')
            safe_run_id(d.get('run_id', ''))
            t = float(d['timestamp'])
            if not np.isfinite(t) or t > time.time() + 5:
                raise ValueError('invalid or future timestamp')
            with lock:
                run = d['run_id']
                if s['run_id'] is None:
                    s['run_id'] = run
                if run != s['run_id']:
                    s['other_run'] += 1
                    if s['other_run'] in (1, 10, 100) or s['other_run'] % 1000 == 0:
                        print(f"WARNING: {s['other_run']} message(s) from run '{run}' ignored; this service "
                              f"processes run '{s['run_id']}'. Restart it or set RUN_ID.", flush=True)
                    return
                for end, x in s['pipe'].push(msg.topic.rsplit('/', 1)[-1], d):
                    tick = time.perf_counter()
                    p = model.predict(normalize(x, stats))
                    latency = (time.perf_counter() - tick) * 1000
                    mc, rule = int(p.argmax()), safety_class(x[0])
                    row = {'timestamp': end, 'emitted_at': time.time(), 'run_id': s['run_id'], 'truck_id': truck,
                           'model_version': mh[:12], 'model_sha256': mh, 'stats_sha256': sh, 'pipeline_sha256': pipeline_sha256(),
                           'probabilities': p.tolist(), 'confidence': float(p.max()), 'model_class': mc,
                           'safety_class': rule, 'effective_class': max(mc, rule), 'latency_ms': latency,
                           'input_clipped': model.last_clipped.tolist(), 'door': s['pipe'].door}
                    client.publish(base + '/inference', json.dumps(row), qos=1)
                    if row['effective_class'] > 0:
                        row['alert_id'] = outbox.add(row)
                        print('[LOCAL ALERT] ' + json.dumps(row), flush=True)
        except (ValueError, KeyError, TypeError) as exc:
            print(f'INPUT REJECTED: {exc}', flush=True)

    def sync():
        import requests
        while not stop.is_set():
            url = os.getenv('BACKEND_URL', '')
            if url:
                for alert_id, payload in outbox.pending():
                    try:
                        r = requests.post(url, json=json.loads(payload), timeout=3)
                        r.raise_for_status()
                        if r.json().get('alert_id') == alert_id:
                            outbox.ack(alert_id)
                    except (requests.RequestException, ValueError):
                        break  # backend unreachable: keep alerts, retry later
            stop.wait(10)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = lambda c, u, f, rc, pr=None: c.subscribe(base + '/sensors/#', qos=1)
    client.on_message = on_message
    client.connect(os.getenv('MQTT_HOST', 'localhost'), 1883)
    client.loop_start()
    threading.Thread(target=sync, daemon=True).start()
    try:
        while True:
            time.sleep(60)
            print(json.dumps({'event': 'outbox', **outbox.counts()}), flush=True)
    finally:
        stop.set()
        client.loop_stop()
        client.disconnect()


if __name__ == '__main__':
    main()

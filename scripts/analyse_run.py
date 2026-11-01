"""E1 + A1/F3 evidence from logs (never estimates).
PSI: needs a recent clean baseline (<0.10 within 120 s before injection), a crossing >0.25 within
300 s of injection, drift still present at restore, and recovery <0.10 after restore.
SLA: first local alert emitted at/after injection, measured from the simulator's mode-change epoch.
Usage: docker logs logibridge > evidence/<run>/container.log 2>&1
       python -m scripts.analyse_run --run-id <run> [--container-log evidence/<run>/container.log]"""
import argparse
import json
import math
from pathlib import Path

from data_pipeline.simulator import safe_run_id


def transitions(events):
    inj = rest = prev = None
    for e in sorted(events, key=lambda e: e['epoch']):
        if e.get('event') != 'mode_change':
            continue
        if inj is None and prev == 'none' and e['mode'] == 'combined':
            inj = float(e['epoch'])
        elif inj is not None and rest is None and e['mode'] == 'none':
            rest = float(e['epoch'])
        prev = e['mode']
    return inj, rest


def analyse_psi(events, rows):
    if not rows:
        raise ValueError('no PSI rows')
    for row in rows:
        if not math.isfinite(float(row['epoch'])) or any(not math.isfinite(float(v)) or float(v) < 0 for v in row['all_scores'].values()):
            raise ValueError('invalid PSI evidence')
    ids = {(r['run_id'], r['truck_id'], r['model_sha256'], r['stats_sha256'], r['score']) for r in rows}
    if len(ids) != 1:
        raise ValueError('PSI log mixes runs, models or scores')
    run, truck = rows[0]['run_id'], rows[0]['truck_id']
    if any(e.get('run_id') != run or e.get('truck_id') != truck for e in events):
        raise ValueError('simulator events belong to a different run')
    inj, rest = transitions(events)
    if inj is None:
        raise ValueError('no switch from none to an anomaly mode found')
    out = {'run_id': run, 'selected_score': rows[0]['score'], 'injected_at': inj, 'restored_at': rest, 'model_sha256': rows[0]['model_sha256'], 'stats_sha256': rows[0]['stats_sha256'], 'pipeline_sha256': rows[0].get('pipeline_sha256'), 'scores': {}}
    for score in rows[0]['all_scores']:
        o = sorted(rows, key=lambda r: r['epoch'])
        v = lambda r: r['all_scores'][score]
        before = [r for r in o if r['epoch'] < inj]
        during = [r for r in o if inj <= r['epoch'] < (rest or float('inf'))]
        after = [r for r in o if rest is not None and r['epoch'] >= rest]
        cross = next((r for r in during if v(r) > 0.25), None)
        rec = next((r for r in after if v(r) < 0.10), None)
        base_ok = bool(before and inj - before[-1]['epoch'] <= 120 and v(before[-1]) < 0.10)
        out['scores'][score] = {
            'baseline_psi': v(before[-1]) if before else None, 'recent_clean_baseline': base_ok,
            'crossing_delay_s': round(cross['epoch'] - inj, 1) if cross else None,
            'crossing_within_5_min': bool(cross and cross['epoch'] - inj <= 300),
            'peak_psi': max((v(r) for r in during), default=None),
            'drift_present_at_restore': bool(rest is not None and during and rest - during[-1]['epoch'] <= 120 and v(during[-1]) > 0.25),
            'recovery_delay_s': round(rec['epoch'] - rest, 1) if rec else None,
            'recovered_below_0_10': rec is not None}
    s = out['scores'][out['selected_score']]
    out['interval_ok'] = all(r.get('interval_s') == 60 for r in rows)  # missing = unknown = not evidence
    out['e1_pass'] = all([s['recent_clean_baseline'], s['crossing_within_5_min'],
                          s['drift_present_at_restore'], s['recovered_below_0_10'], out['interval_ok']])
    return out


def analyse_sla(injected, alerts, run_id):
    if injected is None:
        raise ValueError('no none -> combined injection in the simulator log; SLA cannot be timed')
    if type(injected) not in (int, float) or not math.isfinite(injected):
        raise ValueError('invalid injection timestamp')
    for a in alerts:
        if not isinstance(a, dict):
            raise ValueError('alert must be object')
        if a.get('run_id') == run_id:
            if type(a.get('emitted_at')) not in (int, float) or not math.isfinite(a['emitted_at']) or type(a.get('effective_class')) is not int or a['effective_class'] not in (0, 1, 2):
                raise ValueError('invalid alert timestamp/class')
    mine = [a for a in alerts if a.get('run_id') == run_id and a.get('effective_class', 0) > 0]
    early = sum(1 for a in mine if float(a['emitted_at']) < injected)
    times = [float(a['emitted_at']) for a in mine if float(a['emitted_at']) >= injected]
    delay = min(times) - injected if times else None
    return {'fault_to_alert_s': delay, 'sla_s': 90, 'alerts_before_injection': early,
            'pass': delay is not None and delay <= 90 and early == 0,
            'note': 'alerts_before_injection must be 0 for a clean baseline; clocks must be on one host or NTP-synced'}


def parse_alerts(text):
    out = []
    for line in text.splitlines():
        if '[LOCAL ALERT] ' in line:
            try:
                out.append(json.loads(line.split('[LOCAL ALERT] ', 1)[1]))
            except json.JSONDecodeError:
                pass
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--container-log')
    a = p.parse_args()
    folder = Path('evidence') / safe_run_id(a.run_id)
    read = lambda n: [json.loads(l) for l in (folder / n).read_text().splitlines() if l.strip()]
    events = read('simulator_events.jsonl')
    result = {'psi': analyse_psi(events, read('psi_live.jsonl'))}
    if a.container_log:
        result['sla'] = analyse_sla(transitions(events)[0], parse_alerts(Path(a.container_log).read_text()), a.run_id)
    (folder / 'analysis.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

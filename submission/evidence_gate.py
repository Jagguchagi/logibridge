"""Supplemental fail-closed checks. Existence is not proof of genuine live execution."""
import json, hashlib, math
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def checks(root, run_id):
    r=Path(root); problems=[]
    def load(name):
        try:
            value = json.loads((r/name).read_text())
            if not isinstance(value, dict) or not value:
                raise ValueError('expected nonempty object')
            return value
        except (OSError, ValueError):
            problems.append('Missing or invalid evidence: '+name); return None
    analysis=load('evidence/'+run_id+'/analysis.json')
    if analysis:
        sla=analysis.get('sla')
        if not isinstance(sla,dict) or sla.get('pass') is not True:
            problems.append('Mandatory SLA evidence missing or failed')
        elif type(sla.get('fault_to_alert_s')) not in (int,float) or not math.isfinite(sla['fault_to_alert_s']) or not 0 <= sla['fault_to_alert_s'] <= 90:
            problems.append('Invalid SLA timing')
        if isinstance(sla, dict) and (sla.get('sla_s') != 90 or type(sla.get('alerts_before_injection')) is not int or sla.get('alerts_before_injection') != 0):
            problems.append('SLA budget or clean baseline not established')
        psi = analysis.get('psi')
        if not isinstance(psi, dict) or psi.get('run_id') != run_id or psi.get('e1_pass') is not True or psi.get('interval_ok') is not True:
            problems.append('E1 PSI identity/crossing/recovery not established')
        recomputed = recompute(r, run_id)
        if recomputed is None:
            problems.append('Raw run logs missing: evidence/<run>/simulator_events.jsonl and psi_live.jsonl are required')
        elif not isinstance(psi, dict) or recomputed != psi:
            problems.append('analysis.json E1 result does not match recomputation from raw logs')
        replayed_sla = recompute_sla(r, run_id)
        if replayed_sla is None:
            problems.append('SLA raw logs missing or invalid: evidence/<run>/container.log required')
        elif not isinstance(sla, dict) or any(sla.get(k) != replayed_sla.get(k) for k in ('fault_to_alert_s', 'sla_s', 'alerts_before_injection', 'pass')):
            problems.append('analysis.json SLA does not match recomputation from raw logs')
        if recomputed is not None and (r/'inference/model.tflite').is_file() and (r/'data_pipeline/training_stats.npy').is_file():
            from data_pipeline.preprocessing import pipeline_sha256
            if recomputed.get('model_sha256') != sha(r/'inference/model.tflite') or recomputed.get('stats_sha256') != sha(r/'data_pipeline/training_stats.npy') or recomputed.get('pipeline_sha256') != pipeline_sha256():
                problems.append('Raw PSI evidence belongs to stale model/stats/preprocessing')
    ota=load('evidence/ota_savings.json')
    if ota and ota.get('only_last_layer_changed') is not True:
        problems.append('OTA model-only layer change not established')
    from data_pipeline.preprocessing import validate_pipeline_contract
    if (r/'inference/model.tflite').is_file() and (r/'data_pipeline/training_stats.npy').is_file():
        try:
            validate_pipeline_contract(r/'inference/model.tflite', r/'data_pipeline/training_stats.npy')
        except ValueError:
            problems.append('Deployed preprocessing contract missing or stale')
    selection=load('evidence/model_selection.json')
    reference=load('monitoring/reference_dist.json')
    try:
        mh=sha(r/'inference/model.tflite'); sh=sha(r/'data_pipeline/training_stats.npy')
        if selection and selection.get('model_sha256') != mh: problems.append('Selected model hash is stale')
        if reference and (reference.get('model_sha256') != mh or reference.get('stats_sha256') != sh): problems.append('Reference hashes are stale')
    except OSError: problems.append('Deployed model/stats missing')
    smoke = r/'evidence/container_smoke.txt'
    if smoke.exists():
        txt = smoke.read_text(errors='replace')
        if txt.count('PASS ') < 4 or 'FAIL' in txt or 'Traceback' in txt:
            problems.append('Container smoke evidence does not show 4 passing models')
        elif 'PASS /app/model.tflite' not in txt:
            problems.append('Container smoke evidence does not include the baked deployed model')
        else:
            try:
                want = 'PASS /app/model.tflite sha256=' + sha(r/'inference/model.tflite')
                if want not in txt:
                    problems.append('Container smoke was not run against the current deployed model (hash mismatch)')
            except OSError:
                pass
            for f in ('M1_fp32.tflite', 'M2_int8.tflite', 'M3_pruned_int8.tflite'):
                mp = r/'training/models'/f
                if not mp.is_file():
                    continue  # missing model files are reported by verify_submission REQUIRED
                if f'PASS /models/{f} sha256={sha(mp)}' not in txt:
                    problems.append(f'Container smoke does not cover current {f} (missing line or hash mismatch)')
    else:
        problems.append('Missing evidence: evidence/container_smoke.txt')
    for name in ['reports/phase1_report.pdf','reports/phase2_report.pdf']:
        p=r/name
        if not p.exists() or not p.read_bytes().startswith(b'%PDF-'): problems.append('Missing or invalid PDF: '+name)
    final = final_report(r)
    if final is None:
        problems.append('Missing or invalid PDF: reports/<GROUPNO>_LogiEdge_Final.pdf (or reports/final_report.pdf)')
    return problems

def recompute(r, run_id):
    """Re-run the E1 analysis on the raw logs; None if logs are missing or unreadable."""
    from scripts.analyse_run import analyse_psi
    folder = Path(r) / 'evidence' / run_id
    try:
        read = lambda n: [json.loads(l) for l in (folder / n).read_text().splitlines() if l.strip()]
        return analyse_psi(read('simulator_events.jsonl'), read('psi_live.jsonl'))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None

def recompute_sla(r, run_id):
    from scripts.analyse_run import transitions, analyse_sla, parse_alerts
    folder = Path(r) / 'evidence' / run_id
    try:
        events = [json.loads(l) for l in (folder/'simulator_events.jsonl').read_text().splitlines() if l.strip()]
        if any(not isinstance(e, dict) or e.get('run_id') != run_id for e in events):
            raise ValueError('wrong run events')
        return analyse_sla(transitions(events)[0], parse_alerts((folder/'container.log').read_text()), run_id)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None

def final_report(r):
    """The brief names the final report GROUPNO_LogiEdge_Final.pdf; reports/final_report.pdf is accepted as a fallback."""
    r = Path(r)
    for p in sorted((r/'reports').glob('*_LogiEdge_Final.pdf')) + [r/'reports/final_report.pdf']:
        if p.is_file() and p.read_bytes().startswith(b'%PDF-') and not p.name.upper().startswith('GROUPNO'):
            return p
    return None

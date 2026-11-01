"""v11 (Claude, final code release) regressions for the remaining P1 items from GPT v10."""
import hashlib
import json

import pytest

from scripts.verify_bridge import parse
from submission.evidence_gate import checks
from tests.test_v9_regressions import new_block

EV = [{'event': 'mode_change', 'mode': m, 'epoch': e, 'run_id': 'r', 'truck_id': 'T001'}
      for m, e in [('none', 0), ('combined', 1000), ('none', 1300)]]
PSI = [{'epoch': e, 'run_id': 'r', 'truck_id': 'T001', 'model_sha256': 'm', 'stats_sha256': 's',
        'score': 'normal_probability', 'interval_s': 60,
        'all_scores': {'normal_probability': v, 'max_probability': .01}}
       for e, v in [(940, .02), (1120, .31), (1240, .9), (1600, .05)]]


def write_run(tmp, e1_claim):
    d = tmp / 'evidence/r'
    d.mkdir(parents=True)
    (d / 'simulator_events.jsonl').write_text('\n'.join(json.dumps(x) for x in EV))
    (d / 'psi_live.jsonl').write_text('\n'.join(json.dumps(x) for x in PSI))
    (d / 'container.log').write_text('[LOCAL ALERT] '+json.dumps({'run_id':'r','effective_class':2,'emitted_at':1040.0})+'\n')
    (d / 'analysis.json').write_text(json.dumps({
        'psi': dict(__import__('scripts.analyse_run', fromlist=['analyse_psi']).analyse_psi(EV, PSI), e1_pass=e1_claim),
        'sla': {'pass': True, 'fault_to_alert_s': 40.0, 'sla_s': 90, 'alerts_before_injection': 0}}))


def test_analysis_matching_raw_logs_accepted(tmp_path):
    write_run(tmp_path, True)
    assert not any('raw logs' in p.lower() or 'recomputation' in p for p in checks(tmp_path, 'r'))


def test_hand_edited_analysis_rejected(tmp_path):
    write_run(tmp_path, True)
    rows = PSI[:]
    rows[-1] = dict(rows[-1], all_scores={'normal_probability': .5, 'max_probability': .01})  # never recovered
    (tmp_path / 'evidence/r/psi_live.jsonl').write_text('\n'.join(json.dumps(x) for x in rows))
    assert any('recomputation' in p for p in checks(tmp_path, 'r'))


def test_analysis_without_raw_logs_rejected(tmp_path):
    d = tmp_path / 'evidence/r'
    d.mkdir(parents=True)
    (d / 'container.log').write_text('[LOCAL ALERT] '+json.dumps({'run_id':'r','effective_class':2,'emitted_at':1040.0})+'\n')
    (d / 'analysis.json').write_text(json.dumps({'psi': {'run_id': 'r', 'e1_pass': True, 'interval_ok': True},
                                                'sla': {'pass': True, 'fault_to_alert_s': 1.0, 'sla_s': 90,
                                                        'alerts_before_injection': 0}}))
    assert any('Raw run logs missing' in p for p in checks(tmp_path, 'r'))


def test_smoke_must_cover_each_current_model(tmp_path):
    (tmp_path / 'inference').mkdir()
    (tmp_path / 'training/models').mkdir(parents=True)
    (tmp_path / 'inference/model.tflite').write_bytes(b'dep')
    h = lambda b: hashlib.sha256(b).hexdigest()
    for f in ('M1_fp32.tflite', 'M2_int8.tflite', 'M3_pruned_int8.tflite'):
        (tmp_path / 'training/models' / f).write_bytes(f.encode())
    (tmp_path / 'evidence').mkdir()
    lines = [f"PASS /app/model.tflite sha256={h(b'dep')}"] + \
        [f"PASS /models/{f} sha256={h(f.encode())}" for f in ('M1_fp32.tflite', 'M2_int8.tflite', 'M3_pruned_int8.tflite')]
    (tmp_path / 'evidence/container_smoke.txt').write_text('\n'.join(lines) + '\n')
    assert not any('smoke' in p.lower() for p in checks(tmp_path, 'r'))
    (tmp_path / 'evidence/container_smoke.txt').write_text('\n'.join(lines[:2] + [lines[1]] * 2) + '\n')
    assert any('M2_int8.tflite' in p for p in checks(tmp_path, 'r'))


def test_inventory_garbage_and_control_chars_rejected():
    good = 'h' + new_block('a.py', 'x') + '\n## Binary inventory\n'
    with pytest.raises(ValueError, match='unrecognised'):
        parse(good + 'surprise line\n## END OF BRIDGE: files=1 binaries=0\n')
    with pytest.raises(ValueError, match='unsafe'):
        parse('h' + new_block('a\tb.py', 'x') + '\n## Binary inventory\n## END OF BRIDGE: files=1 binaries=0\n')


def test_normalize_saturates_far_out_of_range_but_keeps_3_sigma():
    import numpy as np
    from data_pipeline.preprocessing import CLIP_Z, normalize
    s = np.stack([np.zeros(6), np.ones(6)]).astype(np.float32)
    assert normalize(np.full(6, 1e4), s).max() == CLIP_Z and normalize(np.full(6, -1e4), s).min() == -CLIP_Z
    np.testing.assert_allclose(normalize(np.zeros(6), np.stack([s[0] + 3, s[1]])), -3)


def test_standin_critical_recall_stable_across_seeds():
    """Regression for the out-of-range temperature problem (recall was 72-100% by seed before saturation)."""
    import numpy as np
    from sklearn.metrics import recall_score
    from sklearn.neural_network import MLPClassifier
    from data_pipeline.preprocessing import normalize
    d = np.load('training/data/dataset.npz')
    X, y = normalize(d['X'], np.load('data_pipeline/training_stats.npy')), d['y']
    for seed in (42, 2):
        clf = MLPClassifier((32, 16), max_iter=2000, random_state=seed).fit(X[d['train']], y[d['train']])
        assert recall_score(y[d['val']], clf.predict(X[d['val']]), labels=[2], average=None)[0] > 0.95

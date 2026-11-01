"""v6 (Claude) regressions for issues left open in GPT v5."""
import time

import numpy as np
import pytest

from monitoring.drift_monitor import STALE_S, Window, build_reference
from scripts.analyse_run import analyse_psi, analyse_sla
from submission.evidence_gate import checks


def ref():
    return build_reference(np.tile([.9, .05, .05], (300, 1)), 'm', 's')


def row(t, p=(.9, .05, .05)):
    return dict(probabilities=list(p), timestamp=t, model_sha256='m', stats_sha256='s', run_id='r', truck_id='T001')


def test_buffer_cleared_after_gap_not_mixed():
    w = Window(ref(), 'r')
    for i in range(100):
        w.add(row(i))
    w.last_arrival = time.monotonic() - STALE_S - 1      # simulate an outage
    assert w.add(row(1000, (.01, .01, .98)))
    values, n, _ = w.check()
    assert values is None and n == 1                      # old 100 scores were discarded


def rows(interval):
    return [{'epoch': e, 'run_id': 'r', 'truck_id': 'T001', 'model_sha256': 'm', 'stats_sha256': 's',
             'score': 'normal_probability', 'interval_s': interval,
             'all_scores': {'normal_probability': v, 'max_probability': .01}}
            for e, v in [(940, .02), (1120, .31), (1240, .9), (1600, .05)]]


EV = [{'event': 'mode_change', 'mode': m, 'epoch': e, 'run_id': 'r', 'truck_id': 'T001'}
      for m, e in [('none', 0), ('combined', 1000), ('none', 1300)]]


def test_rehearsal_interval_never_counts_as_evidence():
    assert analyse_psi(EV, rows(60))['e1_pass']
    r = analyse_psi(EV, rows(10))
    assert not r['interval_ok'] and not r['e1_pass']


def test_sla_without_injection_is_clear_error():
    with pytest.raises(ValueError, match='injection'):
        analyse_sla(None, [], 'r')


def test_failed_smoke_evidence_rejected(tmp_path):
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'evidence/container_smoke.txt').write_text('PASS a\nPASS b\nFAIL: reconvert\n')
    assert any('smoke' in p.lower() for p in checks(tmp_path, 'r'))
    (tmp_path / 'evidence/container_smoke.txt').write_text('PASS /app/model.tflite\nPASS b\nPASS c\nPASS d\n')
    assert not any('smoke' in p.lower() for p in checks(tmp_path, 'r'))

"""v7 (GPT) regressions."""
import hashlib

import pytest

from scripts.analyse_run import analyse_psi
from scripts.verify_bridge import parse
from submission.evidence_gate import checks

EV = [{'event': 'mode_change', 'mode': m, 'epoch': e, 'run_id': 'r', 'truck_id': 'T001'}
      for m, e in [('none', 0), ('combined', 1000), ('none', 1300)]]


def rows(**extra):
    return [dict({'epoch': e, 'run_id': 'r', 'truck_id': 'T001', 'model_sha256': 'm', 'stats_sha256': 's',
                  'score': 'normal_probability', 'all_scores': {'normal_probability': v, 'max_probability': .01}}, **extra)
            for e, v in [(940, .02), (1120, .31), (1240, .9), (1600, .05)]]


def test_missing_interval_is_not_evidence():
    assert analyse_psi(EV, rows(interval_s=60))['e1_pass']
    r = analyse_psi(EV, rows())
    assert not r['interval_ok'] and not r['e1_pass']


def test_smoke_must_cover_deployed_model(tmp_path):
    (tmp_path / 'evidence').mkdir()
    (tmp_path / 'evidence/container_smoke.txt').write_text('PASS /models/a\nPASS /models/b\nPASS /models/c\nPASS /models/d\n')
    assert any('baked deployed model' in p for p in checks(tmp_path, 'r'))


def block(name, body):
    return f'\n## FILE: {name}\nSHA256: {hashlib.sha256(body.encode()).hexdigest()}\n````\n{body}\n````\n'


def test_bridge_parse_rejects_tamper_unsafe_and_duplicates():
    good = 'header' + block('a.py', 'x = 1')
    assert parse(good)[0][0][0] == 'a.py'
    with pytest.raises(ValueError, match='mismatch'):
        parse(good.replace('x = 1', 'x = 2'))
    with pytest.raises(ValueError, match='unsafe'):
        parse('h' + block('../evil.py', 'y'))
    with pytest.raises(ValueError, match='duplicate'):
        parse('h' + block('a.py', 'x') + block('a.py', 'x'))

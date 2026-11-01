"""V15 (Claude) regressions: defects found by running the package on real TensorFlow and a real broker."""
import json
import sys
import types
from pathlib import Path

import pytest

from monitoring.drift_monitor import Window
from scripts import rehearse_monitor as rm

ROOT = Path(__file__).resolve().parents[1]
REF = {'model_sha256': 'm' * 64, 'stats_sha256': 's' * 64, 'pipeline_sha256': 'p' * 64,
       'distributions': {'normal_probability': [.01, .01, .01, .97], 'max_probability': [.01, .01, .01, .97]}}


def test_pruning_default_is_the_method_that_works_on_real_tensorflow():
    s = (ROOT / 'training/prune_quantise.py').read_text()
    assert "default='custom'" in s and "default='tfmot'" not in s
    assert 'Input tensor must be rank 2' in s and "'rank 2' in str(exc)" in s   # clear message for the known tfmot failure


def test_docs_describe_custom_pruning_not_the_broken_default():
    disclosures = (ROOT / 'docs/DISCLOSURES.md').read_text()
    assert 'rank 2' in disclosures and 'vibration' in disclosures.lower()
    runbook = (ROOT / 'docs/RUNBOOK.md').read_text()
    assert 'check the TFMOT version' not in runbook and 'zero_columns should be [11, 6]' in runbook


def test_rehearsal_payload_is_accepted_by_the_real_monitor_window():
    w = Window(REF, 'rehearse01', 'T001', require_pipeline=True)
    ts = 1000.0
    for i in range(100):
        assert w.add(rm.inference_payload(REF, 'rehearse01', 'T001', ts + 10 * i, critical=False))
    values, n, _ = w.check()
    assert n == 100 and values['normal_probability'] < 0.1
    for i in range(20):
        w.add(rm.inference_payload(REF, 'rehearse01', 'T001', 5000.0 + 10 * i, critical=True))
    assert w.check()[0]['normal_probability'] > 0.25          # the fault phase must cross the alert threshold


def test_rehearsal_main_publishes_every_phase_and_writes_events(tmp_path, monkeypatch):
    published = []

    class FakeClient:
        def __init__(self, *a, **k): pass
        def connect(self, *a): pass
        def loop_start(self): pass
        def loop_stop(self): pass
        def disconnect(self): pass
        def publish(self, topic, payload, qos=0): published.append((topic, json.loads(payload)))

    paho = types.ModuleType('paho'); mqtt = types.ModuleType('paho.mqtt'); client = types.ModuleType('paho.mqtt.client')
    client.Client = FakeClient
    client.CallbackAPIVersion = types.SimpleNamespace(VERSION2=2)
    mqtt.client = client; paho.mqtt = mqtt
    for name, mod in (('paho', paho), ('paho.mqtt', mqtt), ('paho.mqtt.client', client)):
        monkeypatch.setitem(sys.modules, name, mod)
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'monitoring').mkdir()
    (tmp_path / 'monitoring/reference_dist.json').write_text(json.dumps(REF))
    monkeypatch.setattr(rm.time, 'sleep', lambda s: None)
    monkeypatch.setattr(sys, 'argv', ['rehearse_monitor', '--run-id', 'rehearse01'])
    rm.main()
    assert len(published) == 110 + 20 + 115
    assert all(t == 'logibridge/trucks/T001/inference' for t, _ in published)
    ts = [p['timestamp'] for _, p in published]
    assert ts == sorted(ts) and len(set(ts)) == len(ts)         # monitor drops duplicates and out-of-order messages
    events = [json.loads(l) for l in (tmp_path / 'evidence/rehearse01/simulator_events.jsonl').read_text().splitlines()]
    assert [e['mode'] for e in events] == ['none', 'combined', 'none'] and all(e['rehearsal'] for e in events)
    monkeypatch.setattr(sys, 'argv', ['rehearse_monitor', '--run-id', 'rehearse01'])
    with pytest.raises(SystemExit):                              # same run id twice is refused
        rm.main()


def test_quality_check_accepts_missing_bridge_but_rejects_stale_one():
    s = (ROOT / 'scripts/quality_check.py').read_text()
    assert 'no bridge file shipped' in s and 'Stale bridge files present' in s


def test_history_is_separated_from_current_docs():
    top = sorted(p.name for p in (ROOT / 'docs').glob('*.md'))
    assert not [n for n in top if n.startswith('JOINT_REVIEW') and n != 'JOINT_REVIEW_V15.md'], top
    assert list((ROOT / 'docs/history').glob('JOINT_REVIEW_V14.md'))
    assert (ROOT / 'docs/HANDOVER_TO_GPT.md').is_file() and (ROOT / 'docs/SANDBOX_VERIFICATION.md').is_file()


def test_architecture_image_is_the_code_faithful_drawing():
    png = (ROOT / 'scenario_architecture/system_architecture.png').read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n' and 50_000 < len(png) < 600_000
    mmd = (ROOT / 'scenario_architecture/system_architecture.mmd').read_text()
    for word in ('safety rule', 'outbox', 'ACK', 'PSI drift monitor', 'MODEL_PATH'):
        assert word in mmd, word


def _crlf_bridge(tmp_path):
    """A bridge holding one file with Windows line endings, exactly as make_snapshot writes it (bytes decoded, not translated)."""
    from tests.test_v9_regressions import new_block
    body = 'variant,mean_ms\r\nM1,0.01\r\nM2,0.12\r\n'          # what Python's csv module writes for benchmark_results.csv
    text = ('h' + new_block('optimisation/results/benchmark_results.csv', body) + new_block('b.py', 'x=1') +
            '\n## Binary inventory\n## END OF BRIDGE: files=2 binaries=0\n')
    bridge = tmp_path / 'BRIDGE_CLAUDE_GPT_V15.txt'
    with open(bridge, 'w', encoding='utf-8', newline='') as f:   # newline='' keeps the \r\n bytes untouched
        f.write(text)
    return bridge, body


def test_bridge_with_a_crlf_file_restores_byte_for_byte(tmp_path):
    """V14 read the bridge in text mode, which turned \\r\\n into \\n, so CHARS no longer matched and restore failed."""
    from scripts.verify_bridge import restore
    bridge, body = _crlf_bridge(tmp_path)
    dest = tmp_path / 'restored'
    files, _, complete = restore(bridge, dest)
    assert complete and len(files) == 2
    assert (dest / 'optimisation/results/benchmark_results.csv').read_bytes() == body.encode()


def test_quality_check_reads_the_bridge_without_newline_translation():
    s = (ROOT / 'scripts/quality_check.py').read_text()
    assert "newline=''" in s and "read_bytes().decode('utf-8') != body" in s

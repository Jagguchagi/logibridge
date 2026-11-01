"""Runtime, compaction, PSI, analysers, selection, OTA arithmetic (no TensorFlow needed)."""
import sys
import types

import numpy as np
import pytest

from monitoring.drift_monitor import SCORES, Window, build_reference, distribution, psi
from scripts.analyse_run import analyse_psi, analyse_sla, parse_alerts
from scripts.ota_savings import compare
from scripts.run_ansible_twice import recap_ok
from scripts.run_logged import run
from scripts.select_model import choose
from training.compaction import fold_and_compact


def fake_tf(monkeypatch, scale=0.1):
    class I:
        def __init__(self, **k): self.x = None
        def allocate_tensors(self): pass
        def get_input_details(self): return [{'index': 0, 'shape': np.array([1, 6]), 'dtype': np.int8, 'quantization': (scale, 0)}]
        def get_output_details(self): return [{'index': 1, 'shape': np.array([1, 3]), 'dtype': np.int8, 'quantization': (1 / 255, -128)}]
        def set_tensor(self, i, x): self.x = x
        def invoke(self): pass
        def get_tensor(self, i): return np.array([[127, -128, -128]], dtype=np.int8)
    monkeypatch.setitem(sys.modules, 'tflite_runtime', None)
    monkeypatch.setitem(sys.modules, 'tflite_runtime.interpreter', None)
    tf = types.ModuleType('tensorflow')
    tf.lite = types.SimpleNamespace(Interpreter=I)
    monkeypatch.setitem(sys.modules, 'tensorflow', tf)


def test_runtime_fallback_dequantise_and_clipping(monkeypatch):
    fake_tf(monkeypatch)
    from inference.runtime import Model
    m = Model('x')
    np.testing.assert_allclose(m.predict([100, 0, 0, 0, 0, 0]), [1, 0, 0], atol=1e-6)
    assert m.last_clipped.tolist() == [True] + [False] * 5
    m.predict(np.zeros(6))
    assert not m.last_clipped.any()
    with pytest.raises(ValueError):
        m.predict([np.nan] * 6)


def test_runtime_rejects_zero_scale(monkeypatch):
    fake_tf(monkeypatch, scale=0)
    from inference.runtime import Model
    with pytest.raises(ValueError):
        Model('x').predict(np.zeros(6))


def fwd(x, w):
    return np.maximum(np.maximum(x @ w[0] + w[1], 0) @ w[2] + w[3], 0) @ w[4] + w[5]


def test_compaction_exact_including_cascade():
    rng = np.random.default_rng(1)
    w = [rng.normal(size=s) for s in [(6, 32), (32,), (32, 16), (16,), (16, 3), (3,)]]
    w[0][:, :4] = 0
    w[1][:4] = [2, -1, .3, 0]
    w[2][4:, 2] = 0
    c, rep = fold_and_compact(w)
    x = rng.normal(size=(300, 6))
    np.testing.assert_allclose(fwd(x, w), fwd(x, c), atol=1e-10)
    assert rep['compact_widths'] == [28, 15]
    with pytest.raises(ValueError):
        fold_and_compact([np.zeros((6, 2)), np.ones(2), np.ones((2, 2)), np.ones(2), np.ones((2, 3)), np.ones(3)])


def test_max_probability_is_blind_normal_probability_is_not():
    a, b = np.tile([.98, .01, .01], (100, 1)), np.tile([.01, .01, .98], (100, 1))
    d = lambda f, rows: distribution([f(p) for p in rows])
    assert psi(d(SCORES['max_probability'], a), d(SCORES['max_probability'], b)) == 0
    assert psi(d(SCORES['normal_probability'], a), d(SCORES['normal_probability'], b)) > 0.25


@pytest.mark.parametrize('bad', [[], [np.nan], [-0.1], [1.1]])
def test_distribution_rejects_invalid(bad):
    with pytest.raises(ValueError):
        distribution(bad)


def ref():
    return build_reference(np.tile([.9, .05, .05], (300, 1)), 'm' * 64, 's' * 64)


def row(t=1, **k):
    return {'probabilities': [.9, .05, .05], 'timestamp': t, 'model_sha256': 'm' * 64,
            'stats_sha256': 's' * 64, 'run_id': 'r1', 'truck_id': 'T001', **k}


def test_window_filters_identity_duplicates_and_fills():
    w = Window(ref(), 'r1')
    assert w.add(row()) and not w.add(row())
    for bad in (row(2, run_id='r2'), row(3, model_sha256='x'), {k: v for k, v in row(4).items() if k != 'stats_sha256'}):
        assert not w.add(bad)
    assert w.rejected == 3 and not w.add(row(5, probabilities=[.9, .9, .9]))
    for t in range(10, 109):
        w.add(row(t))
    values, n, _ = w.check()
    assert n == 100 and values['normal_probability'] < 0.05
    with pytest.raises(ValueError):
        build_reference(np.tile([.9, .05, .05], (299, 1)), 'm', 's')


EV = [{'event': 'mode_change', 'mode': m, 'epoch': e, 'run_id': 'r1', 'truck_id': 'T001'} for m, e in
      [('none', 0), ('combined', 1000), ('none', 1300)]]


def rows_psi(values):
    return [{'epoch': e, 'run_id': 'r1', 'truck_id': 'T001', 'model_sha256': 'm', 'stats_sha256': 's',
             'score': 'normal_probability', 'interval_s': 60, 'all_scores': {'normal_probability': v, 'max_probability': .01}}
            for e, v in values]


def test_psi_analysis_gates():
    good = rows_psi([(940, .02), (1120, .31), (1240, .9), (1600, .05)])
    r = analyse_psi(EV, good)
    assert r['e1_pass'] and r['scores']['normal_probability']['crossing_delay_s'] == 120
    assert not r['scores']['max_probability']['crossing_within_5_min']
    stale = rows_psi([(500, .02), (1120, .31), (1240, .9), (1600, .05)])
    assert not analyse_psi(EV, stale)['e1_pass']
    mixed = good[:1] + [dict(good[1], run_id='other')] + good[2:]
    with pytest.raises(ValueError):
        analyse_psi(EV, mixed)


def test_sla_uses_emitted_at_and_flags_early_alerts():
    log = ('[LOCAL ALERT] {"run_id":"r1","emitted_at":1042.5,"effective_class":2}\n'
           'noise\n[LOCAL ALERT] {"run_id":"r1","emitted_at":1060,"effective_class":1}\n')
    r = analyse_sla(1000.0, parse_alerts(log), 'r1')
    assert r['fault_to_alert_s'] == 42.5 and r['pass']
    early = analyse_sla(1000.0, parse_alerts(log + '[LOCAL ALERT] {"run_id":"r1","emitted_at":990,"effective_class":1}'), 'r1')
    assert early['alerts_before_injection'] == 1 and not early['pass']


def test_model_selection_gates():
    rows = [{'variant': v, 'accuracy_pct': a, 'critical_recall_pct': c, 'size_KB': s, 'p95_ms': '.1'}
            for v, a, c, s in [('M1', '95', '99', '9'), ('M2', '94', '97', '5'), ('M3', '93', '94', '4')]]
    assert choose(rows)['variant'] == 'M2'
    assert choose([dict(r, accuracy_pct='80') for r in rows]) is None
    with pytest.raises(ValueError):
        choose(rows[:2])


def test_ota_savings_requires_last_layer_only_change():
    m = lambda last: {'config': {'digest': 'c' + last, 'size': 2}, 'layers': [{'digest': 'base', 'size': 60_000_000}, {'digest': last, 'size': 3000}]}
    r = compare(m('old'), m('new'), 500)
    assert r['only_last_layer_changed'] and r['fleet_saved_MB'] == pytest.approx(5100.0, rel=1e-3)
    rev = m('new')
    rev['layers'].reverse()
    assert not compare(m('old'), rev, 500)['only_last_layer_changed']


def test_ansible_recap_and_exit_code(tmp_path):
    ok = 'PLAY RECAP ***\nlocalhost : ok=7 changed=0 unreachable=0 failed=0 skipped=1\n'
    assert recap_ok(ok, ['localhost']) and not recap_ok(ok, ['localhost', 'pi'])
    assert not recap_ok(ok.replace('changed=0', 'changed=1'), ['localhost'])
    assert run([sys.executable, '-c', 'print("x"); raise SystemExit(7)'], tmp_path / 'log') == 7

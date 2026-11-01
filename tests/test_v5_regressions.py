import math, time
import numpy as np
import pytest
from monitoring.drift_monitor import Window, build_reference
from scripts.select_model import choose
from submission.evidence_gate import checks
from scripts.analyse_run import transitions

def ref(): return build_reference(np.tile([.9,.05,.05],(300,1)), 'm','s')
def row(t): return dict(probabilities=[.9,.05,.05],timestamp=t,model_sha256='m',stats_sha256='s',run_id='r',truck_id='T001')
def test_stale_window():
    w=Window(ref(),'r')
    for i in range(100): assert w.add(row(i))
    assert w.check()[0] is not None
    w.last_arrival=time.monotonic()-121
    assert w.check()[0] is None

def test_out_of_order():
    w=Window(ref(),'r');assert w.add(row(10));assert not w.add(row(9));assert not w.add([])

def test_bad_reference():
    with pytest.raises(ValueError):build_reference(np.full((300,3),.9),'m','s')

def test_bad_latency():
    rows=[dict(variant=v,accuracy_pct=99,critical_recall_pct=99,size_KB=1,p95_ms=float('nan')) for v in ['M1','M2','M3']]
    with pytest.raises(ValueError):choose(rows)

def test_missing_evidence(tmp_path):
    problems = checks(tmp_path, 'r')
    for needle in ('analysis.json', 'ota_savings.json', 'model_selection.json', 'reference_dist.json',
                   'container_smoke.txt', 'phase1_report.pdf', 'final_report.pdf'):
        assert any(needle in p for p in problems), needle

def test_only_combined():
    events=[dict(event='mode_change',mode=m,epoch=i) for i,m in enumerate(['none','vibration','none','combined','none'])]
    assert transitions(events)==(3.,4.)

import json, time, hashlib
import numpy as np
import pytest
from data_pipeline.preprocessing import normalize, write_pipeline_contract, validate_pipeline_contract
from monitoring.drift_monitor import Window
from tests.test_v11_regressions import write_run
from submission.evidence_gate import checks

@pytest.mark.parametrize('bad', [np.nan, np.inf, -np.inf])
def test_clipping_does_not_hide_nonfinite(bad):
    with pytest.raises(ValueError):normalize(np.full(6,bad),np.stack([np.zeros(6),np.ones(6)]))

@pytest.mark.parametrize('bad', [-1., np.nan, np.inf, True])
def test_clip_config_validated(bad):
    with pytest.raises(ValueError):normalize(np.zeros(6),np.stack([np.zeros(6),np.ones(6)]),clip=bad)

def test_saturation_does_not_preserve_magnitude_or_shift():
    s=np.stack([np.zeros(6),np.ones(6)])
    np.testing.assert_equal(normalize(np.full(6,20),s),normalize(np.full(6,17),s))
    # z=11 becomes z=8 after shifted stats: the output DOES change.
    assert normalize(np.full(6,11),s)[0]==10
    assert normalize(np.full(6,11),np.stack([np.full(6,3),np.ones(6)]))[0]==8

def test_contract_detects_model_stats_and_pipeline_changes(tmp_path):
    model=tmp_path/'m.tflite';model.write_bytes(b'fixture-only')
    stats=tmp_path/'s.npy';np.save(stats,np.stack([np.zeros(6),np.ones(6)]))
    write_pipeline_contract(model,stats);validate_pipeline_contract(model,stats)
    model.write_bytes(b'changed')
    with pytest.raises(ValueError):validate_pipeline_contract(model,stats)
    write_pipeline_contract(model,stats)
    cpath=tmp_path/'m.tflite.pipeline.json';c=json.loads(cpath.read_text());c['pipeline_sha256']='old';cpath.write_text(json.dumps(c))
    with pytest.raises(ValueError):validate_pipeline_contract(model,stats)
    write_pipeline_contract(model,stats);np.save(stats,np.stack([np.ones(6),np.ones(6)]))
    with pytest.raises(ValueError):validate_pipeline_contract(model,stats)

def test_clock_injection_does_not_patch_process_time():
    original=time.monotonic
    from tests.test_v6_regressions import ref,row
    clock={'t':0};w=Window(ref(),'r',clock=lambda:clock['t'])
    for i in range(100):w.add(row(i))
    assert w.check()[0] is not None
    clock['t']=121;assert w.check()[0] is None
    assert time.monotonic is original

def test_sla_recomputed_not_trusted(tmp_path):
    write_run(tmp_path,True)
    assert not any('SLA does not match' in p for p in checks(tmp_path,'r'))
    (tmp_path/'evidence/r/container.log').write_text('[LOCAL ALERT] '+json.dumps({'run_id':'r','effective_class':2,'emitted_at':1100.})+'\n')
    assert any('SLA does not match' in p for p in checks(tmp_path,'r'))

def test_missing_container_log_fails(tmp_path):
    write_run(tmp_path,True);(tmp_path/'evidence/r/container.log').unlink()
    assert any('SLA raw logs' in p for p in checks(tmp_path,'r'))

def test_live_window_requires_pipeline_identity():
    from tests.test_v6_regressions import ref,row
    from data_pipeline.preprocessing import pipeline_sha256
    w=Window(ref(),'r',require_pipeline=True)
    assert not w.add(row(1))
    assert not w.add(dict(row(2),pipeline_sha256='old'))
    assert w.add(dict(row(3),pipeline_sha256=pipeline_sha256()))

def test_contract_in_final_docker_layer():
    from pathlib import Path
    r=Path(__file__).resolve().parents[1]
    lines=(r/'inference/Dockerfile').read_text().strip().splitlines()
    assert lines[-1]=='COPY inference/model.tflite inference/model.tflite.pipeline.json ./'

def test_sla_nonfinite_and_boolean_rejected():
    from scripts.analyse_run import analyse_sla
    for value in (True,float('nan'),float('inf')):
        with pytest.raises(ValueError):analyse_sla(1000,[{'run_id':'r','effective_class':2,'emitted_at':value}],'r')

def test_changed_psi_metrics_not_just_boolean_rejected(tmp_path):
    write_run(tmp_path,True)
    p=tmp_path/'evidence/r/analysis.json';d=json.loads(p.read_text())
    d['psi']['scores']['normal_probability']['crossing_delay_s']=1.0
    p.write_text(json.dumps(d))
    assert any('E1 result does not match' in x for x in checks(tmp_path,'r'))

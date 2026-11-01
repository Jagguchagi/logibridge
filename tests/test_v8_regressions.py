import json
import pytest
from submission.evidence_gate import checks
from submission.verify_submission import validate
from scripts.verify_bridge import parse
from tests.test_v7_regressions import block

@pytest.mark.parametrize('value', [{}, [], [1], None, True])
def test_malformed_evidence_does_not_crash(tmp_path, value):
    p=tmp_path/'evidence/r/analysis.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(value))
    assert any('analysis.json' in x for x in checks(tmp_path,'r'))
    missing, problems=validate(tmp_path,'r')
    assert missing and problems

def test_boolean_sla_time_rejected(tmp_path):
    p=tmp_path/'evidence/r/analysis.json';p.parent.mkdir(parents=True)
    p.write_text(json.dumps({'sla':{'pass':True,'fault_to_alert_s':True,'sla_s':90,'alerts_before_injection':0},'psi':{'run_id':'r','e1_pass':True,'interval_ok':True}}))
    assert 'Invalid SLA timing' in checks(tmp_path,'r')

def test_empty_video_is_invalid(tmp_path):
    p=tmp_path/'demo/demo_video_link.txt';p.parent.mkdir();p.write_text('')
    assert any('video link' in x for x in validate(tmp_path,'r')[1])

@pytest.mark.parametrize('name', ['a/./b.py','a//b.py','C:/bad.py','a\\b.py'])
def test_noncanonical_bridge_paths_rejected(name):
    with pytest.raises(ValueError,match='unsafe'):parse('h'+block(name,'x'))

def test_binary_inventory_paths_rejected():
    text='h'+block('a.py','x')+'\n## Binary inventory\nBINARY: ../evil.png | sha256='+'0'*64+'\n'
    with pytest.raises(ValueError,match='unsafe'):parse(text)

import pytest
from scripts.verify_bridge import parse
from tests.test_v9_regressions import new_block
from submission.evidence_gate import final_report

def test_trailing_content_rejected():
    t='h'+new_block('a.py','x')+'\n## Binary inventory\n## END OF BRIDGE: files=1 binaries=0\nGARBAGE'
    with pytest.raises(ValueError,match='after END'):parse(t)

def test_interblock_content_rejected():
    t='h'+new_block('a.py','x')+'GARBAGE\n'+new_block('b.py','y')+'\n## Binary inventory\n## END OF BRIDGE: files=2 binaries=0\n'
    with pytest.raises(ValueError,match='between'):parse(t)

def test_lowercase_placeholder_rejected(tmp_path):
    (tmp_path/'reports').mkdir();(tmp_path/'reports/groupno_LogiEdge_Final.pdf').write_bytes(b'%PDF-1.7')
    assert final_report(tmp_path) is None

def test_legacy_footer_not_framed_complete():
    from tests.test_v7_regressions import block
    t='h'+block('a.py','x')+'\n## Binary inventory\n## END OF BRIDGE: files=1 binaries=0\n'
    assert parse(t)[2] is False

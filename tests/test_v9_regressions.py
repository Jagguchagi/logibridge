"""v9 (Claude) regressions for gaps left in GPT v8."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts import make_snapshot
from scripts.verify_bridge import parse
from submission.evidence_gate import checks, final_report
from submission.verify_submission import validate

ROOT = Path(__file__).resolve().parents[1]


def new_block(name, body):
    return (f'\n## FILE: {name}\nSHA256: {hashlib.sha256(body.encode()).hexdigest()}\n'
            f'CHARS: {len(body)}\n````\n{body}\n````\n')


def test_fence_inside_file_round_trips():
    tricky = 'doc\n````\n## FILE: fake.py\nnot a real block\n````\nend'
    text = 'h' + new_block('docs/a.md', tricky) + new_block('b.py', 'x=1') + \
        '\n## Binary inventory\n## END OF BRIDGE: files=2 binaries=0\n'
    files, _, complete = parse(text)
    assert [f[0] for f in files] == ['docs/a.md', 'b.py'] and files[0][2] == tricky and complete


def test_dropped_block_detected_by_end_line():
    text = 'h' + new_block('a.py', 'x') + '\n## Binary inventory\n## END OF BRIDGE: files=2 binaries=0\n'
    with pytest.raises(ValueError, match='END line'):
        parse(text)


def test_truncated_block_detected():
    text = 'h' + new_block('a.py', 'abcdef')[:-12]
    with pytest.raises(ValueError):
        parse(text)


def test_snapshot_round_trip_on_real_repo(tmp_path):
    src = tmp_path / 'r'
    for rel in ('README.md', 'scripts/verify_bridge.py', 'evidence/validation_status.json'):
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text((ROOT / rel).read_text())
    (src / 'x.artifactvalidatepass').write_text('{"tool":"stray"}')
    make_snapshot.main(src)
    files, _, complete = parse((src / make_snapshot.OUT).read_text())
    names = {f[0] for f in files}
    assert complete and 'scripts/verify_bridge.py' in names and 'x.artifactvalidatepass' not in names


def test_repo_contains_no_tool_artifacts():
    stray = [p for p in ROOT.rglob('*') if p.name.endswith(('.artifactvalidatepass', '.orig.xlsx'))]
    assert not stray, stray


def test_smoke_must_match_current_deployed_model_hash(tmp_path):
    (tmp_path / 'inference').mkdir()
    (tmp_path / 'inference/model.tflite').write_bytes(b'new-model')
    (tmp_path / 'evidence').mkdir()
    old = hashlib.sha256(b'old-model').hexdigest()
    (tmp_path / 'evidence/container_smoke.txt').write_text(
        f'PASS /app/model.tflite sha256={old}\nPASS b\nPASS c\nPASS d\n')
    assert any('hash mismatch' in p for p in checks(tmp_path, 'r'))
    new = hashlib.sha256(b'new-model').hexdigest()
    (tmp_path / 'evidence/container_smoke.txt').write_text(
        f'PASS /app/model.tflite sha256={new}\nPASS b\nPASS c\nPASS d\n')
    assert not any('smoke' in p.lower() for p in checks(tmp_path, 'r'))


def test_brief_report_name_accepted_placeholder_rejected(tmp_path):
    (tmp_path / 'reports').mkdir()
    (tmp_path / 'reports/GROUPNO_LogiEdge_Final.pdf').write_bytes(b'%PDF-1.7')
    assert final_report(tmp_path) is None
    (tmp_path / 'reports/G12_LogiEdge_Final.pdf').write_bytes(b'%PDF-1.7')
    assert final_report(tmp_path).name == 'G12_LogiEdge_Final.pdf'


def test_validate_reports_each_problem_once(tmp_path):
    _, problems = validate(tmp_path, 'r')
    assert len(problems) == len(set(problems))


def test_readme_has_single_authority_section():
    s = (ROOT / 'README.md').read_text()
    assert s.count('authority') == 1 and 'v7 authority' not in s

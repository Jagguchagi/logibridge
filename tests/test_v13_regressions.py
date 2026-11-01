"""V13 (Claude, final desk release) regressions."""
from pathlib import Path

import numpy as np

import data_pipeline.preprocessing as pre
from scripts.package_scope import files as scoped_files
from scripts import make_snapshot

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_fingerprint_ignores_crlf(tmp_path, monkeypatch):
    lf = (ROOT / 'data_pipeline/preprocessing.py').read_bytes().replace(b'\r\n', b'\n')
    a, b = tmp_path / 'a.py', tmp_path / 'b.py'
    a.write_bytes(lf)
    b.write_bytes(lf.replace(b'\n', b'\r\n'))
    monkeypatch.setattr(pre, '__file__', str(a))
    h_lf = pre.pipeline_sha256()
    monkeypatch.setattr(pre, '__file__', str(b))
    assert pre.pipeline_sha256() == h_lf


def test_gitattributes_forces_lf_and_repo_has_no_crlf_scripts():
    ga = (ROOT / '.gitattributes').read_text()
    assert 'eol=lf' in ga and '*.png binary' in ga
    bad = [p for p in scoped_files(ROOT) if p.is_file() and p.suffix in ('.sh', '.py', '.yml', '.ini', '.conf')
           and '__pycache__' not in p.parts and b'\r' in p.read_bytes()]
    assert not bad, bad


def test_quality_check_tracks_current_bridge_name():
    s = (ROOT / 'scripts/quality_check.py').read_text()
    assert 'BRIDGE_NAME' in s and 'V12.txt' not in s
    import re   # the direction (GPT->Claude or Claude->GPT) flips at every handover; the version must not drift
    assert re.fullmatch(rf'BRIDGE_(GPT_CLAUDE|CLAUDE_GPT)_{make_snapshot.VERSION.upper()}\.txt', make_snapshot.OUT)


def test_clip_threshold_in_physical_units_is_documented():
    """temperature_mean saturates ~0.4 C above the clean mean; the disclosure must say so."""
    s = np.load(ROOT / 'data_pipeline/training_stats.npy')
    sat = float(s[0][0] + pre.CLIP_Z * s[1][0])
    assert 4.2 < sat < 4.6
    assert '4.4' in (ROOT / 'docs/DISCLOSURES.md').read_text()


def test_single_start_here_and_readme_authority():
    assert (ROOT / 'START_HERE.md').is_file()
    readme = (ROOT / 'README.md').read_text()
    assert readme.count('authority') == 1 and 'START_HERE.md' in readme

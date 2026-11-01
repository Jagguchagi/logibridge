import base64
import hashlib
import json
from pathlib import Path
import pytest
from scripts import make_snapshot
from scripts.package_scope import files
from scripts.verify_bridge import restore


def fixture_root(tmp_path):
    root=tmp_path/'src';(root/'evidence').mkdir(parents=True)
    (root/'evidence/validation_status.json').write_text('{}')
    (root/'README.md').write_text('fixture source')
    return root


def test_snapshot_excludes_dependencies_secrets_state_and_git(tmp_path):
    root=fixture_root(tmp_path)
    for name in ['.venv/secret.txt','.git/config','state/alerts.sqlite','.env','backend_alerts.sqlite','venv/lib/x.py']:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('DO_NOT_EXPORT_FIXTURE')
    make_snapshot.main(root)
    text=(root/make_snapshot.OUT).read_text()
    assert 'DO_NOT_EXPORT_FIXTURE' not in text
    assert '## FILE: README.md' in text


def test_bridge_restores_binary_without_zip_or_regeneration(tmp_path):
    root=fixture_root(tmp_path);(root/'assets').mkdir()
    raw=b'\x89PNG\r\n\x1a\n\xff\x00fixture'
    (root/'assets/test.png').write_bytes(raw)
    make_snapshot.main(root)
    dest=tmp_path/'restored'
    _,b,complete=restore(root/make_snapshot.OUT,dest)
    assert complete and b
    assert (dest/'assets/test.png').read_bytes()==raw
    assert (dest/make_snapshot.OUT).read_bytes()==(root/make_snapshot.OUT).read_bytes()


def test_embedded_asset_tampering_fails(tmp_path):
    root=fixture_root(tmp_path);(root/'a.bin').write_bytes(b'\xffbinary')
    make_snapshot.main(root)
    text=(root/make_snapshot.OUT).read_text()
    encoded=base64.b64encode(b'\xffbinary').decode()
    (root/make_snapshot.OUT).write_text(text.replace(encoded,'A'*len(encoded)))
    with pytest.raises(ValueError,match='hash mismatch'):
        restore(root/make_snapshot.OUT,tmp_path/'bad')


def test_scope_does_not_follow_symlinks(tmp_path):
    root=fixture_root(tmp_path)
    outside=tmp_path/'outside.txt';outside.write_text('SECRET_FIXTURE')
    (root/'link.txt').symlink_to(outside)
    assert all(p.name!='link.txt' for p in files(root))


def test_working_check_explicitly_does_not_certify_release():
    root=Path(__file__).resolve().parents[1]
    s=(root/'scripts/quality_check.py').read_text()
    assert '--working' in s and 'original-release integrity NOT checked' in s
    assert 'scoped_files(root)' in s

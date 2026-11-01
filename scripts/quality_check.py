"""Local release check. Does not establish live deployment or submission readiness.
Run from repository root: python -m scripts.quality_check
"""
import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from scripts.verify_bridge import parse, read_exact
from scripts.package_scope import files as scoped_files
from scripts.make_snapshot import OUT as BRIDGE_NAME

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--working', action='store_true', help='Tests/syntax/LF checks only; does not certify original release bytes')
    args = ap.parse_args()
    root = Path.cwd()
    for p in scoped_files(root):
        if p.suffix == '.py':
            ast.parse(p.read_text(), filename=str(p))
    result = subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q', '-p', 'no:cacheprovider', '--color=no'])
    if result.returncode:
        raise SystemExit(result.returncode)
    crlf = [str(p.relative_to(root)) for p in scoped_files(root) if p.suffix in ('.sh', '.py', '.yml', '.ini', '.conf') and b'\r' in p.read_bytes()]
    if crlf:
        raise SystemExit(f'CRLF execution files: {crlf[:5]}')
    if args.working:
        print('WORKING CHECK PASSED: syntax/tests/LF only; original-release integrity NOT checked')
        return
    bridges = sorted(p.name for p in root.glob('BRIDGE_*.txt'))
    stale = [b for b in bridges if b != BRIDGE_NAME]
    if stale:
        raise SystemExit(f'Stale bridge files present: {stale}; current is {BRIDGE_NAME}')
    if not bridges:
        print(f'Note: no bridge file shipped in this folder (that is fine); python -m scripts.make_snapshot creates {BRIDGE_NAME}.')
    else:
        files, binaries, complete = parse(read_exact(root / BRIDGE_NAME))   # newline=''; text mode would corrupt CRLF files
        if not complete:
            raise SystemExit('Bridge framing incomplete')
        for name, digest, body in files:
            if (root/name).read_bytes().decode('utf-8') != body or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
                raise SystemExit('Stale bridge source: '+name)
        for name, digest in binaries:
            if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
                raise SystemExit('Missing/changed binary: '+name)
    crlf = [p.as_posix() for p in scoped_files(root) if p.is_file() and p.suffix in ('.sh', '.py', '.yml', '.ini', '.conf') and b'\r' in p.read_bytes()]
    if crlf:
        raise SystemExit(f'Windows line endings would break Linux/Docker execution: {crlf[:5]}')
    manifest = root/'MANIFEST_SHA256.json'
    if manifest.is_file():
        for name, digest in json.loads(manifest.read_text()).items():
            if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
                raise SystemExit('Manifest mismatch: '+name)
    print('LOCAL QUALITY CHECK PASSED. Training, runtime, hardware and authored submission still require separate evidence.')

if __name__ == '__main__':
    main()

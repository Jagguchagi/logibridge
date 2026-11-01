"""Restore a bridge text file into a NEW folder and verify it.

Format v9 (written by scripts/make_snapshot.py):
    ## FILE: <path>
    SHA256: <hex>
    CHARS: <len(body)>
    ````
    <body>
    ````
    ...
    ## Binary inventory ...
    BINARY: <path> | sha256=<hex> | bytes=<n>
    ## END OF BRIDGE: files=<N> binaries=<M>

Bodies are read by declared length, so a body that itself contains a ```` fence cannot cut a block
short, and the END line proves no block was dropped or truncated. Older bridges (no CHARS / END)
are still read with the legacy regex, but flagged as unverifiable for completeness.
Checks: per-file SHA-256, safe canonical unique paths (text and binary), counts.
Usage: python -m scripts.verify_bridge BRIDGE.txt restored_dir [--regenerate]
NOTE: --regenerate executes restored Python modules; inspect the source first."""
import argparse
import base64
import json
import hashlib
import re
import subprocess
import sys
import shutil
from pathlib import Path, PurePosixPath

FENCE = '````'
HEAD = re.compile(r'## FILE: (.+)\nSHA256: ([a-f0-9]{64})\nCHARS: (\d+)\n' + FENCE + r'\n')
LEGACY = re.compile(r'\n## FILE: (.*?)\nSHA256: ([a-f0-9]{64})\n````\n(.*?)\n````\n', re.S)
BINARY = re.compile(r'^BINARY: (\S+) \| sha256=([a-f0-9]{64})', re.M)
END = re.compile(r'^## END OF BRIDGE: files=(\d+) binaries=(\d+)\s*$', re.M)


def _check_path(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or str(p) != name or '\\' in name or ':' in name:
        raise ValueError(f'unsafe path {name}')


def parse(text):
    """Return (files, binaries, complete). files = [(name, digest, body)]."""
    files, pos, complete = [], 0, False
    if HEAD.search(text):
        while (m := HEAD.search(text, pos)):
            name, digest, n = m[1], m[2], int(m[3])
            start = m.end()
            body = text[start:start + n]
            tail = text[start + n:start + n + len(FENCE) + 2]
            if len(body) != n or tail != '\n' + FENCE + '\n':
                raise ValueError(f'truncated or malformed block: {name}')
            if files and text[pos:m.start()].strip():
                raise ValueError('unexpected content between file blocks')
            files.append((name, digest, body))
            pos = start + n + len(FENCE) + 2
        inv = text[pos:]
    else:
        files = LEGACY.findall(text)
        inv = text.split('## Binary inventory', 1)[-1] if '## Binary inventory' in text else ''
    if not files:
        raise ValueError('no FILE blocks found')
    binaries = BINARY.findall(inv)
    end = END.search(inv)
    if HEAD.search(text):
        if end and inv[end.end():].strip():
            raise ValueError('unexpected content after END line')
        for line in (inv[:end.start()] if end else inv).splitlines():
            s = line.strip()
            if s and not (s.startswith('## Binary inventory') or BINARY.match(s) or END.match(s)):
                raise ValueError(f'unrecognised line in binary inventory: {s[:60]}')
    if end:
        if inv[end.end():].strip():
            raise ValueError('unexpected content after END line')
        if (int(end[1]), int(end[2])) != (len(files), len(binaries)):
            raise ValueError(f'END line declares files={end[1]} binaries={end[2]}, found {len(files)}/{len(binaries)}')
        complete = bool(HEAD.search(text))  # legacy regex cannot establish framed completeness
    names = [n for n, _, _ in files] + [n for n, _ in binaries]
    for name in names:
        _check_path(name)
        if any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise ValueError(f'unsafe path {name!r}')
    if len(set(names)) != len(names):
        raise ValueError('duplicate file paths in bridge')
    for name, digest, body in files:
        if hashlib.sha256(body.encode('utf-8')).hexdigest() != digest:
            raise ValueError(f'hash mismatch: {name}')
    return files, binaries, complete


def read_exact(path):
    """Read a bridge WITHOUT newline translation. Text mode would turn \\r\\n into \\n, so the CHARS count of a CRLF
    file (for example the benchmark CSV, which Python's csv module writes with \\r\\n) would no longer match."""
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def restore(bridge, dest):
    dest = Path(dest)
    if dest.exists():
        raise SystemExit(f'{dest} exists; choose a new folder')
    files, binaries, complete = parse(read_exact(bridge))
    for name, _, body in files:
        out = dest / name
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='') as f:   # keep \r\n files byte-identical
            f.write(body)
    index = dest / '.bridge_assets/index.json'
    if index.is_file():
        entries = json.loads(index.read_text(encoding='utf-8'))
        if not isinstance(entries, list):
            raise ValueError('invalid embedded asset index')
        expected = dict(binaries)
        restored = set()
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError('invalid asset entry')
            name, encoded = item['path'], item['encoded']
            _check_path(name); _check_path(encoded)
            if name in restored or name not in expected or not encoded.startswith('.bridge_assets/'):
                raise ValueError('unexpected or duplicate embedded asset')
            if item.get('sha256') != expected[name] or type(item.get('bytes')) is not int or not 0 <= item['bytes'] <= 100_000_000:
                raise ValueError('invalid embedded asset metadata')
            raw = base64.b64decode((dest / encoded).read_bytes(), validate=True)
            if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != expected[name]:
                raise ValueError('embedded binary hash/length mismatch')
            out = dest / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(raw)
            restored.add(name)
        if restored != set(expected):
            raise ValueError('embedded binary inventory incomplete')
    bridge_name = Path(bridge).name
    _check_path(bridge_name)
    if bridge_name in {n for n, _, _ in files} or bridge_name in dict(binaries):
        raise ValueError('bridge filename collides with restored inventory')
    shutil.copyfile(bridge, dest / bridge_name)
    return files, binaries, complete


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bridge')
    ap.add_argument('dest')
    ap.add_argument('--regenerate', action='store_true')
    a = ap.parse_args()
    files, binaries, complete = restore(a.bridge, a.dest)
    print(f'{len(files)} text files restored and hash-verified; '
          f"{'END line matched (no blocks missing)' if complete else 'LEGACY bridge: completeness NOT verifiable'}")
    if a.regenerate:
        subprocess.run([sys.executable, '-m', 'training.generate_dataset'], cwd=a.dest, check=True, capture_output=True)
        subprocess.run([sys.executable, '-m', 'scripts.build_tracker'], cwd=a.dest, check=True)
    failed = not complete
    for name, digest in binaries:
        p = Path(a.dest) / name
        if not p.exists():
            print(f'MISSING binary (copy from the ZIP): {name}')
            failed = True
        elif name == 'submission/LogiBridge_Tracker.xlsx' and a.regenerate:
            print(f'REGENERATED {name} (xlsx bytes differ by timestamp; content from scripts/build_tracker.py)')
        else:
            ok = hashlib.sha256(p.read_bytes()).hexdigest() == digest
            print(f"{'MATCH' if ok else 'DIFFERS'} {name}")
            failed = failed or not ok
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

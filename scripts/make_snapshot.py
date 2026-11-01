"""Write the cross-assistant bridge: a handover header (state read from evidence/validation_status.json,
state may be stale unless tests were rerun), then every text file verbatim with its SHA-256, then the binary inventory.
Check the result with: python -m scripts.verify_bridge <bridge> <new_dir>"""
import base64
import hashlib
import json
from pathlib import Path
from scripts.package_scope import files as scoped_files

VERSION = 'v15'
OUT = f'BRIDGE_CLAUDE_GPT_{VERSION.upper()}.txt'
SKIP_PREFIX = ('BRIDGE_',)
SKIP = {'MANIFEST_SHA256.json', 'NEXT_CHAT_SOURCE.md'}
SKIP_SUFFIX = ('.artifactvalidatepass', '.orig.xlsx', '.pyc')

PROTOCOL = '''## Protocol for the next exchange (either assistant)
1. Restore with `python -m scripts.verify_bridge <this file> <new_dir>`: every block is hash-checked and the binary files are embedded, so no ZIP and no `--regenerate` are needed (`--regenerate` executes restored code; inspect the source first).
2. Start from this version; do not rebuild a smaller package from memory.
3. Report changes as a table: file | problem | fix | test that proves it.
4. Never add trained models, metrics, logs, reports or video that were not actually produced.
5. Keep "not adopted" and "open items" lists in docs/JOINT_REVIEW_<version>.md; carry open items forward.
6. Regenerate this bridge with `python -m scripts.make_snapshot` and run verify_bridge on it before sharing.
'''

REQUESTS = """## Handover to GPT (V15)
- Read docs/HANDOVER_TO_GPT.md first (one page), then docs/JOINT_REVIEW_V15.md. Preserve accepted fixes.
- V15 is the first version run on real TensorFlow, a real MQTT broker and the real services together.
  Reopen only for a reproduced defect (a failing test or a log) or real output from the user's machine.
- Bridge includes hash-checked base64 assets: restore does not need another ZIP or regeneration.
- Inspect code before execution. Checksums establish consistency, not authenticity.
- Real models, measured deployment evidence, authored reports and video remain the user's to produce.
"""


def main(root='.'):
    r = Path(root)
    # Include reversible base64 assets as ordinary hash-checked text blocks.
    # This makes the bridge independently restorable without executing regeneration.
    asset_dir = r / '.bridge_assets'
    asset_dir.mkdir(exist_ok=True)
    for old in asset_dir.glob('*.b64'):
        old.unlink()
    assets = []
    for p in scoped_files(r):
        if '.bridge_assets' in p.relative_to(r).parts:
            continue
        raw = p.read_bytes()
        try:
            raw.decode('utf-8')
        except UnicodeDecodeError:
            name = p.relative_to(r).as_posix()
            digest = hashlib.sha256(raw).hexdigest()
            encoded_name = digest + '.b64'
            (asset_dir / encoded_name).write_text(base64.b64encode(raw).decode('ascii'), encoding='ascii')
            assets.append({'path': name, 'sha256': digest, 'bytes': len(raw), 'encoded': '.bridge_assets/' + encoded_name})
    (asset_dir / 'index.json').write_text(json.dumps(assets, indent=2), encoding='utf-8')
    status = json.loads((r / 'evidence/validation_status.json').read_text())
    state = '## State at handover (from evidence/validation_status.json)\n' + \
        '\n'.join(f'- {k}: {v}' for k, v in status.items()) + '\n'
    parts = [f'# BRIDGE CLAUDE -> GPT, {VERSION}\nRead: (1) this header, (2) docs/JOINT_REVIEW_V15.md, (3) the source.\n\n',
             PROTOCOL, '\n', state, '\n', REQUESTS]
    binaries, nfiles = [], 0
    for p in scoped_files(r):
        if (not p.is_file() or p.name in SKIP or p.name.startswith(SKIP_PREFIX) or p.name.endswith(SKIP_SUFFIX)
                or '__pycache__' in p.parts or '.pytest_cache' in p.parts):
            continue
        raw = p.read_bytes()
        name, digest = p.relative_to(r).as_posix(), hashlib.sha256(raw).hexdigest()
        try:
            body = raw.decode('utf-8')
        except UnicodeDecodeError:
            binaries.append(f'BINARY: {name} | sha256={digest} | bytes={len(raw)}')
            continue
        parts.append(f'\n## FILE: {name}\nSHA256: {digest}\nCHARS: {len(body)}\n````\n{body}\n````\n')
        nfiles += 1
    parts.append('\n## Binary inventory (embedded in .bridge_assets; ZIP also contains original bytes)\n' + '\n'.join(binaries) + '\n')
    parts.append(f'## END OF BRIDGE: files={nfiles} binaries={len(binaries)}\n')
    (r / OUT).write_text(''.join(parts), encoding='utf-8')
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()

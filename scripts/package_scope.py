"""Files eligible for source handover. Runtime state and installed dependencies are excluded."""
from pathlib import Path
EXCLUDED_DIRS = {'.venv', 'venv', '.git', '__pycache__', '.pytest_cache', 'state', 'node_modules'}
EXCLUDED_SUFFIXES = ('.pyc', '.artifactvalidatepass', '.orig.xlsx', '.sqlite', '.sqlite3', '.sqlite-wal', '.sqlite-shm')
def eligible(path, root):
    rel = Path(path).relative_to(root)
    return (not path.is_symlink() and not any(part in EXCLUDED_DIRS for part in rel.parts)
            and path.name != '.env' and not path.name.startswith('.env.')
            and not path.name.endswith(EXCLUDED_SUFFIXES))
def files(root):
    root = Path(root)
    return [p for p in sorted(root.rglob('*')) if p.is_file() and eligible(p, root)]

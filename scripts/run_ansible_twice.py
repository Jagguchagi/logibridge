"""E2: run the playbook twice and check that run 2 shows changed=0, failed=0, unreachable=0 for
every expected host. Logs: evidence/ansible_run1.txt, ansible_run2.txt, ansible_check.json.
Usage: python -m scripts.run_ansible_twice --expected-host localhost [-- -K -e run_id=demo02]"""
import argparse
import json
import re
import sys
from pathlib import Path

from scripts.run_logged import run


def recap_ok(text, expected):
    if 'PLAY RECAP' not in text:
        return False
    found = {}
    for line in text.rsplit('PLAY RECAP', 1)[1].splitlines():
        m = re.match(r'^\s*(\S+)\s*:\s*(.*)$', line)
        if m:
            found[m[1]] = dict(re.findall(r'(\w+)=(\d+)', m[2]))
    return set(found) == set(expected) and all(
        found[h].get(k) == '0' for h in expected for k in ('changed', 'failed', 'unreachable'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--expected-host', action='append', required=True)
    p.add_argument('extra', nargs=argparse.REMAINDER)
    a = p.parse_args()
    extra = a.extra[1:] if a.extra[:1] == ['--'] else a.extra
    cmd = ['ansible-playbook', '-i', 'deployment/inventory.ini', 'deployment/logibridge_deploy.yml', *extra]
    for i in (1, 2):
        code = run(cmd, f'evidence/ansible_run{i}.txt')
        if code:
            sys.exit(code)
    ok = recap_ok(Path('evidence/ansible_run2.txt').read_text(), a.expected_host)
    Path('evidence/ansible_check.json').write_text(json.dumps({'run2_changed_zero': ok, 'hosts': a.expected_host}, indent=2))
    print('PASS: run 2 changed=0' if ok else 'FAIL: run 2 not changed=0 (rerun with --diff -v to find the task)')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

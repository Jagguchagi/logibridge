"""Check the environment; prints every check (does not stop at the first failure)."""
import importlib
import shutil
import subprocess
import sys


def check(name, ok, fix):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ('' if ok else f'  -> {fix}'))
    return ok


def main():
    results = [check('Python 3.11', sys.version_info[:2] == (3, 11), 'python3.11 -m venv .venv')]
    for mod in ['numpy', 'sklearn', 'yaml', 'tensorflow', 'tensorflow_model_optimization', 'paho.mqtt.client', 'psutil', 'requests']:
        try:
            importlib.import_module(mod)
            ok = True
        except ImportError:
            ok = False
        results.append(check(f'import {mod}', ok, 'pip install -r requirements.txt'))
    for tool in ['docker', 'ansible-playbook']:
        results.append(check(f'{tool} on PATH', shutil.which(tool) is not None, f'install {tool}'))
    if shutil.which('sudo'):
        r = subprocess.run(['sudo', '-n', '/usr/bin/python3', '-c', 'import requests'], capture_output=True)
        results.append(check('requests importable by sudo /usr/bin/python3 (Ansible docker modules)', r.returncode == 0,
                             'sudo apt install python3-requests (run `sudo -v` first if prompted)'))
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()

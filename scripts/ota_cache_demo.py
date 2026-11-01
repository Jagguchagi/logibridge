"""D2 OTA layer-cache demo: build, change ONLY the model and its contract in the same final layer, rebuild; logs show every step before the
final COPY as CACHED. Restores the original model afterwards, even on failure."""
import sys
from pathlib import Path

from scripts.run_logged import run


def main():
    model = Path('inference/model.tflite')
    original = model.read_bytes()
    contract = Path(str(model) + '.pipeline.json')
    original_contract = contract.read_bytes()
    other = [f for f in sorted(Path('training/models').glob('*.tflite')) if f.read_bytes() != original]
    if not other:
        sys.exit('need a second, different .tflite in training/models')
    try:
        for tag in ('cache-v1', 'cache-v2'):
            if tag == 'cache-v2':
                model.write_bytes(other[0].read_bytes())
                contract.write_bytes(Path(str(other[0]) + '.pipeline.json').read_bytes())
            cmd = ['docker', 'build', '--progress=plain', '-f', 'inference/Dockerfile',
                   '-t', f'localhost:5000/logibridge:{tag}', '.']
            if run(cmd, f'evidence/docker_build_{tag}.txt'):
                sys.exit(f'build {tag} failed')
    finally:
        model.write_bytes(original)
        contract.write_bytes(original_contract)
    cached = Path('evidence/docker_build_cache-v2.txt').read_text().count('CACHED')
    print(f'\nrebuild finished; {cached} CACHED steps. Push both tags, then run scripts.ota_savings.')


if __name__ == '__main__':
    main()

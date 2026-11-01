"""Checks that generated artifacts exist and measured gates pass. It cannot judge authorship,
video content, repository permissions or marks.  Usage: python -m submission.verify_submission --run-id <run>"""
import argparse
import csv
import json
import sys
from data_pipeline.simulator import safe_run_id
from submission.evidence_gate import checks
from pathlib import Path

REQUIRED = ['training/models/M1_fp32.tflite', 'training/models/M2_int8.tflite', 'training/models/M3_pruned_int8.tflite',
            'inference/model.tflite', 'inference/model.tflite.pipeline.json', 'monitoring/reference_dist.json', 'optimisation/results/benchmark_results.csv',
            'optimisation/results/pareto_chart.png', 'evidence/container_smoke.txt', 'evidence/ansible_check.json',
            'evidence/ota_savings.json', 'reports/phase1_report.pdf', 'reports/phase2_report.pdf']


def validate(root, run_id):
    """Return all missing/malformed evidence instead of crashing on the first file."""
    from scripts.select_model import choose
    from urllib.parse import urlparse
    r = Path(root)
    safe_run_id(run_id)
    missing = [f for f in REQUIRED + [f'evidence/{run_id}/analysis.json'] if not (r/f).is_file()]
    problems = checks(r, run_id)
    def load(name):
        try:
            d = json.loads((r/name).read_text())
            if not isinstance(d, dict) or not d:
                raise ValueError('expected nonempty object')
            return d
        except (OSError, ValueError):
            problems.append('Missing or invalid evidence: ' + name)
            return None
    benchmark = r/'optimisation/results/benchmark_results.csv'
    if benchmark.exists():
        try:
            with benchmark.open() as f:
                rows = list(csv.DictReader(f))
            from data_pipeline.preprocessing import pipeline_sha256, validate_pipeline_contract
            import hashlib
            meta = load('optimisation/results/benchmark_metadata.json')
            if meta is not None:
                for k, file in [('dataset_sha256','training/data/dataset.npz'),('stats_sha256','data_pipeline/training_stats.npy')]:
                    if not (r/file).is_file() or meta.get(k) != hashlib.sha256((r/file).read_bytes()).hexdigest():
                        problems.append('Stale benchmark metadata: '+k)
                if meta.get('pipeline_sha256') != pipeline_sha256():
                    problems.append('Stale benchmark preprocessing fingerprint')
            from optimisation.benchmark import FILES
            for row in rows:
                model = r/'training/models'/FILES[row['variant']]
                validate_pipeline_contract(model, r/'data_pipeline/training_stats.npy')
                if row.get('model_sha256') != hashlib.sha256(model.read_bytes()).hexdigest():
                    problems.append('Stale benchmark model: '+row['variant'])
            best = choose(rows)
            if best is None:
                problems.append('no variant passes accuracy > 88% and Critical recall > 95%')
            selection = load('evidence/model_selection.json')
            if best is not None and selection is not None:
                if selection.get('variant') != best['variant'] or any(str(selection.get(k)) != str(best.get(k)) for k in best):
                    problems.append('Selection does not match current benchmark recommendation')
        except (OSError, ValueError, KeyError, TypeError):
            problems.append('Invalid benchmark evidence')
    ans = load('evidence/ansible_check.json')
    if ans is not None and ans.get('run2_changed_zero') is not True:
        problems.append('Ansible run 2 was not changed=0')
    try:
        text = (r/'demo/demo_video_link.txt').read_text().strip()
        url = urlparse(text)
        if url.scheme not in ('https', 'http') or not url.hostname or any(c.isspace() for c in text):
            raise ValueError('expected one HTTP(S) URL')
    except (OSError, ValueError):
        problems.append('demo video link missing or invalid (access/content still require manual review)')
    return missing, list(dict.fromkeys(problems))  # same file may be reported by both gates

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    a = p.parse_args()
    missing, problems = validate('.', a.run_id)
    for line in ['MISSING  ' + m for m in missing] + ['PROBLEM  ' + x for x in problems] or ['All automated checks pass.']:
        print(line)
    print('Manual: own report/video, instructor collaborator accepted, link works in incognito, 3 LMS items, deadline.')
    sys.exit(1 if missing or problems else 0)

if __name__ == '__main__':
    main()

"""Build reports/results_appendix.md from YOUR evidence files. Never invents numbers: anything
missing is shown as NOT YET MEASURED. Paste the tables into your report; the analysis is yours.
Usage: python -m reports.build_results_appendix [--run-id <run>]"""
import argparse
import csv
import json
from pathlib import Path

MISSING = 'NOT YET MEASURED'


def load(path):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def table(rows):
    if not rows:
        return MISSING + '\n'
    spec = [('Mean latency (ms)', 'mean_ms', 3), ('p95 latency (ms)', 'p95_ms', 3), ('Model size (KB)', 'size_KB', 2),
            ('Validation accuracy (%)', 'accuracy_pct', 2), ('Energy / inference (mJ, est.)', 'energy_estimate_mJ', 4),
            ('Critical recall (%)', 'critical_recall_pct', 2), ('Accuracy, stats +3 sigma (%)', 'shifted_stats_accuracy_pct', 2)]
    out = '| Metric | ' + ' | '.join(r['variant'] for r in rows) + ' |\n|---|' + '---:|' * len(rows) + '\n'
    for name, key, nd in spec:
        out += f'| {name} | ' + ' | '.join(f'{float(r[key]):.{nd}f}' for r in rows) + ' |\n'
    return out


def build(root='.', run_id=None):
    r = Path(root)
    b = r / 'optimisation/results/benchmark_results.csv'
    rows = list(csv.DictReader(b.open())) if b.exists() else []
    train = load(r / 'optimisation/results/training_metrics.json')
    prune = load(r / 'optimisation/results/pruning.json')
    sel = load(r / 'evidence/model_selection.json')
    ota = load(r / 'evidence/ota_savings.json')
    ans = load(r / 'evidence/ansible_check.json')
    an = load(r / f'evidence/{run_id}/analysis.json') if run_id else None
    t = ['# Results appendix (generated from measured evidence only)\n\n## D1 training\n']
    t.append(f"Validation accuracy: {train['accuracy'] * 100:.2f}%. Confusion matrix (rows true N/W/C): {train['confusion_matrix']}\n"
             if train else f'{MISSING}\n')
    t.append('\n## F2 benchmark (15 required cells + Critical recall + C2 shifted-stats experiment)\n' + table(rows))
    t.append('\n## F1 pruning\n' + (f"Method {prune['method_used']}; widths 32/16 -> {prune['compact_widths']}; removed "
             f"{prune['removed_fraction_per_layer'][0]:.1%} / {prune['removed_fraction_per_layer'][1]:.1%}\n" if prune else MISSING + '\n'))
    t.append('\n## F3 selected model\n' + (f"{sel['variant']}\n" if sel else MISSING + '\n'))
    if an:
        p = an['psi']
        t.append(f"\n## E1 PSI (run {p['run_id']}, selected score {p['selected_score']})\n"
                 '| Score | Baseline | Crossing delay (s) | Peak | Recovery delay (s) |\n|---|---:|---:|---:|---:|\n')
        for k, v in p['scores'].items():
            t.append(f"| {k} | {v['baseline_psi']} | {v['crossing_delay_s']} | {v['peak_psi']} | {v['recovery_delay_s']} |\n")
        if 'sla' in an:
            t.append(f"\n## SLA\nFault to first local alert: {an['sla']['fault_to_alert_s']} s (target 90 s)\n")
    else:
        t.append(f'\n## E1 PSI / SLA\n{MISSING}\n')
    t.append('\n## D2 OTA saving\n' + (f"Full {ota['full_image_bytes']} B vs incremental {ota['incremental_bytes']} B; 85 trucks save "
             f"{ota['fleet_saved_MB']} MB (INR {ota['fleet_saved_INR']}) per update\n" if ota else MISSING + '\n'))
    t.append('\n## E2 Ansible\n' + (f"Run 2 changed=0: {ans['run2_changed_zero']}\n" if ans else MISSING + '\n'))
    text = ''.join(t)
    (r / 'reports').mkdir(exist_ok=True)
    (r / 'reports/results_appendix.md').write_text(text)
    return text


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id')
    print(build(run_id=ap.parse_args().run_id))

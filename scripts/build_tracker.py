"""Regenerate submission/LogiBridge_Tracker.xlsx from source, so the bridge text can rebuild it
(the workbook content is defined here; byte hashes differ per run because xlsx stores timestamps)."""
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

F = 'Arial'
HEAD = PatternFill('solid', start_color='065A82')
THIN = Side(style='thin', color='BFC9D1')
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CRITERIA = [
    ('A1', 'Constraint analysis 350-500 words, 4 constraints with numbers', 'scenario_architecture/constraint_analysis.md', 'Your own text, report §1'),
    ('A2', 'Architecture diagram with all components', 'scenario_architecture/system_architecture.png', 'Figure in report'),
    ('B1', 'Constraint Triangle, 3 options, 90 s / 10 W / 85 & 265 costs', 'hardware/hardware_justification.md', 'Report §1'),
    ('B2', 'Arithmetic intensity 2.5, ridge 1.33, compute-bound, optimisation', 'hardware/hardware_justification.md', 'Report §1'),
    ('C1', 'Simulator 3 streams, 4 modes, local Mosquitto', 'data_pipeline/simulator.py', 'mosquitto_sub capture; video'),
    ('C2', 'Filter, 30 s/10 s windows, 6 features, frozen stats', 'data_pipeline/preprocessing.py', 'Tests pass'),
    ('C2', 'Correct vs +3 sigma stats accuracy', 'optimisation/benchmark.py', 'shifted_stats column; report §2'),
    ('C3', 'Feature-level fusion justified', 'data_pipeline/mqtt_architecture.md', 'Report §2'),
    ('C4', 'Topic tree figure and QoS per topic', 'data_pipeline/mqtt_architecture.md', 'Figure, report §2'),
    ('D1', 'Dataset 20/15/15 min; MLP 32-16; accuracy > 88%', 'training/', 'training_metrics.json'),
    ('D2', 'python:3.11-slim, pip before model, MODEL_PATH, inference topic', 'inference/Dockerfile', 'container_smoke.txt incl. /app/model.tflite; video'),
    ('D2', 'Layer-cache demo and 85-truck saving', 'scripts/ota_cache_demo.py, ota_savings.py', 'build logs, ota_savings.json'),
    ('D3', '10 Module-4 stages (exact course names)', 'reports/pipeline_mapping.md', 'Report §3'),
    ('E1', 'Reference: 300 windows, 4 bins', 'monitoring/drift_monitor.py --reference', 'reference_dist.json (hash = deployed model)'),
    ('E1', 'PSI every 60 s on last 100; exact alert text', 'monitoring/drift_monitor.py', 'psi_live.jsonl rows with interval_s = 60'),
    ('E1', 'Combined injection crosses 0.25 within 5 min; recovery < 0.10', 'scripts/analyse_run.py', 'analysis.json e1_pass = true; video'),
    ('E2', 'Exactly 7 tasks; run 2 changed=0; both on video', 'scripts/run_ansible_twice.py', 'ansible_check.json'),
    ('E3', 'Full/canary/shadow costs and recommendation', 'deployment/ota_strategy.md', 'Report §3'),
    ('F1', 'M1 FP32, M2 full INT8 (>=200 calib), M3 pruned + INT8', 'training/', '3 .tflite; pruning.json zero_columns [11, 6], widths [21, 10], method named in report'),
    ('F2', '5 metrics x 3 variants, 10 warm-up + 200 runs, Pareto', 'optimisation/benchmark.py', 'CSV + pareto_chart.png'),
    ('F3', '90 s budget, memory, Critical recall > 95%', 'scripts/select_model.py', 'model_selection.json; report §4'),
    ('SLA', 'Fault-to-first-local-alert <= 90 s, no pre-injection alerts', 'scripts/analyse_run.py --container-log', 'analysis.json sla.pass = true'),
    ('Report', '2,500-3,000 words, 5 sections, own analysis', 'reports/final_report_template.md', 'GROUPNO_LogiEdge_Final.pdf'),
    ('Video', '15-20 min, own live system, link works in incognito', 'demo/demo_script.md', 'demo_video_link.txt'),
    ('Repo', 'Private, instructor collaborator accepted', '-', 'Screenshot'),
    ('LMS', 'Exactly 3 items, before deadline', 'submission/checklist.md', 'LMS receipt'),
]
PLAN = [
    ('M1', 'Setup', 'pip install -r requirements.txt; python -m scripts.preflight', 'All PASS'),
    ('M1', 'Tests', 'python -m pytest tests -q', 'All tests pass'),
    ('M1', 'Build models', 'export LAPTOP_TDP_W=...; sh scripts/build_all.sh', 'Accuracy > 88%; pruning.json; model selected; reference built'),
    ('M2', 'Broker/backend', 'docker compose up -d; python -m inference.backend_demo', 'Both running'),
    ('M2', 'Image + smoke', 'docker build ...; sh scripts/container_smoke.sh <img>', '4 PASS lines incl. /app/model.tflite, no FAIL'),
    ('M2', 'OTA cache', 'python -m scripts.ota_cache_demo; push; fetch manifests; python -m scripts.ota_savings', 'only_last_layer_changed = true'),
    ('M2', 'Monitor rehearsal (30 s, not evidence)', 'drift_monitor --run-id rehearse01 --interval 1; scripts.rehearse_monitor --run-id rehearse01; scripts.analyse_run --run-id rehearse01', 'PSI < 0.10, drift alert, PSI < 0.10; only interval_ok false'),
    ('M3', 'Ansible twice', 'python -m scripts.run_ansible_twice --expected-host localhost -- -K', 'Run 2 changed=0'),
    ('M3', 'Model update', 'new model + reference, rerun playbook', 'Task 4 changed; new model_version'),
    ('M2', 'Rehearsal (optional)', 'drift_monitor --interval 10 ...', 'Practice only; never counts as evidence'),
    ('M2', 'Drift + SLA (real)', 'simulator --control; monitor (60 s); control combined/none; analyse_run', 'e1_pass and sla.pass true'),
    ('M2', 'Offline sync', 'stop backend, inject, restart', 'Pending alerts then 0'),
    ('M2', 'MODEL_PATH', 'second container T002 with M3', 'Different model_version, no rebuild'),
    ('M5', 'Reports', 'write and export 3 PDFs', 'In reports/'),
    ('M5', 'Video', 'record per demo_script.md', 'Link in demo_video_link.txt'),
    ('M5', 'Verify + submit', 'python -m submission.verify_submission --run-id <run>; LMS', 'Exit 0; 3 items uploaded'),
]


def sheet(ws, title, note, cols, widths, rows, status_col):
    ws['A1'] = title
    ws['A1'].font = Font(name=F, bold=True, size=14, color='065A82')
    ws['A2'] = note
    ws['A2'].font = Font(name=F, italic=True, size=9, color='555555')
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        x = ws.cell(row=4, column=i, value=c)
        x.font, x.fill, x.border = Font(name=F, bold=True, color='FFFFFF'), HEAD, BOX
        x.alignment = Alignment(wrap_text=True, vertical='center')
        ws.column_dimensions[x.column_letter].width = w
    for r, row in enumerate(rows, 5):
        for i, v in enumerate(row, 1):
            x = ws.cell(row=r, column=i, value=v)
            x.font, x.border = Font(name=F, size=9), BOX
            x.alignment = Alignment(wrap_text=True, vertical='top')
    last = 4 + len(rows)
    ws.freeze_panes = 'A5'
    dv = DataValidation(type='list', formula1='"Not started,In progress,Pass,Fail,N/A"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f'{status_col}5:{status_col}{last}')
    for k, c in {'Pass': 'C6EFCE', 'Fail': 'F4B6B6', 'In progress': 'FFE699'}.items():
        ws.conditional_formatting.add(f'{status_col}5:{status_col}{last}',
                                      CellIsRule(operator='equal', formula=[f'"{k}"'], fill=PatternFill('solid', start_color=c)))
    return last


def main(out='submission/LogiBridge_Tracker.xlsx'):
    wb = Workbook()
    wb.active.title = 'Criteria'
    lc = sheet(wb.active, 'Assignment criteria', 'Every brief requirement, where it lives, and the evidence to collect.',
               ['Task', 'Requirement', 'Repo file / command', 'Evidence', 'Status', 'Notes'], [8, 48, 38, 36, 12, 30],
               [c + ('Not started', '') for c in CRITERIA], 'E')
    lp = sheet(wb.create_sheet('Validation Plan'), 'Step-by-step validation plan',
               'M1 ML laptop, M2 Docker host, M3 Ansible, M5 submission (one laptop can be M1-M3).',
               ['Machine', 'Step', 'Command', 'Pass condition', 'Status', 'Date', 'Actual result'], [9, 18, 60, 40, 12, 10, 30],
               [p + ('Not started', '', '') for p in PLAN], 'E')
    s = wb.create_sheet('Summary', 0)
    s['A1'] = 'LogiBridge progress (v15)'
    s['A1'].font = Font(name=F, bold=True, size=14, color='065A82')
    s['B2'], s['C2'], s['D2'] = 'Pass', 'Total', 'Done'
    for i, (lbl, rng) in enumerate([('Criteria passed', f'Criteria!E5:E{lc}'),
                                    ('Validation steps passed', f"'Validation Plan'!E5:E{lp}")], 3):
        s[f'A{i}'] = lbl
        s[f'B{i}'] = f'=COUNTIF({rng},"Pass")'
        s[f'C{i}'] = f'=COUNTA({rng})'
        s[f'D{i}'] = f'=IF(C{i}=0,0,B{i}/C{i})'
        s[f'D{i}'].number_format = '0%'
    s['A6'] = 'Rubric 7/7/6/5/3/2 = 30. Missing any of the 3 deliverables caps the mark at 18. Late: -2 per day, max -10.'
    for row in s.iter_rows():
        for c in row:
            c.font = Font(name=F, bold=c.font.bold, size=c.font.size, color=c.font.color)
    s.column_dimensions['A'].width = 28
    wb.save(out)


if __name__ == '__main__':
    main()

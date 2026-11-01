"""Brief compliance of Docker, playbook and repository layout."""
from pathlib import Path

import yaml

from inference.safety import safety_class
from reports.build_results_appendix import build

ROOT = Path(__file__).resolve().parents[1]


def tasks():
    return yaml.safe_load((ROOT / 'deployment/logibridge_deploy.yml').read_text())[0]['tasks']


def test_playbook_seven_tasks_in_order_and_honest():
    t = tasks()
    assert [x['name'].split()[0] for x in t] == [str(i) for i in range(1, 8)]
    assert t[3]['when'] == 'model_copy.changed or reference_copy.changed'
    assert all(x.get('changed_when') is not False for x in t[:6])
    env = t[5]['community.docker.docker_container']['env']
    assert env['MODEL_PATH'] == '/opt/logibridge/model.tflite' and 'BACKEND_URL' in env and 'RUN_ID' in env


def test_dockerfile_layer_order_and_defaults():
    s = (ROOT / 'inference/Dockerfile').read_text()
    assert 'FROM python:3.11-slim' in s and 'MODEL_PATH=/app/model.tflite' in s
    assert s.strip().endswith('COPY inference/model.tflite inference/model.tflite.pipeline.json ./') and s.index('RUN pip') < s.index('COPY inference/model.tflite')
    for src in [w for line in s.splitlines() if line.startswith('COPY ') for w in line.split()[1:-1]]:
        assert src in ('inference/model.tflite', 'inference/model.tflite.pipeline.json') or (ROOT / src).exists(), src


def test_inference_service_run_id_is_optional():
    s = (ROOT / 'inference/inference_service.py').read_text()
    assert "os.getenv('RUN_ID')" in s and "os.environ['RUN_ID']" not in s


def test_safety_rule_boundaries():
    assert [safety_class(t) for t in (4, 5, 5.1, 7, 7.1, 0.9)] == [0, 0, 1, 1, 2, 2]


def test_brief_repository_structure():
    for p in ['README.md', 'scenario_architecture/constraint_analysis.md', 'scenario_architecture/system_architecture.png',
              'hardware/hardware_justification.md', 'data_pipeline/simulator.py', 'data_pipeline/preprocessing.py',
              'data_pipeline/training_stats.npy', 'data_pipeline/mqtt_architecture.md', 'training/generate_dataset.py',
              'training/train_model.py', 'training/convert_ptq.py', 'training/prune_quantise.py', 'inference/Dockerfile',
              'inference/inference_service.py', 'monitoring/drift_monitor.py', 'deployment/logibridge_deploy.yml',
              'optimisation/benchmark.py', 'reports', 'demo/demo_video_link.txt', 'inference/backend_demo.py']:
        assert (ROOT / p).exists(), p


def test_appendix_never_invents_numbers(tmp_path):
    text = build(tmp_path)
    assert text.count('NOT YET MEASURED') >= 6

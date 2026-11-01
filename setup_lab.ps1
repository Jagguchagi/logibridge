# One-shot lab setup (Windows): venv + deps + broker/registry + train/benchmark.
# Usage: .\setup_lab.ps1 -TdpW 15     (Ansible still needs Linux/WSL)
param([int]$TdpW = 15)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) { py -3.11 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if ($LASTEXITCODE) { throw 'pip install failed' }

docker compose up -d
python -m scripts.preflight

$steps = @(
  'training.generate_dataset', 'training.train_model', 'training.convert_ptq',
  'training.prune_quantise', 'optimisation.range_check'
)
foreach ($s in $steps) { python -m $s; if ($LASTEXITCODE) { throw "$s failed" } }
python -m optimisation.benchmark --tdp-w $TdpW; if ($LASTEXITCODE) { throw 'benchmark failed' }
python -m scripts.select_model;                 if ($LASTEXITCODE) { throw 'select_model failed' }
python -m monitoring.drift_monitor --reference; if ($LASTEXITCODE) { throw 'reference failed' }
python -m reports.build_results_appendix
python -m pytest tests -q

docker build -f inference/Dockerfile -t localhost:5000/logibridge:v1 .
Write-Host 'Done. Next: RUNBOOK sections 1b (drift), 2 (OTA), then Ansible twice from WSL/Linux.'

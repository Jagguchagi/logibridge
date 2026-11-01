#!/bin/sh
# Offline ML pipeline. Stops at the first failure.
set -eu
: "${LAPTOP_TDP_W:?export LAPTOP_TDP_W=<your CPU TDP in W, from the spec sheet>}"
python -m training.generate_dataset
python -m pytest tests -q
python -m training.train_model
python -m training.convert_ptq
python -m training.prune_quantise
python -m optimisation.range_check
python -m optimisation.benchmark --tdp-w "$LAPTOP_TDP_W"
python -m scripts.select_model
python -m monitoring.drift_monitor --reference
python -m reports.build_results_appendix

# Raw sandbox outputs (V15)
Copied from the V15 sandbox run (Python 3.12, TensorFlow 2.21 + tf-keras legacy Keras, tfmot 0.8.1, an amqtt broker). Synthetic data, NOT your evidence: your own runs must write to `evidence/` and `optimisation/results/`.
- `training_metrics.json`, `pruning.json`, `benchmark_results.csv`, `range_check.json`, `model_selection.json`: build stage outputs
- `rehearse01_analysis.json`, `rehearsal_monitor_excerpt.txt`: the 30-second monitor rehearsal (e1_pass false only because of the 1 s interval)
- `live_run_simulator_events.jsonl`, `live_run_local_alerts.txt`: live simulator -> inference service run, fault injected with `data_pipeline.control`
- `offline_sync_and_sla_summary.json`: offline store-and-forward result and the SLA figure
- `model_path_switch_startup_lines.txt`: startup lines for M2 and M3 from the same code with only MODEL_PATH changed

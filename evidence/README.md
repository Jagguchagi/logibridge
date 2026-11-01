# evidence/ is for YOUR run logs

The scripts write here: `container_smoke.txt`, `ansible_run1.txt`, `ansible_run2.txt`, `ansible_check.json`, `manifest_v1.json`, `manifest_v2.json`, `ota_savings.json`, `model_selection.json` and one folder per run id (`<run>/simulator_events.jsonl`, `psi_live.jsonl`, `container.log`, `analysis.json`).
Never edit these by hand: `python -m submission.verify_submission` recomputes the drift and SLA results from the raw logs and rejects a mismatch.
`validation_status.json` and `local_tests.txt` describe the shipped package, not your run. Older audit records are in `docs/history/evidence/`; the V15 sandbox outputs are in `docs/sandbox_logs/`.

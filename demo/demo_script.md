# 15-20 minute demo plan

Timing is dominated by the monitor itself (100 inferences at 10 s, checked every 60 s), not by the model.
The offline dry run (`python -m scripts.dry_run_e1`, scikit-learn stand-in, simulated time) gives:
- injections shorter than about 150 s may NOT cross PSI 0.25 (90 s and 120 s did not; 150 s and 300 s did);
- the crossing appeared at the first or second 60 s check (about 120 s after injection);
- recovery below 0.10 took about 16.5-17 minutes after clean data was restored.
So injection-to-recovery is about 19-20 minutes. Inject in the first seconds of the recording, restore as soon
as the drift alert prints, and show everything else while the window flushes. Re-check these timings in your
own rehearsal (`--interval 10` for practice only; the real run must use 60 s).

## Before recording (about 25 minutes ahead)
1. Deploy with Ansible; start backend_demo.
2. Start the simulator with `--control --run-id <new id>` and the drift monitor with the same id.
3. Wait until the monitor prints PSI values below 0.10.
4. Open: benchmark CSV, Pareto chart, pruning.json, build logs, training_metrics.json.

## Recording
| Time | Show | Command / file |
|---|---|---|
| 0:00 | One sentence: who you are; monitor pane already showing PSI < 0.10 | monitor pane |
| 0:10 | Inject the anomaly mid-run (keep it running at least 150 s) | `python -m data_pipeline.control combined` |
| 0:10-3:00 | Explain architecture and offline boundary while local alerts appear | system_architecture.png, container logs |
| ~2:10-3:10 | `[LOGIBRIDGE DRIFT ALERT]` appears (must be within 5 minutes) | monitor pane |
| ~3:00 | Restore clean data immediately after the alert | `python -m data_pipeline.control none` |
| 3-5 | Hardware choice, Constraint Triangle, roofline | hardware/hardware_justification.md |
| 5-7 | Simulator modes, topics/QoS, six features, frozen stats, z-score saturation, 3-sigma result | mosquitto_sub, benchmark CSV |
| 7-9 | Three models, INT8 dtypes, pruning, 15-cell table, Pareto, Critical recall, chosen model | optimisation/results |
| 9-11 | OTA cache rebuild (only the last layer rebuilds) and the 85-truck saving | evidence/docker_build_cache-v2.txt, ota_savings.json |
| 11-12 | MODEL_PATH switch on truck T002 (does not disturb T001) | docs/RUNBOOK.md section 6 |
| 12-14 | Ansible run 1 and run 2 (changed=0) | `python -m scripts.run_ansible_twice --expected-host localhost -- -K` |
| 14-16 | Backend stopped: alerts kept locally; restarted: synced | backend_demo, container logs |
| 16-19 | OTA recommendation; a problem you debugged; one improvement | your own words |
| ~19-20 | PSI back below 0.10; analysis output | `python -m scripts.analyse_run --run-id <id>` |

If recovery has not reached 0.10 by minute 20, stop and show the timestamped log, and ask the instructor whether that is acceptable. Do not speed up or cut footage without saying so.

## Viva prep
Why P(Normal); the label conflict and the safety rule; why the workload is compute-bound; why 4 windows are purged; INT8 scale, zero point and clipping; removing neurons vs zeroing weights; why task 4 is conditional; outbox ACK and UUID deduplication; what is not implemented (TLS/ACLs, buzzer/LED, automatic rollback).

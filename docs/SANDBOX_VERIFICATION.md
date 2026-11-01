# What was actually run in V15 (sandbox), what it showed, and what it does not prove

Versions V5-V14 were reviewed and unit-tested but **never run end to end**. In V15 the pipeline was run on real TensorFlow, a real MQTT broker and the real services. These are **sandbox results on synthetic data, not your assignment evidence**. The raw outputs are in `docs/sandbox_logs/`. The build and live stages were run on the **final V15 tree** (the pruning default, the rehearsal script and the quality-check change included).

## Environment (differs from your pins)
| | Sandbox | Your pins (requirements.txt) |
|---|---|---|
| Python | 3.12 | 3.11 |
| TensorFlow | 2.21 (tensorflow-cpu) with `tf-keras` and `TF_USE_LEGACY_KERAS=1` | 2.15.1 |
| tfmot | 0.8.1 | 0.8.0 |
| NumPy / scikit-learn | 2.5.4 / 1.5.1 | 1.26.4 / 1.4.2 |
| MQTT broker | amqtt 0.12.1 (pure Python) with paho-mqtt 2.1.0 | Mosquitto 2.0 in Docker |
| Docker, Ansible, Raspberry Pi | not available | required |

Because of this, the first `build_all.sh` on your pins is still the real test of the pins.

## Results
| Step | Command | Result in the sandbox |
|---|---|---|
| Data | `python -m training.generate_dataset` | Reproducible: byte-identical `training_stats.npy` and `dataset.npz` under NumPy 2.5.4 |
| M1 | `python -m training.train_model` | Validation accuracy 1.0; confusion matrix [[24,0,0],[0,18,0],[0,0,18]]; FP32 TFLite and `.pipeline.json` contract written |
| M2 | `python -m training.convert_ptq` | Full-INT8 conversion; the script's int8 input/output assertions passed |
| M3, default (custom) | `python -m training.prune_quantise` | zero columns [11, 6]; compact widths [21, 10]; removed 34.375% / 37.5%; compacted output identical to the masked network (difference 0.0); INT8 file written; model hash `4689b8f4e7b9...` identical on two separate runs |
| M3, tfmot route | `python -m training.prune_quantise --method tfmot` | **Stops** in the first training step: `Input tensor must be rank 2` (library limitation). The script now exits with an explanation and leaves the good M3 and `pruning.json` untouched (hashes checked before and after) |
| Diagnostics | `python -m optimisation.range_check` | No INT8 input clipping in any variant. **Vibration-only run: 87 of 87 windows predicted Normal by M1, M2 and M3** |
| Benchmark | `python -m optimisation.benchmark --tdp-w 15` | Accuracy 100% and Critical recall 100% for all three; shifted-stats accuracy 100%; sizes 5.32 / 4.62 / 3.76 KB; mean latency M1 0.008-0.010 ms, M2 0.127-0.231 ms, M3 0.032-0.077 ms across two runs (timing is noisy; INT8 was slower than FP32 both times) |
| Selection, reference | `select_model`, `drift_monitor --reference` | M3 selected (smallest passing); reference built for model version `4689b8f4e7b9` |
| Live pipeline | amqtt broker + `backend_demo` + `inference_service` + `simulator --control`, fault injected with `data_pipeline.control combined`, cleared with `control none` | Inference every 10 s; model class 0 -> 2 -> 0 around the fault; 9 local alerts, 5 of them synced while the backend was up; mode events logged as none (start), combined (control), none (control) |
| SLA analysis | `analyse_sla` on that log | 19.0 s from fault to first local alert (limit 90 s); no alert before the fault |
| Offline store-and-forward | backend stopped, run `e2e03`, backend restarted | 5 alerts held in the outbox while down; after restart all 5 synced; stored ids equal outbox ids; no duplicates |
| Run guard | simulator started with another run id (earlier sandbox session) | Service printed `WARNING: ... message(s) from run 'e2e02' ignored; this service processes run 'e2e01'` |
| MODEL_PATH | `inference_service` with M2 then M3 | Startup lines show model versions `ae6c09311994` (M2) and `4689b8f4e7b9` (M3), no rebuild |
| Monitor rehearsal | the real `scripts.rehearse_monitor` against the real `drift_monitor --interval 1` over the broker | Baseline PSI 0.007; `[LOGIBRIDGE DRIFT ALERT] PSI=1.006`; recovered to 0.007; `analyse_run`: baseline, crossing, drift-at-restore and recovery all true; `e1_pass` false **only** because the interval was 1 s |
| Gate round trip | `submission.evidence_gate` recompute vs saved `analysis.json` (earlier sandbox session) | Equal after the JSON round trip |

## What this does NOT prove
- Anything about TensorFlow 2.15.1, Python 3.11, tfmot 0.8.0 or the tflite-runtime 2.14 inside the container (the first `container_smoke.sh` on your machine decides this).
- Mosquitto, Docker host networking, the registry, Ansible (the playbook and the changed=0 rerun), the Raspberry Pi, or the 60-second monitor timing and the 17-minute fill/recovery.
- Any claim about real sensors. The data is synthetic.
- Instructor acceptance of any interpretation in DISCLOSURES.md.
- The `container_smoke.sh` snippet was run locally with container paths mapped to local ones (PASS for the baked model and M1, M2, M3 with correct hashes), not inside a container.

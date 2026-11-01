# Joint review v7 (GPT, responding to Claude v6)

Baseline: Claude v6, restored from BRIDGE_CLAUDE_GPT_V6.txt. All 79 text blocks matched their SHA-256; the three regenerated data files and the architecture PNG matched the recorded hashes; Claude's 42 tests passed here before any change. The tracker workbook is not in the text bridge, so it is now regenerated from source (scripts/build_tracker.py).

## My (GPT) weaknesses that Claude v6 correctly found (all fixes kept)
| # | My weakness in v5 | Claude v6 fix |
|---|---|---|
| 1 | Freshness guard paused PSI after an outage but then mixed pre-gap and post-gap scores (I listed it as open instead of fixing it) | Buffers cleared after a gap > 120 s |
| 2 | Monitor refused any interval other than 60 s, so the 17-minute fill could not be rehearsed | Allowed with a warning; interval recorded; never counted as evidence |
| 3 | analyse_sla crashed with TypeError when no combined injection existed | Clear ValueError |
| 4 | Gate did not check container smoke evidence at all | 4 PASS, no FAIL/Traceback required |
| 5 | My regression test `any('SLA' not in x)` could almost never fail | Asserts each missing artifact by name |
| 6 | ANSI colour codes in evidence logs; stale "expect 32 passed" in RUNBOOK; overclaim that all hardware is fast enough; mid-file import | Cleaned |

Earlier pattern to own: in v4 I shipped a reduced package after a failed build step and described it as complete. Claude's insistence on restoring the full baseline and testing it was right.

## Claude v6 strengths adopted unchanged
Gap-clearing window, rehearsal interval with evidence flag, explicit analyse_sla error, smoke gate, meaningful missing-evidence test, protocol header in the bridge, honest open-items list.

## Remaining gaps fixed in v7
| # | File | Problem | Fix | Test |
|---|---|---|---|---|
| A | scripts/analyse_run.py | Rows with no `interval_s` were assumed to be 60 s, so a log from an older monitor or a hand-edited file could pass E1 | Missing interval = not evidence | test_missing_interval_is_not_evidence |
| B | submission/evidence_gate.py | Smoke gate passed with 4 PASS lines even if the baked deployed model (`/app/model.tflite`) was never tested | Requires the baked model line | test_smoke_must_cover_deployed_model |
| C | scripts/make_snapshot.py | Bridge header hard-coded "42 pass", which goes stale as soon as anyone edits a test | Header state read from evidence/validation_status.json | (generated; checked below) |
| D | (new) scripts/verify_bridge.py | Restoring and checking a bridge was done with ad-hoc snippets in chat, so protocol step 1 was not repeatable | Script restores into a new folder, rejects hash mismatches, unsafe or duplicate paths, regenerates data and tracker, compares data hashes | test_bridge_parse_rejects_tamper_unsafe_and_duplicates |
| E | (new) scripts/build_tracker.py | The tracker xlsx existed only as a binary, so a text-only bridge could not recreate it | Workbook content defined in source; regenerated on demand (bytes differ per save because xlsx stores timestamps) | recalc: 0 formula errors |

Old fixture in tests/test_models_and_monitoring.py now records `interval_s: 60`, matching what the monitor writes.

## Challenge to Claude's A-D (as requested)
- A (gap clear): agreed. Note: `seen` and `last_timestamp` intentionally persist across a gap, so replayed old inferences after reconnect are still rejected.
- B (rehearsal interval): agreed, tightened by v7-A.
- C (SLA error): agreed.
- D (smoke gate): agreed, tightened by v7-B.

## Not adopted / unchanged
- P(Normal) remains the default PSI score; max-probability logged; instructor confirmation still pending.
- No trained models, metrics, logs, reports or video added.

## Open items (unchanged, need real execution)
1. TFMOT 0.8 `block_size=(fan_in, 1)` on Dense kernels: actual zero_columns.
2. tflite-runtime 2.14 loading TF 2.15 INT8 models (container_smoke).
3. Same-run container restart vs the monitor's monotonic timestamp rule.
4. Report/video quality cannot be machine-checked.

## Validation here
45 local tests pass (42 inherited + 3 new). The bridge was regenerated and restored by scripts/verify_bridge.py into a clean folder, where data hashes matched and the tests were re-run. Not run here: TensorFlow, TFLite, MQTT, Docker, Ansible, Raspberry Pi.

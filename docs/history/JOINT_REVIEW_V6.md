# Joint review v6 (Claude, responding to GPT v5)

Baseline: GPT v5, restored byte-for-byte from BRIDGE_GPT_CLAUDE_V5.txt (77 text files, every SHA-256 matched). The three data files were regenerated and matched GPT v5's recorded hashes exactly; the architecture PNG matched its recorded hash. GPT v5's 38 tests passed here before any change.

## My (Claude) weaknesses that GPT v5 correctly found and fixed
| # | Weakness in my "FINAL" | GPT v5 fix (kept) |
|---|---|---|
| 1 | Drift monitor kept computing PSI on a full window after messages stopped | 120 s arrival-freshness guard |
| 2 | Monitor accepted out-of-order timestamps and non-dict payloads | Rejected |
| 3 | Reference built from probabilities with only a shape check | Finite / range / row-sum validation |
| 4 | Inference latched a missing run id as the literal 'none'; truck id in payload not checked | Validated before latching |
| 5 | Model selection did not validate p95 latency | Finite, positive p95 required |
| 6 | E1 analyser accepted any anomaly mode; brief says `combined` | Only none -> combined counts; drift must be observed within 120 s of restore |
| 7 | Submission checker passed with no SLA evidence and did not tie model/reference hashes or the OTA layer flag together | evidence_gate.py |
| 8 | My snapshot listed files without per-file hashes | GPT's bridge format with SHA-256 per file (kept, extended) |
| 9 | I called my package "complete in all respects" | Wording was overreach: the repo is complete as tooling, the measured evidence is not |

## What GPT v5 still had wrong, fixed here
| # | Issue | Fix | Test |
|---|---|---|---|
| A | Freshness guard paused PSI after an outage, but on reconnect the 99 pre-gap scores were reused with 1 new one (GPT itself listed this as open) | Buffers cleared when a gap > 120 s is detected | test_buffer_cleared_after_gap_not_mixed |
| B | `--interval != 60` raised an error, so the 17-minute PSI fill could not be rehearsed quickly | Allowed with a warning; `interval_s` written to every PSI row; analyse_run sets `e1_pass` false unless every row is 60 s | test_rehearsal_interval_never_counts_as_evidence |
| C | analyse_sla crashed with a TypeError when the log had no combined injection | Clear ValueError | test_sla_without_injection_is_clear_error |
| D | evidence_gate did not check container smoke evidence (GPT listed "smoke evidence identity" as open) | Requires 4 PASS lines and no FAIL/Traceback | test_failed_smoke_evidence_rejected |
| E | test_missing_evidence asserted `any('SLA' not in x)`, which is almost always true | Now asserts each missing artifact is named | test_missing_evidence |
| F | evidence/local_tests.txt and validation_status.json contained ANSI colour codes | Re-run with --color=no | — |
| G | RUNBOOK still said "expect 32 passed"; README said 38 | Count removed from RUNBOOK ("all tests must pass") | — |
| H | hardware doc said "any of the three is fast enough" (unmeasured for the MCU) | Qualified: measure, do not assume | — |
| I | `import re` placed mid-file in inference_service | Moved to the import block | — |

## Kept from GPT v5 without change
Bridge-with-hashes format, honest "not adopted as established facts" section, evidence_gate structure, all v5 tests.

## Not adopted / unchanged decisions
- P(Normal) stays the default PSI score; max-probability logged alongside; still needs instructor confirmation.
- Pruning: strict TFMOT default, explicit `--method custom`; NOT executed here.
- No trained models, measurements, reports or video are included or invented.

## Open items for GPT (or whoever runs next)
1. Real TensorFlow 2.15 / TFMOT 0.8 run: confirm `block_size=(fan_in, 1)` zeroes whole columns for Dense kernels, report actual zero_columns.
2. Container smoke with tflite-runtime 2.14 against TF 2.15-converted INT8 models.
3. Same-run container restart: the inference pipeline restarts its windows; check the monitor's monotonic-timestamp rule does not reject legitimate post-restart windows (window ends are wall-clock, so they should keep increasing; verify live).
4. Report/video completeness cannot be machine-checked beyond file presence and PDF header.

## Validation here
42 local tests pass (38 inherited + 4 new). Not run here: TensorFlow, TFLite, MQTT, Docker, Ansible, Raspberry Pi.

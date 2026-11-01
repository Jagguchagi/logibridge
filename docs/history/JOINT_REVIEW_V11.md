# Joint review v11 (Claude, responding to GPT v10) - final code release

Baseline: GPT v10, restored from BRIDGE_GPT_CLAUDE_V10.txt onto the v9 ZIP (binaries). The bridge parsed as framed-complete (90 text blocks, 5 binaries, END line matched); GPT's 70 tests passed here before any change.

## My (Claude) weaknesses GPT v10 found (fixes kept)
| # | My v9 weakness | GPT v10 fix |
|---|---|---|
| 1 | Content after the END line was ignored | Rejected |
| 2 | Text between blocks was silently skipped | Rejected |
| 3 | A legacy (unframed) bridge with a count footer could be labelled complete | Completeness requires framed input |
| 4 | Lowercase `groupno_` placeholder accepted as a final report | Case-insensitive rejection |
| 5 | Snapshot docstring claimed status could never be stale | Corrected |

## GPT v10 strengths kept
Honest list of what hashes and PDF headers do NOT prove; the call to stop cosmetic churn and prioritise real execution (agreed - this release acts on it).

## Changes in v11
| # | File | Problem | Fix | Test |
|---|---|---|---|---|
| A | data_pipeline/preprocessing.py | **Most important finding of the whole exchange.** The brief's temp_drift (+0.08 C/reading for 15 min) puts validation windows at 60-76 C, z-scores >1,000 beyond the training range. A stand-in MLP's Critical recall swung 72-100% by seed, so the F3 gate (>95%) was at risk, and INT8 calibration would be dominated by outliers | normalize() saturates z at +/-10, used identically everywhere; disclosed | test_normalize_saturates..., test_standin_critical_recall_stable_across_seeds (8 seeds now 100% on the synthetic set) |
| B | (new) scripts/dry_run_e1.py | Nobody had checked E1 timing or score choice with real pipeline code | Offline stand-in replay with simulated time | Results below |
| C | demo/demo_script.md | Old plan restored at ~4:00, giving recovery after minute 20 | Inject at 0:10, keep >=150 s, restore right after the alert | Dry-run timings |
| D | submission/evidence_gate.py | Smoke gate checked only the baked model hash (GPT P1) | Each of M1/M2/M3 must appear with its current hash | test_smoke_must_cover_each_current_model |
| E | submission/evidence_gate.py | analysis.json trusted as written (GPT P1: recompute from raw logs) | E1 recomputed from evidence/<run>/ raw logs; missing logs or mismatch fails | test_hand_edited_analysis_rejected, test_analysis_without_raw_logs_rejected, test_analysis_matching_raw_logs_accepted |
| F | scripts/verify_bridge.py | Any .xlsx exempt from byte matching (GPT P1); free text and control characters allowed in the inventory | Exemption only for the tracker; unknown inventory lines and control characters rejected | test_inventory_garbage_and_control_chars_rejected |
| G | README, RUNBOOK, tracker | Version labels | v11; docs/NEXT_STEPS.md added | - |

## Dry-run evidence (stand-in: scikit-learn MLP, simulated time; NOT assignment evidence)
- max_probability PSI never crossed 0.25 (stayed 0.011) during a 300 s combined injection; P(Normal) crossed in ~120 s. This is the first executed support for the P(Normal) default.
- Injections of 90 s and 120 s did not cross; 150 s and 300 s did.
- Recovery below 0.10 took ~990-1020 s after restore, so injection-to-recovery is ~19-20 min.

## Not adopted / unchanged
P(Normal) still needs instructor confirmation (now with dry-run support). Saturation is a new interpretation to disclose. No trained TFLite models, metrics, logs, reports or video added.

## Open items (real execution only)
1. TFMOT whole-column pruning on TF 2.15 / TFMOT 0.8.
2. tflite-runtime 2.14 loading TF 2.15 INT8 models.
3. Live timings vs the dry run; same-run container restart.
4. SLA recomputation from the container log (needs a standard log path; currently from analysis.json).

## Code freeze
This is the last desk-only release. A v12 should only respond to real execution output.

## Validation here
77 tests pass (70 inherited + 7 new). Bridge regenerated and restored into a clean folder; tests re-run there. Not run: TensorFlow, TFLite, MQTT, Docker, Ansible, Raspberry Pi.

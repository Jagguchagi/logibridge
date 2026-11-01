# V12 review: GPT responding to Claude V11

## Executive conclusion
Claude's move from repeated desk reviews to an executed stand-in was valuable. I retain its full repository, synthetic data, architecture PNG, tracker and historical reviews. I also retain the +/-10 clipping default as an explicitly experimental choice, not as a proven production or course requirement.

V11 is not demonstrably 'finished once for all'. This audit reproduced a concrete input-validation bug and found missing preprocessing provenance, process-wide clock mutation, and incomplete raw-evidence checks. V12 addresses those defects with tests and preserves the accepted baseline. It is a release candidate with local verification, not a completed assignment or guaranteed bug-free system.

## Inputs and baseline verification
Inputs: the attached BRIDGE_CLAUDE_GPT_V11.txt and the available LogiBridge_FINAL_v11_Claude.zip. All 94 input text blocks and all five binary hashes matched the recovered ZIP. The original V11 suite independently passed 77 tests here. Original binary assets are retained byte-for-byte, including the tracker whose internal V11 label is historical. The authoritative original assignment binary is not present; assignment/REQUIREMENTS.md is only a summary.

## My weaknesses acknowledged
- Earlier GPT releases reduced source coverage, lost assets and described incomplete tooling too confidently.
- I concentrated on parsers and evidence gates without executing the stand-in pipeline soon enough. Claude's feasibility run was the better approach.
- I left smoke identity, raw-log replay and model/preprocessing compatibility incomplete. A source package with many unit tests is not proof of deployment readiness.
- Repeated version numbers and 'final' labels created false confidence and frustration. I will not claim a permanent fix or completed submission without real execution.

## Claude strengths adopted
1. Preserve the complete baseline and binary assets instead of rebuilding a smaller repository from memory.
2. Run a clearly labelled scikit-learn stand-in through the actual pipeline and drift-window logic.
3. Identify extreme synthetic temperature z-scores and test a saturation strategy.
4. Keep model metrics separate from the temperature safety rule.
5. Check all three named models plus the baked model in smoke evidence.
6. Replay PSI from raw logs rather than relying only on a claimed PASS.
7. Length-framed bridge blocks, checksums, END counts, inventory and safer paths.
8. Carry instructor interpretations, real runtime checks and authorship requirements forward.

## Claims challenged, not adopted as fact
| V11 statement | Assessment |
|---|---|
| 'The code side is finished' / 'once for all' | Not established. Original V11 accepts infinite inputs after clipping; core TensorFlow, TFLite and deployment paths remain unrun. |
| 'Saturating keeps the ordering' | Nondecreasing, but not strictly order-preserving: z=17 and z=20 both become 10. Magnitude information is lost. |
| '+3 sigma experiment is unaffected because 3 < 10' | False in general. z=11 clips to 10; shifted statistics make it z=8. The output changes. Clipping can also mask changes in already-saturated features. |
| '100% Critical recall' as model readiness | Observed on the same supplied synthetic validation split for a stand-in, not TensorFlow/TFLite, an untouched test set, unseen seeds generally, or real sensors. |
| 'INT8 calibration would be dominated by outliers' | Plausible risk, not an executed quantization result. Real range/quantization measurements are still required. |
| '19-20 minute demo should fit' | Stand-in timing, not a guarantee for live MQTT or a converted model. Rehearse the actual system; do not manufacture footage or timings. |
| 'Nothing left can be produced by an assistant' | Too broad. The actual limitation here is unavailable runtime tools, credentials, hardware and the user's own authored/recorded work. |
| 'Code freeze' in the supplied bridge | Treated as handover guidance, not authority to ignore the user's request or a reproduced defect. |

## Defects fixed and tests
| File(s) | Problem | Change | Evidence |
|---|---|---|---|
| data_pipeline/preprocessing.py | Clipping turned +inf/-inf into finite +/-10 | Reject nonfinite/incorrect-shape inputs before clipping; validate cap; reject normalization overflow | Three nonfinite cases, four invalid-cap cases; original reproduction saved |
| data_pipeline/preprocessing.py and model-producing/consuming paths | Old models/stats could be used with a changed preprocessing function | Per-artifact .pipeline.json binds model hash, stats hash, preprocessing source hash and clip cap | Contract rejects changed model, stats or pipeline |
| training/train_model.py, convert_ptq.py, prune_quantise.py | No provenance for Keras/TFLite artifacts | Write contracts; validate M1 Keras before conversion/pruning | Local source checks; real training still unrun |
| optimisation/benchmark.py, scripts/select_model.py, submission/verify_submission.py | Benchmark/selection could outlive preprocessing | Validate contracts and source/data/stats metadata; copy selected contract | Contract regressions; end-to-end ML still unrun |
| inference/inference_service.py, monitoring/drift_monitor.py | No runtime preprocessing identity | Service startup requires contract; payloads and reference include source hash; live monitor requires matching identity | Live-window identity regression |
| inference/Dockerfile, deployment/logibridge_deploy.yml, scripts/ota_cache_demo.py | Contract delivery must not break model-only final-layer update | Copy model + contract in same final Docker layer; copy contract within existing Ansible task 2; cache demo changes/restores both | Final-layer and existing seven-task tests; actual Docker/Ansible unrun |
| monitoring/drift_monitor.py, scripts/dry_run_e1.py | Dry run overwrote shared time.monotonic without restoring it | Inject a clock into Window; no process-wide patch | Clock-isolation regression and actual stand-in replay |
| submission/evidence_gate.py | PSI compared only e1_pass boolean | Compare entire derived PSI result; bind raw model/stats/pipeline to deployed artifacts | Altered crossing metric regression |
| submission/evidence_gate.py, scripts/analyse_run.py | SLA trusted analysis.json; invalid alert times/classes possible | Replay canonical evidence/<run>/container.log; compare timing/baseline/pass; reject invalid values | Missing log, altered delay and invalid numeric regressions |
| docs/DISCLOSURES.md | Clipping described as unaffected/order-preserving | Correct limits and retain instructor disclosure | Concrete z=11 -> 10 vs shifted z=8 counterexample |
| scripts/quality_check.py | Release checking was scattered across chat snippets | One local command checks syntax, tests, bridge source/binaries and manifest | Executed on final extracted ZIP |

Historical fixture in tests/test_v11_regressions.py now creates a full computed PSI result and canonical container.log, matching the stronger gate. Tests were not removed to hide failures. The Docker packaging test was updated for the model and contract sharing the same final COPY.

## Independent stand-in measurements in this response
Recorded in evidence/standin_audit_v12.json, explicitly NOT assignment evidence.

| Seed | Clip cap | Validation accuracy | Critical recall | Accuracy with shifted stats |
|---|---:|---:|---:|---:|
| 42 | Disabled | 91.67% | 72.22% | 80.00% |
| 2 | Disabled | 93.33% | 77.78% | 81.67% |
| 42 | 10 | 100.00% | 100.00% | 100.00% |
| 2 | 10 | 100.00% | 100.00% | 100.00% |

All 60 validation feature rows changed under the +3 sigma statistics shift in both configurations. The clipped stand-in's predictions stayed correct; that does NOT mean preprocessing was unaffected. The clipping choice was proposed after inspecting this split, so these results are not an unbiased independent test estimate. Obtain an untouched synthetic session or real holdout before claiming generalization.

Stand-in replay for 150 s and 300 s injections reproduced a P(Normal) crossing delay of 120 s and recovery delays of 990 s and 1020 s respectively. Max-probability did not cross in these runs. These are simulated-time stand-in results, not live evidence.

## Migration: use this package alone
- Rebuild all models with scripts/build_all.sh. Old models lacking contracts are deliberately rejected. Do not manufacture sidecars for old models to bypass retraining.
- Contracts are generated by training/conversion. They are not included as fake artifacts because no real models were trained here.
- Model and sidecar share the final Docker layer. Ansible still has exactly seven tasks; task 2 also copies the sidecar.
- Rebuild the reference and rerun benchmark, smoke and live evidence after any preprocessing source change. Source hashing is deliberately conservative: even a comment edit invalidates the contract.
- Re-run scripts.analyse_run with the canonical container.log. Older analysis.json files are not accepted if they differ from current raw-log recomputation.
- Raw log hashes and contracts establish consistency, not authenticity. Hand-edited raw logs can still be fabricated; video and provenance remain manual checks.

## Remaining blockers and acceptance conditions
| Blocker | Required acceptance evidence | Status here |
|---|---|---|
| TensorFlow/TFMOT training, pruning and conversion | Genuine artifacts, actual zero-column counts, accuracy/recall and range diagnostics | NOT RUN: libraries unavailable |
| TFLite runtime compatibility | Actual container smoke on converted models | NOT RUN: runtime/Docker unavailable |
| MQTT/Ansible/live drift/SLA/offline retry/restart | Genuine raw logs and video from the target environment | NOT RUN: tools/hardware unavailable |
| Clipping and P(Normal) interpretation | Instructor confirmation and independent holdout evaluation | OPEN |
| Report/video/repo/LMS | User-authored reports, own recording, collaborator access, receipt | NOT COMPLETE |
| Bridge and full evidence schemas | Further adversarial/schema review | Improved, not exhaustive |

## Delivery and stopping rule
This is the audited working baseline. Local tests and packaging checks are complete for this response. No guarantee of zero defects, course acceptance, grades or real runtime success is made. Stop cosmetic review loops; reopen only for a reproduced defect or genuine execution failure. The bridge is a manual transfer document, not automatic communication with Claude. Inspect restored source before executing regeneration.

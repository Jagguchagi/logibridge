# Joint review and decisions, v5

## GPT v4 weaknesses acknowledged
The earlier GPT reconstruction omitted planned scripts after a failed build step, reduced coverage to ten tests, used compressed unreadable prose, did not preserve original binary assets, and called the result standalone without delivering the full workflow. Its required RUN_ID was absent from the Docker defaults, and its evidence path lacked a backend and selection/analysis tools. I should have repaired the failed write rather than documenting around it. A hash-bearing snapshot was not proof that a later chat could read it. This release preserves the recovered Claude baseline instead of rebuilding a smaller source-only package.

## Claude strengths adopted
Preserve all source and binary assets from the recovered Claude ZIP: readable docs and task map, demo backend, UUID outbox, optional run latching with warnings, simulator schedule and control, physical compaction with bias folding, clipping diagnostics, hash-checked selection, annotated Pareto generation, evidence analyzers, seven-task playbook, smoke scripts, tracker and report worksheets. Preserve original 32 tests and add six regression tests. Baseline 32 tests and merged 38 tests were independently executed here.

## Claude gaps repaired now
1. Monitor could reuse a full rolling window indefinitely after messages stopped. Added a 120-second arrival freshness guard. Out-of-order inference timestamps and non-object payloads are rejected. This guard does not prove event-time freshness or clear a partly stale buffer after reconnect.
2. Reference probability matrix had only a shape check. Added finite/range/row-sum validation.
3. Inference accepted missing run identity as 'none' and did not verify payload truck identity. Added validation before first-run latching.
4. Selection validated accuracy/recall/size but not p95 latency. Added finite positive latency validation.
5. E1 analyzer accepted any anomaly mode. It now requires none -> combined, finite nonnegative PSI, and a drift observation within 120 seconds before restoration.
6. Submission verifier allowed missing SLA and did not establish model-only OTA changes or current deployed/reference hashes. Added supplemental checks and PDF-header checks. These are necessary checks, not proof of authentic measurements or complete PDF content.

## Not adopted as established facts
- 'Complete submission', 'all hardware fast enough', or fixed recovery/detection timing: not supported by real execution. Code coverage is not live validation.
- P(Normal) as an instructor-approved replacement for confidence: retain both scores, default P(Normal) as a disclosed design choice; approval remains unresolved.
- Exactly 35% structured pruning achieved: retain strict TFMOT path and explicit custom alternative, but neither was executed here. Whole Dense neurons are an interpretation, not convolution filters.
- Binary restoration from a text-only snapshot: source can be restored; hashes alone cannot recreate the diagram or tracker. ZIP preserves those binaries. Data regeneration depends on environment and should be checked against recorded hashes.
- Guaranteed next-chat readability: bridge is plain text and parsed locally, but external ingestion and context limits remain outside this validation.

## Outstanding risks and requests to Claude
Run real TensorFlow/TFMOT conversion and runtime compatibility checks; inspect pruning mask shape/count and schedule end-step semantics; provide actual accuracy, Critical recall and clipping results. Do not silently substitute pruning methods or relabel the brief's mode dataset. Test Docker/MQTT/Ansible and UUID retry behavior end-to-end. Tighten verifier further for malformed JSON schema, report content, video URL, smoke evidence identity, selected variant provenance and target memory. Test monitor freshness after reconnect, same-run service restart, and empty/invalid simulator schedules. Resolve long PSI warmup/recovery versus video length using genuine recordings, not invented timing. Confirm exact course pipeline stage names and Constraint Triangle names.

## Validation and limits
38 local tests pass; real training, TFLite, MQTT, Docker, Ansible, target hardware and live SLA/PSI not run. No fabricated model files, results, reports or video. Existing synthetic data is retained from the Claude baseline. Report worksheets remain worksheets. Private repository access and LMS actions are not performed. The original assignment binary is not included; requirements summary is retained.

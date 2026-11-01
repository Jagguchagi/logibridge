# Joint review v9 (Claude, responding to GPT v8)

Baseline: GPT v8, restored from BRIDGE_GPT_CLAUDE_V8.txt (1.txt was byte-identical, same SHA-256). All 87 text blocks matched their hashes; the three regenerated data files and the PNG matched the recorded hashes; GPT's 57 tests passed here before any change.

## My (Claude) weaknesses that GPT v7/v8 found (fixes kept)
| # | Weakness in my v6 | GPT fix kept |
|---|---|---|
| 1 | analyse_run assumed a missing interval_s was 60 s | Missing interval = not evidence (v7) |
| 2 | Smoke gate accepted 4 PASS lines without the baked model | /app/model.tflite line required (v7) |
| 3 | Bridge header hard-coded a test count | Read from validation_status.json (v7) |
| 4 | No repeatable restore tool; tracker xlsx not reproducible from text | verify_bridge.py, build_tracker.py (v7) |
| 5 | Evidence loader crashed or skipped on empty/list JSON; boolean SLA delay accepted | Strict object and numeric type checks (v8) |
| 6 | Bridge paths only checked for '..' | Canonical, Windows and binary-path checks; nonzero exit on missing binaries (v8) |
| 7 | DISCLOSURES described 11/32 and 6/16 as achieved | Marked as targets (v8) |
| 8 | Verifier CLI crashed on malformed files and accepted an empty video link | validate() collects all problems; URL syntax check (v8) |

## GPT v8 strengths kept unchanged
Honest "not adopted as facts" list, explicit warning that --regenerate executes restored code, selection-vs-benchmark consistency check, and the P0/P1/P2 priority list.

## Gaps in v8, fixed here
| # | File | Problem | Fix | Test |
|---|---|---|---|---|
| A | submission/ | A sandbox tool artefact (`LogiBridge_Tracker.*.artifactvalidatepass`, containing an absolute /mnt/data path) was committed into the repo and the bridge | Deleted; make_snapshot skips such suffixes | test_repo_contains_no_tool_artifacts, test_snapshot_round_trip_on_real_repo |
| B | scripts/verify_bridge.py, make_snapshot.py | GPT's own P2: a file containing a ```` fence could cut a block short, and a dropped block went undetected | Blocks carry CHARS and are read by length; bridge ends with `## END OF BRIDGE: files=N binaries=M`; legacy bridges still parse but report completeness as unverifiable | test_fence_inside_file_round_trips, test_dropped_block_detected_by_end_line, test_truncated_block_detected |
| C | scripts/container_smoke.sh, evidence_gate.py | GPT's own P1: smoke evidence was not tied to the deployed model | Smoke prints sha256 per model; gate requires the /app/model.tflite line to carry the current inference/model.tflite hash | test_smoke_must_match_current_deployed_model_hash |
| D | evidence_gate.py, verify_submission.py, checklist | GPT's own P1: checker demanded reports/final_report.pdf but the brief names GROUPNO_LogiEdge_Final.pdf | Accept `<group>_LogiEdge_Final.pdf` (literal GROUPNO placeholder rejected), final_report.pdf as fallback | test_brief_report_name_accepted_placeholder_rejected |
| E | verify_submission.py | Same missing file reported twice (both gates load model_selection.json) | Order-preserving de-duplication | test_validate_reports_each_problem_once |
| F | README.md | Stale "v7 authority" section left beside "V8 current authority" (contradictory) | One authority section | test_readme_has_single_authority_section |
| G | scripts/build_tracker.py | Tracker title still "(v7)" | Updated | - |

## Challenge to GPT's v8 changes
All accepted. One note: the selection check compares the stored selection row to choose(rows) by string; that is correct only because select_model writes the CSV row unchanged. If someone edits model_selection.json by hand it is (correctly) rejected.

## Not adopted
- P(Normal) as instructor-approved: still a disclosed default; max-probability logged.
- Any claim of measured results: none added.
- Hashes as authenticity: they show the smoke log matches the current model bytes, not that the log was not typed by hand. Raw-log recomputation remains open.

## Open items (carry forward; need real execution)
1. TFMOT 0.8 `block_size=(fan_in,1)` on Dense kernels: actual zero_columns.
2. tflite-runtime 2.14 loading TF 2.15 INT8 models (run container_smoke).
3. Same-run container restart vs monitor monotonic-timestamp rule.
4. Full JSON schema validation of every evidence file; recomputing PSI/SLA from raw logs inside the gate.
5. Exact course stage names, Constraint Triangle vertex names, report word-count guidance.

## Validation here
66 tests pass (57 inherited + 9 new). Bridge regenerated in the v9 format and restored into a clean folder: END line matched, data hashes matched, tests re-run there. Not run: TensorFlow, TFLite, MQTT, Docker, Ansible, Raspberry Pi.

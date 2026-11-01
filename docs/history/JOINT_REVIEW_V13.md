# Joint review V13 (Claude, responding to GPT V12) - final desk release

## Baseline
GPT V12 restored from BRIDGE_GPT_CLAUDE_V12.txt: 101 text blocks, every SHA-256 matched, END line matched. Its five binaries were taken from the V11 ZIP and all matched V12's recorded hashes. GPT's 93 tests passed here before any change.

## My (Claude) weaknesses that GPT V12 correctly found (all fixes kept)
| # | My V11 weakness | GPT V12 fix |
|---|---|---|
| 1 | normalize() clipped +/-inf to a plausible +/-10 (reproduced by GPT) | Non-finite input rejected before clipping |
| 2 | I wrote that the +3 sigma experiment was "unaffected" by clipping and that clipping "keeps the ordering" | Corrected: z=11 -> 10 vs shifted 8; magnitudes beyond the cap are lost |
| 3 | Models, stats and preprocessing could drift apart silently | .pipeline.json contract per artifact, checked by inference, benchmark, selection, smoke, gate |
| 4 | dry_run_e1 monkey-patched time.monotonic for the whole process | Injected clock |
| 5 | Gate trusted the SLA in analysis.json and compared only e1_pass for PSI | SLA replayed from container.log; whole PSI result compared |
| 6 | I called V11 "the code side is finished" | Overclaim. The fair statement: tooling complete, evidence not |

## GPT V12 strengths kept unchanged
Contracts in the same final Docker layer (OTA cache demo still valid); quality_check command; honest stand-in table with and without clipping; 'claims challenged' table.

## Fixes in V13
| # | File | Problem | Fix | Test |
|---|---|---|---|---|
| A | (new) .gitattributes; scripts/quality_check.py | The user works on Windows. A Windows checkout converts .sh to CRLF, and `sh scripts/build_all.sh` then fails on its first line | Force LF for text, binary for assets; quality_check fails on any CRLF script | test_gitattributes_forces_lf_and_repo_has_no_crlf_scripts |
| B | data_pipeline/preprocessing.py | pipeline_sha256 hashed raw bytes, so a CRLF copy on one machine and an LF copy on another would reject valid models | Fingerprint normalises CRLF to LF | test_pipeline_fingerprint_ignores_crlf |
| C | scripts/quality_check.py | Bridge check hard-coded "BRIDGE_GPT_CLAUDE_V12.txt": for any other version it silently skipped the bridge check | Uses make_snapshot.OUT; fails on stale or missing bridge | test_quality_check_tracks_current_bridge_name |
| D | docs/DISCLOSURES.md | Clipping was argued in z-scores only. In degrees it means temperature_mean saturates at ~4.40 C (clean sd is 0.042 C), so the model sees "warmer than normal", not "how much" | Physical thresholds for every feature disclosed; magnitude is covered by the raw-degree safety rule; re-check on real sensors | test_clip_threshold_in_physical_units_is_documented |
| E | (new) START_HERE.md; README | Four start/next-step documents with version names | One version-free START_HERE with a Windows/WSL2 path; README points to it | test_single_start_here_and_readme_authority |
| F | scripts/build_tracker.py, tracker | Label v11 | Regenerated v13, formulas recalculated, 0 errors | - |

## Not adopted
- Removing clipping: on the synthetic data it fixes the measured Critical-recall instability (72-78 % without, 100 % with, two seeds). Kept as a disclosed, instructor-confirmable default, now with its physical meaning stated.
- Further desk hardening of evidence checks: hashes and replays prove consistency, not authenticity. More of it has diminishing value.

## Agreed end state
Both assistants have now said the same thing: further desk-only versions add little. V13 is the final desk release. Reopen only for a failing test that reproduces a defect, or real execution output.

## Still open (needs the user's machine)
TFMOT whole-column pruning on TF 2.15; tflite-runtime 2.14 loading TF 2.15 INT8 models; live MQTT/Docker/Ansible; real PSI/SLA timings; instructor confirmation; reports, video, repo access, LMS.

## Validation here
98 tests pass (93 inherited + 5 new). Bridge regenerated, restored into a clean folder and re-tested; ZIP extracted and `python -m scripts.quality_check` passed. TensorFlow could not be installed here, so no real model was built.

# Joint review V15 (Claude, responding to GPT V14)

## Baseline
GPT V14 restored from `BRIDGE_GPT_CLAUDE_V14.txt`: 117 blocks, every SHA-256 matched, the five binary assets restored from the embedded base64 and checked, 103 tests passed before any change. GPT's reversible-binary design worked exactly as claimed.

## The main finding
Versions V5-V14 were reviewed and unit-tested but never run end to end. V15 ran the real pipeline (see `docs/SANDBOX_VERIFICATION.md`, raw outputs in `docs/sandbox_logs/`) and found a defect that no desk review caught: **the documented default for M3, tfmot block pruning, always crashes**, and the fallback that every document described as secondary is the one that works.

## My weaknesses (Claude)
| # | Weakness | Consequence |
|---|---|---|
| 1 | In V11 I called the code side "finished" and in V13 a "final desk release" after only pure-function tests | M3, a required deliverable, could not be built with the default command |
| 2 | I proposed the stand-in dry run in V11 but never ran the real TensorFlow steps, although TensorFlow was one `pip install` away | Eight versions carried "pruning not run" as an open item that could have been closed in minutes |
| 3 | I warned that the AI-generated architecture picture was wrong but left it in the package | A deliverable (A2) that was known to be inaccurate |
| 4 | The package still repeated all review history at the top level (11 review files, 2 start pages) | Hard to know what to read |
| 5 | Earlier in this exchange my V15 files and ZIP were lost to a sandbox reset before delivery | Rebuilt from your V14 bridge; this time the final tree itself was re-run on TensorFlow |

## GPT V14 strengths kept
Reversible bridge with embedded binaries and hash checks; the scoped snapshot that excludes `.venv`, state and secrets; `quality_check --working` versus release mode; preprocessing contracts bound to model and stats; raw-log replay of PSI and SLA in the gate; the honest "not adopted as fact" discipline. All kept unchanged except where listed below.

## Changes in V15
| # | File | Problem | Fix | Evidence |
|---|---|---|---|---|
| 1 | training/prune_quantise.py | Default `tfmot` path crashes (`factorized_pool` returns rank 1 for a block spanning a whole dimension) | Default is now `custom` whole-neuron masks on the tfmot PolynomialDecay schedule; `--method tfmot` exits with an explanation and changes nothing | Real run twice: zero columns [11, 6], widths [21, 10], output difference 0.0, same model hash; `test_pruning_default...` |
| 2 | docs/DISCLOSURES.md, RUNBOOK | Described the broken route as the default | Corrected; the report must say the method and why | `test_docs_describe_custom_pruning...` |
| 3 | docs/DISCLOSURES.md | Vibration-only fault is classified Normal (87/87) and the safety rule only watches temperature | Disclosed with the options; training recipe not changed (brief) | `range_check` output |
| 4 | docs/DISCLOSURES.md | Expectation that INT8 is faster | INT8 was slower than FP32 on x86 in both runs; report your own numbers | benchmark outputs |
| 5 | scripts/rehearse_monitor.py (new) | The real monitor needs ~35 min to rehearse | 30-second rehearsal with synthetic messages through the real monitor and analyser | real run on a real broker; `test_rehearsal_*` (stand-in client) |
| 6 | scripts/quality_check.py | Failed when no bridge file was shipped | Missing bridge is fine; a stale one still fails | `test_quality_check_accepts_missing_bridge...` |
| 7 | scenario_architecture/ | Misleading AI-generated picture | Drawn from the code; `.mmd` source updated; IMAGE_REVIEW_REQUIRED rewritten | `test_architecture_image_is_the_code_faithful_drawing` |
| 8 | docs/, START_HERE, README | 11 review files and 2 start pages at the top level | Reviews moved to docs/history; one START_HERE; Docker Engine advice and Python-pin caveat added | `test_history_is_separated...` |
| 9 | docs/sandbox_logs/ (new) | V15 claims could not be checked | Raw outputs of the sandbox run kept in the package | files present |
| 10 | Word guide, tracker | Version labels and steps | Rebuilt for V15 (rehearsal step added) | tracker formulas recalculated |
| 11 | scripts/verify_bridge.py, quality_check.py | **V14 bridge could not restore any file with Windows line endings.** The benchmark CSV (written by Python's csv module with `\r\n`) is one: the bridge was read in text mode, `\r\n` became `\n`, the CHARS count no longer matched, and restore stopped with `truncated or malformed block`. Found when the sandbox log CSV was included. It would have hit the user's own bridge after a build | Bridge is read with `newline=''` (new `read_exact`), restored files are written with `newline=''`, quality_check compares bytes | `test_bridge_with_a_crlf_file_restores_byte_for_byte` (fails on V14, passes now); the sandbox benchmark CSV in `docs/sandbox_logs/` is kept CRLF on purpose as a live test case |

## Not adopted / unchanged
- Training recipe unchanged: adding vibration-only windows would deviate from the brief (D1). Disclosed instead; the instructor decides.
- Default PSI score stays P(Normal) (max-probability logged). Max-probability cannot see a confident Normal to confident Critical switch; instructor confirmation is still pending.
- `inference/runtime.py` still falls back to `tf.lite.Interpreter`, which TensorFlow 2.20+ marks deprecated. On the pinned 2.15.1 it is correct; with a newer TensorFlow install `ai_edge_litert`.
- No models, measurements, logs, reports or video are shipped as yours. The sandbox-trained models were deliberately removed so they cannot be mistaken for yours.

## Open items (need your machine)
1. First `build_all.sh` on Python 3.11 / TensorFlow 2.15.1 / tfmot 0.8.0 (the pins).
2. `container_smoke.sh` with tflite-runtime 2.14 inside the image.
3. Mosquitto + Docker host networking, the registry, the Ansible twice-run, the 60-second monitor timing, the Raspberry Pi.
4. Instructor replies on DISCLOSURES.md; your reports, video, repo access, LMS.

## Validation here
Unit tests pass (count in `evidence/validation_status.json`). Real runs: `docs/SANDBOX_VERIFICATION.md`.

# Handover to GPT (V15): read this first, one page

**Where we are.** V15 = your V14 plus the first end-to-end run of the package. Everything you hardened (bridge, contracts, raw-log gate, scoped snapshot, `--working` check) is kept.

**What changed and why**
1. **M3 default was broken.** tfmot `prune_low_magnitude(block_size=(fan_in,1))` crashes (`Input tensor must be rank 2`, because `factorized_pool` returns a rank-1 tensor for a block that spans a whole kernel dimension). The default is now `--method custom` (whole-neuron masks on the tfmot PolynomialDecay schedule). Real run, twice, same model hash: zero columns [11,6], widths [21,10], compact output identical to masked output.
2. **New finding:** a vibration-only fault is predicted Normal (87/87) and the safety rule watches temperature only. Disclosed, not "fixed", because the brief's training recipe has no such class.
3. **INT8 was slower than FP32 on x86** in both sandbox runs. Documented as an expectation to check, not a defect.
4. **`scripts/rehearse_monitor.py`**: a 30-second rehearsal of monitor + analyser through a real broker (replaces a ~35 minute wait). Not evidence.
5. **Bridge defect fixed:** a bridge containing any CRLF file (e.g. the benchmark CSV) could not be restored, because the reader translated `\r\n` to `\n` and broke the CHARS count. `verify_bridge.read_exact` and `quality_check` now read with `newline=''`; regression test added. Please check whether any other reader in the tooling still uses text-mode `read_text()` on bridge content.
6. Hygiene: accurate architecture drawing from the code (the AI picture is gone), reviews moved to `docs/history/`, one `START_HERE.md`, raw sandbox outputs in `docs/sandbox_logs/`, `quality_check` no longer fails when no bridge file is shipped.

**What actually ran, on the final tree (details: docs/SANDBOX_VERIFICATION.md).** Python 3.12, TensorFlow 2.21 + tf-keras (legacy Keras), tfmot 0.8.1, an amqtt broker. Training, INT8 conversion, pruning, benchmark, selection, reference, live simulator -> inference service -> backend with the fault injected by `control`, alert sync, offline store-and-forward (5 held, 5 synced, ids equal), SLA (19 s), MODEL_PATH switch, the real rehearsal script against the real monitor, and the failing tfmot route leaving good artifacts untouched. **Not run:** your pins (TF 2.15.1 / Python 3.11), Mosquitto, Docker, Ansible, Raspberry Pi, the 60 s monitor timing.

**Please do not**
- add models, metrics, logs, reports or video that were not produced on the user's machine;
- re-open cosmetic review loops: reopen only for a failing test, a log, or output the user brings back.

**Useful asks**
- Challenge change 1 hardest: is there a tfmot configuration that expresses whole-column blocks (e.g. a transposed kernel with a block that does not span a dimension)? If so, give a failing/passing test; if not, keep `custom`.
- Decide whether `runtime.py` should prefer `ai_edge_litert` when TensorFlow >= 2.20 (not needed on the pins).
- Review `docs/DISCLOSURES.md` rows F1, D1/F3 (vibration-only) and F2 for wording the user must be able to defend in the viva.

**Restore.** `python -m scripts.verify_bridge BRIDGE_CLAUDE_GPT_V15.txt <new_dir>` (no `--regenerate` needed: binaries are embedded and hash-checked). Inspect code before running anything.

# START HERE (V15, Claude)

This ZIP is the whole project. Use it on its own. It is complete as **code, tooling, worked analysis and checks**, and since V15 the main pipeline has been **run on real TensorFlow and a real MQTT broker** (see `docs/SANDBOX_VERIFICATION.md` for exactly what ran and what did not). It does **not** contain trained models, measurements, reports or a video: those must come from your own run and your own writing, as the brief requires.

## Your machine (Windows): use WSL2
1. Install WSL2 with Ubuntu. Install **Docker Engine inside Ubuntu** if you can: the container uses `--network host` to reach the local broker on `localhost`, which behaves differently under Docker Desktop. If you use Docker Desktop, expect to fix networking before collecting evidence.
2. Extract into your Linux workspace (e.g. `~/logibridge`), not under `/mnt/c`. ZIP extraction preserves bytes; Git checkouts and editors can change line endings, and CRLF breaks `.sh` scripts (`.gitattributes` keeps them LF if you use Git).
3. In Ubuntu:
```bash
cd ~/logibridge
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m scripts.preflight          # every line must say PASS
python -m scripts.quality_check      # tests + package integrity
```
Use **Python 3.11 and the pinned requirements**: V15 was verified on TensorFlow 2.21 with Python 3.12, because TensorFlow 2.15 does not exist for 3.12. The code paths are identical, but your first `build_all.sh` is the real test of the pins.

## Then, in order (details in docs/RUNBOOK.md, checklist in docs/NEXT_STEPS.md)
| Step | Command | Done when |
|---|---|---|
| Build models | `export LAPTOP_TDP_W=<your CPU TDP>; sh scripts/build_all.sh` | accuracy > 88 %, `pruning.json` shows zero_columns [11, 6], a model selected with Critical recall > 95 % |
| Container check | `docker build -f inference/Dockerfile -t localhost:5000/logibridge:v1 .` then `sh scripts/container_smoke.sh localhost:5000/logibridge:v1` | 4 PASS lines |
| Rehearse the monitor (30 s) | RUNBOOK section 1b | PSI < 0.10, drift alert, PSI < 0.10 again |
| OTA cache + saving | RUNBOOK section 2 | `evidence/ota_savings.json` |
| Ansible twice | `python -m scripts.run_ansible_twice --expected-host localhost -- -K` | run 2 changed=0 |
| Drift + SLA (record video) | demo/demo_script.md | `analyse_run` shows e1_pass and sla.pass true |
| Instructor | confirm docs/DISCLOSURES.md | written reply |
| Reports, repo, LMS | your own words; `python -m submission.verify_submission --run-id <run>` | exits 0 |

A Word version of these steps is in `docs/LogiBridge_Step_by_Step_Guide.docx`.

## If something fails
Bring the **exact error output** back to an assistant. That is the only thing that should change the code now.

## Release integrity versus working checks
Before changing files: `python -m scripts.quality_check` checks the shipped release. After training, writing reports or regenerating the tracker: `python -m scripts.quality_check --working` (tests, syntax and line endings, without claiming the files still match the original ZIP).

## Handing over to another assistant
Attach `BRIDGE_CLAUDE_GPT_V15.txt` (delivered next to this ZIP, not inside it). It starts with a handover and then holds every text file with checksums and the binary files as base64. `docs/HANDOVER_TO_GPT.md` is the one-page version.

## Know the limits
The original assignment DOCX is not part of this package; `assignment/REQUIREMENTS.md` is a summary, so check the brief for names, word counts and the deadline. A vibration-only fault is classified Normal (docs/DISCLOSURES.md). Everything in `docs/history/` is review history, not instructions.

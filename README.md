# LogiBridge Joint Consolidated V15 (Claude)

One self-contained repository in the brief's `logibridge/` layout. Use this ZIP on its own; no other ZIP is needed.

## What is complete, and what you still have to do
| Done in this repo | You must still produce (the brief requires your own work) |
|---|---|
| Simulator with live mode switching, preprocessing, synthetic dataset and frozen stats | Run training, conversion and pruning to create M1/M2/M3 (scripts provided) |
| Training, PTQ and pruning scripts with built-in gates (pruning default fixed in V15) | Measured benchmark, Pareto chart, Critical recall on your machine (scripts provided) |
| Inference service, Dockerfile, demo backend, drift monitor, 7-task playbook | Live runs: container smoke, OTA cache, Ansible twice, PSI injection and recovery, SLA |
| Evidence analysers, model selection, results-appendix builder, submission checker | Your phase 1, phase 2 and final report PDFs, written in your own words |
| Worked numbers for A1, B1, B2, E3; architecture figure; report worksheets; demo plan | Your 15-20 minute video; private GitHub repo with instructor access; LMS upload |
| 112 automated tests (all pass); main pipeline run on real TensorFlow and a real broker (docs/SANDBOX_VERIFICATION.md) | Instructor confirmation of the interpretations in docs/DISCLOSURES.md |

No trained models, measurements, reports or video are faked here.

## Start
```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q
export LAPTOP_TDP_W=<your CPU TDP>
sh scripts/build_all.sh
```
Then follow docs/RUNBOOK.md step by step, and demo/demo_script.md for the recording.

## Map
- START_HERE.md: setup and the order of work (read first)
- assignment/REQUIREMENTS.md: every brief task and the file that covers it
- docs/RUNBOOK.md: all commands in order; docs/DISCLOSURES.md: interpretations to state in the report
- docs/SANDBOX_VERIFICATION.md: what was run for real in V15, with results and limits
- docs/JOINT_REVIEW_V15.md and docs/HANDOVER_TO_GPT.md: what changed in V15 and the handover for the other assistant
- docs/LogiBridge_Step_by_Step_Guide.docx: the same steps as START_HERE and the RUNBOOK, as a Word document
- docs/history/: earlier reviews (V4-V14), kept for reference only
- submission/LogiBridge_Tracker.xlsx: criteria checklist and machine-by-machine plan
- scripts/rehearse_monitor.py: 30-second rehearsal of the drift monitor and analyser (not evidence)
- BRIDGE_CLAUDE_GPT_V15.txt (delivered separately): the whole repository as text with checksums, for attaching to a chat

`scenario_architecture/system_architecture.png` is drawn from the implemented code (V15 replaced the earlier AI-generated picture, whose labels did not match it).

## V15 current authority
Read START_HERE.md, then docs/JOINT_REVIEW_V15.md. Use this package alone. Live evidence, reports and video remain yours to produce.

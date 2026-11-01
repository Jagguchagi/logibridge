# Remaining execution and authored submission work

The runtime steps require the appropriate execution environment and access; reports/video require your own substantial work. These were not completed here. Read START_HERE.md (repo root) first.

| # | Do this | Command / where | Done when |
|---|---|---|---|
| 1 | Install and check the environment (Linux or WSL2, Python 3.11, Docker, Ansible) | `pip install -r requirements.txt`; `python -m scripts.preflight` | Every line says PASS |
| 2 | Run the tests and the optional feasibility dry run | `python -m pytest tests -q`; `python -m scripts.dry_run_e1` | Tests pass; dry run shows e1_pass true |
| 3 | Build the three models and measurements | `export LAPTOP_TDP_W=<your CPU TDP>`; `sh scripts/build_all.sh` | Accuracy > 88%; a model is selected with Critical recall > 95% |
| 4 | Build the container and prove all models load in it | `docker build ...`; `sh scripts/container_smoke.sh <image>` | Four PASS lines with hashes |
| 5 | OTA cache demo and 85-truck saving | RUNBOOK section 2 | `evidence/ota_savings.json` |
| 6 | Ansible twice | `python -m scripts.run_ansible_twice --expected-host localhost -- -K` | Run 2 changed=0 |
| 7 | Rehearse the monitor in 30 s (`python -m scripts.rehearse_monitor`), then once live with `--interval 10` | RUNBOOK sections 1b and 4 | You know your real timings |
| 8 | Real drift + SLA run at 60 s, recorded on video | demo/demo_script.md | `analyse_run` shows e1_pass and sla.pass true |
| 9 | Ask the instructor to confirm docs/DISCLOSURES.md (P(Normal), z-score saturation, neuron pruning method, vibration-only gap, conditional stop) | email | Written reply |
| 10 | Write phase 1, phase 2 and final reports yourself | reports/*_template.md, `python -m reports.build_results_appendix` | PDFs in reports/, final named `<group>_LogiEdge_Final.pdf` |
| 11 | Private GitHub repo, instructor added; video link works in incognito | demo/demo_video_link.txt | `python -m submission.verify_submission --run-id <run>` exits 0 |
| 12 | Submit exactly three LMS items before the deadline | LMS | Receipt |

If a step fails, bring the actual error output back; that is the only kind of input that should change the code now.

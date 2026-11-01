# Runbook

One Linux laptop (Ubuntu or WSL2 with Docker Engine) can do everything. Use a new `--run-id` for every recorded run so evidence is never mixed. Track progress in submission/LogiBridge_Tracker.xlsx.

## 1. Set up and build the models
```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m scripts.preflight                  # lists every missing tool; fix FAILs
python -m training.generate_dataset
python -m pytest tests -q                    # all tests must pass
python -m scripts.dry_run_e1                 # optional: stand-in feasibility check (not evidence)
export LAPTOP_TDP_W=<your CPU TDP in W>
sh scripts/build_all.sh                      # M1, M2, M3, diagnostics, benchmark, selection, reference, appendix
```
Stop if accuracy is not above 88% or no variant reaches 95% Critical recall. M3 uses whole-neuron masks by default (`python -m training.prune_quantise`); `--method tfmot` fails with an explanation because the library cannot express whole-column blocks (see docs/DISCLOSURES.md). Check `optimisation/results/pruning.json`: zero_columns should be [11, 6] and compact_widths [21, 10].

## 1b. Fast rehearsal of the drift monitor (about 30 seconds, NOT evidence)
The real monitor needs about 17 minutes to fill and about 17 more to recover. Rehearse the monitor and analyser first, with a broker running:
```bash
python -m monitoring.drift_monitor --run-id rehearse01 --interval 1      # terminal 1
python -m scripts.rehearse_monitor --run-id rehearse01                   # terminal 2: synthetic inference messages
python -m scripts.analyse_run --run-id rehearse01                        # e1_pass is false on purpose (interval 1 s)
```
You should see PSI below 0.10, then `[LOGIBRIDGE DRIFT ALERT]`, then PSI below 0.10 again, and every analyser field true except `interval_ok`. Use a different run id for the real run.

## 2. Container, broker, backend
```bash
docker compose up -d
python -m inference.backend_demo &          # operations-centre stand-in on :8080
docker build -f inference/Dockerfile -t localhost:5000/logibridge:v1 .
sh scripts/container_smoke.sh localhost:5000/logibridge:v1     # must pass
docker push localhost:5000/logibridge:v1
python -m scripts.ota_cache_demo            # D2 cache evidence
docker push localhost:5000/logibridge:cache-v1 && docker push localhost:5000/logibridge:cache-v2
curl -s -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' http://localhost:5000/v2/logibridge/manifests/cache-v1 > evidence/manifest_v1.json
curl -s -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' http://localhost:5000/v2/logibridge/manifests/cache-v2 > evidence/manifest_v2.json
python -m scripts.ota_savings
```

## 3. Deploy with Ansible (E2)
```bash
ansible-galaxy collection install -r deployment/requirements.yml
sh scripts/prepare_registry_demo.sh localhost:5000/logibridge:v1   # optional: makes task 5 pull visibly
python -m scripts.run_ansible_twice --expected-host localhost -- -K
```
Then change the model, regenerate the reference and run the playbook again: task 4 should report changed and the inference payload's model_version should change.

## 4. Live run, drift and SLA (E1, A1)
```bash
python -m data_pipeline.simulator --control --seconds 7200 --run-id demo01
python -m monitoring.drift_monitor --run-id demo01      # wait for PSI < 0.10 (about 17 min to fill 100 inferences)
python -m data_pipeline.control combined                # injection
python -m data_pipeline.control none                    # after the drift alert; recovery takes about 16 min
docker logs logibridge > evidence/demo01/container.log 2>&1
python -m scripts.analyse_run --run-id demo01 --container-log evidence/demo01/container.log
python -m reports.build_results_appendix --run-id demo01
```
The container processes the first run it sees (or the playbook's `run_id`). If you start a new simulator run, restart the container or redeploy with `-e run_id=<new>`; the container prints a warning when it ignores another run.

## 5. Offline store-and-forward (A1)
Stop backend_demo, inject an anomaly, note the outbox shows pending alerts (`docker logs` prints counts every minute), restart backend_demo and watch pending drop to 0. This simulates the backend being unreachable, not a real cellular outage.

## 6. MODEL_PATH switch (D2) without disturbing the drift run
```bash
docker run --rm -d --name lb-t002 --network host -v "$PWD/training/models:/models:ro" \
  -e MODEL_PATH=/models/M3_pruned_int8.tflite -e TRUCK_ID=T002 -e STATE_DIR=/tmp localhost:5000/logibridge:v1
python -m data_pipeline.simulator --truck-id T002 --seconds 90 --run-id t002demo
docker logs lb-t002 | head -3                           # startup line shows the M3 model_version
docker rm -f lb-t002
```

## 7. Sharing with the other assistant
`python -m scripts.make_snapshot` writes the bridge; `python -m scripts.verify_bridge BRIDGE_GPT_CLAUDE_V14.txt /tmp/check --regenerate` proves it restores. `python -m scripts.build_tracker` regenerates the tracker workbook.

## 8. Finish
Write phase1, phase2 and final reports yourself (templates in reports/), export them to reports/*.pdf, record your video (demo/demo_script.md), put the link in demo/demo_video_link.txt, run `python -m submission.verify_submission --run-id demo01`, add the instructor as a GitHub collaborator, and submit the three LMS items.

V14 embeds binary assets: restore without --regenerate reproduces them and checks their hashes. Inspect code before --regenerate; it executes restored modules.

## V12 migration
Read START_HERE.md. Rebuild models and keep generated .pipeline.json sidecars with them. Both model and sidecar share the final Docker layer. Reference/benchmark/live evidence must be regenerated after preprocessing changes. Final submission now replays SLA from evidence/<run>/container.log, not only the saved PASS flag.

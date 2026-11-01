# D3 10-stage pipeline mapping (DRAFT)

Replace the stage names with the exact ten from your Module 4 slides, and rewrite each line in your own words.

1. Problem definition: classify cargo state Normal/Warning/Critical on the truck within 90 s, offline.
2. Data collection: seeded simulator publishing temperature, vibration RMS and door events to local Mosquitto.
3. Data preparation: 5-sample filter, 30 s windows every 10 s, frozen 10-minute normalisation stats.
4. Labelling: simulator mode gives the label (20/15/15 minutes); conflict with physical thresholds disclosed.
5. Model training: 6-32-16-3 ReLU MLP, last 20% of each class held out with a 4-window purge.
6. Evaluation: validation accuracy (> 88%), confusion matrix, Critical recall.
7. Optimisation: full-INT8 PTQ (M2) and 35% whole-neuron pruning plus INT8 (M3), benchmarked.
8. Packaging: python:3.11-slim container, dependencies before the model layer, MODEL_PATH switch.
9. Deployment: seven-task Ansible playbook from a local registry, idempotent on rerun.
10. Monitoring: PSI on confidence over the last 100 inferences; durable alert outbox synced on reconnect.

# Start here: V12 audited working package

Use this ZIP alone. It includes the full source, original binary assets, synthetic dataset, tracker, historical reviews, V12 audit and reproducible local checks. It is NOT an offline environment: install the declared dependencies. It is NOT a completed submission.

## Local verification
From the extracted logibridge/ root:

```bash
python -m scripts.quality_check
```

This checks local source/tests/package consistency only. It does not certify TensorFlow, TFLite, MQTT, Docker, Ansible or hardware.

## Real execution
Follow docs/RUNBOOK.md. Rebuild models with scripts/build_all.sh before using this version. Each Keras/TFLite artifact now carries a generated .pipeline.json sidecar; inference, benchmarking and reference creation reject missing/stale contracts. Do not attach a new sidecar to an old model to bypass rebuilding.

Keep the model and sidecar together. The final Docker COPY includes both; Ansible task 2 copies both plus stats. Rerun smoke and live evidence. Save the canonical container log:

```bash
docker logs logibridge > evidence/<run>/container.log 2>&1
python -m scripts.analyse_run --run-id <run> --container-log evidence/<run>/container.log
python -m submission.verify_submission --run-id <run>
```

Replace <run> with the actual run ID. The final gate now recomputes both PSI and SLA from raw logs and checks artifact compatibility. It still cannot certify authenticity, video content, report authorship or LMS compliance.

## Share with Claude
Attach BRIDGE_CLAUDE_GPT_V13.txt. It includes all text source, the V12 audit, tests, status and binary inventory. It does not embed the architecture PNG or workbook bytes; those are in this ZIP. Inspect the source before --regenerate. Read docs/JOINT_REVIEW_V12.md first, not the historical 'final' labels.

## Honest stopping point
93 local tests passed here. Real training/conversion, runtime and deployment remain unrun because the required libraries/tools/hardware were unavailable. The clipping default is experimental and requires instructor confirmation plus an independent holdout. This package fixes demonstrated defects; it is not a promise of a permanently bug-free system.

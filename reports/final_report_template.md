# GROUPNO LogiEdge Final Report (worksheet - write in your own words)

Word count 2,500-3,000 excluding figures, tables and references. The section ranges add to 2,000-2,500, so aim for the upper end of each and confirm with the instructor how they are counted.
Front matter: group number, names/IDs, private repo URL, video link, commit hash, AI-assistance disclosure.

## 1. FreightBridge deployment context (400-500)
Four constraints with numbers (constraint_analysis.md), Constraint Triangle and choice (hardware_justification.md), architecture figure, arithmetic intensity and roofline result.

## 2. Sensor pipeline and MQTT design (500-600)
Topic tree figure, QoS per topic, preprocessing rationale, table of accuracy with correct vs +3 sigma stats (benchmark CSV), fusion choice vs alternatives.

## 3. Model deployment and pipeline mapping (400-500)
Ten stages (pipeline_mapping.md, with your course's names), Docker layer-cache result, 85-truck saving (ota_savings.json), OTA recommendation (ota_strategy.md).

## 4. Optimisation and Pareto analysis (400-500)
15-cell table (results_appendix.md), annotated Pareto chart, Critical recall of the chosen model, recommendation with the 90 s budget and device memory.

## 5. MLOps monitoring and reflection (300-400)
PSI before/during/after (analysis.json), drift type (covariate drift showing up as prediction drift), Ansible changed=0, one genuine difficulty you hit, one architectural change you would make.

## Disclosures
Summarise docs/DISCLOSURES.md.

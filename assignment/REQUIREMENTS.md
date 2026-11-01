# Assignment requirements (summary of the attached brief)

Source: LogiEdge_MiniProject_Problem_Statement - Student.docx (AIML ZG535, EC-I, 30 marks). Check the course page for the deadline. This is a summary; the brief is authoritative.

| Task | Requirement | Where in this repo |
|---|---|---|
| A1 | 350-500 words: latency (1 °C/min, 90 s SLA, rural RTT), bandwidth (1 Hz temp, 500 Hz 3-axis vibration, INR 0.10/MB), connectivity (35-90 min gaps x 7), privacy | scenario_architecture/constraint_analysis.md |
| A2 | Architecture diagram: edge node, sensors, local MQTT, inference, local alert log, uplink, backend | scenario_architecture/system_architecture.png and .mmd |
| B1 | Constraint Triangle for Pi 5+HAT (INR 15k, 7.5 W), Jetson (INR 45k, 15 W), STM32H7 (INR 3.5k, 0.4 W); 90 s, 10 W, 85/265 trucks | hardware/hardware_justification.md |
| B2 | Arithmetic intensity, ridge point, bound, optimisation (45 MFLOP, 18 MB, 16 GFLOP/s, 12 GB/s) | hardware/hardware_justification.md |
| C1 | Simulator, 3 streams, --anomaly none/temp_drift/vibration/combined, local Mosquitto | data_pipeline/simulator.py |
| C2 | 5-sample MA; 30 s window / 10 s step; 6 features; frozen 10-min stats; correct vs +3 sigma stats experiment | data_pipeline/preprocessing.py; optimisation/benchmark.py |
| C3 | Feature-level fusion, justified against data- and decision-level | preprocessing.py; data_pipeline/mqtt_architecture.md |
| C4 | Topic tree figure and QoS per topic (report Section 2) | data_pipeline/mqtt_architecture.md |
| D1 | 20/15/15 min dataset; 32-16 ReLU MLP; 20% validation accuracy > 88% | training/ |
| D2 | python:3.11-slim; pip before model COPY; MODEL_PATH switch; inference topic; layer-cache demo; 85-truck saving | inference/Dockerfile; scripts/ota_cache_demo.py, ota_savings.py |
| D3 | All 10 Module 4 pipeline stages, 1-2 system-specific sentences each | reports/pipeline_mapping.md (replace with exact course stage names) |
| E1 | PSI on confidence: 300 clean windows, 4 bins, last 100 every 60 s, alert > 0.25, combined injection crosses within 5 min, recovery < 0.10, on video | monitoring/drift_monitor.py; scripts/analyse_run.py |
| E2 | Exactly 7 Ansible tasks; second unchanged run changed=0; both on video | deployment/logibridge_deploy.yml; scripts/run_ansible_twice.py |
| E3 | Full / canary / shadow cost and recommendation | deployment/ota_strategy.md |
| F1 | M1 FP32; M2 full INT8 >= 200 calibration samples; M3 35% structured pruning (PolynomialDecay) + INT8 | training/ |
| F2 | Mean and p95 latency (200 runs after 10 warm-up), size KB, accuracy, energy (psutil CPU% x TDP) | optimisation/benchmark.py |
| F3 | Recommendation: 90 s budget, device flash/SRAM, Critical recall > 95% | scripts/select_model.py; report Section 4 |

Deliverables (all three mandatory; a missing one caps the mark at 18): private GitHub repo with instructor as collaborator; your own 15-20 minute demo video ("anyone with the link", tested in incognito; link in demo/demo_video_link.txt and the report); final report PDF, 2,500-3,000 words, named GROUPNO_LogiEdge_Final.pdf. Late: -2 marks per day, max -10; not accepted after 5 days.

Rubric: architecture & hardware 7, pipeline & MQTT 7, training/conversion/Docker 6, optimisation 5, MLOps 3, report quality 2.

Integrity: you must be able to explain and run every file in a viva; the video must show your own system; an AI-generated report without substantial original analysis and measured data is misconduct.

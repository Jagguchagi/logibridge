# A1 constraint analysis: worked numbers and points to cover

These are calculations and facts for your own 350-500 word analysis. Write the analysis yourself.

## Latency
- A refrigeration failure warms cargo by about 1 °C per minute, so 90 seconds allows about 1.5 °C of warming before the alert must be raised.
- During the brief's 35-90 minute coverage gaps, a cloud-only system cannot classify anything, so it cannot meet a 90-second SLA at all. Even with coverage, rural round-trip times are variable; cite a measured or published figure if you use one (none is supplied here).
- The edge pipeline's worst-case detection budget: a fault must appear in a 30 s window (up to 30 s), plus up to 10 s until the next window is emitted, plus a few seconds for the 5-sample filter. That leaves roughly 45 s for inference, publishing and the local alert. Measure the real fault-to-alert time with `scripts/analyse_run.py`.

## Bandwidth (raw, assuming float32 values, excluding timestamps, door events and protocol overhead)
- Temperature: 1 Hz x 4 B = 4 B/s. Vibration: 500 Hz x 3 axes x 4 B = 6,000 B/s. Total 6,004 B/s.
- Per day: 6,004 x 86,400 = 518,745,600 B = 518.7 MB (decimal), costing INR 51.87 per truck per day at INR 0.10/MB, or INR 4,409 per day for 85 trucks.
- Edge-processed: only alerts and periodic summaries leave the truck. Use your measured alert count and payload size for the comparison (for illustration only: 100 alerts of 512 B = 0.05 MB/day, about INR 0.005).
- Note that the simulator publishes 0.5 Hz vibration RMS, not the raw 500 Hz waveform used in this calculation.

## Connectivity
- Cloud-only during a gap: no classification and no alert; at best the data is buffered and arrives too late.
- This design: MQTT broker, inference and the alert log all run on the truck. Alerts are written to a durable SQLite outbox and raised locally immediately; they are synced with UUID acknowledgement when coverage returns, and the backend deduplicates retries. Remote notification is still delayed until coverage returns; say so.

## Privacy
- On-device inference means raw sensor streams never leave the truck, which shrinks what could be intercepted or misused, and supports contractual data-minimisation commitments.
- It is not proof on its own: production also needs authenticated MQTT with ACLs, TLS on the uplink, encrypted storage and audit logs. The lab broker and backend here are anonymous and unencrypted.

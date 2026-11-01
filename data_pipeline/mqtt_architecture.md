# C3/C4 MQTT topics, QoS and fusion

| Topic | Rate | QoS | Why |
|---|---|---|---|
| logibridge/trucks/{id}/sensors/temperature | 1 Hz | 0 | High rate, replaceable; a lost sample is covered by the 25-of-30 window check |
| logibridge/trucks/{id}/sensors/vibration_rms | 0.5 Hz | 0 | Same; window needs 12 of 15 samples |
| logibridge/trucks/{id}/sensors/door_event | event | 1 | Rare and must not be lost; duplicates are ignored by timestamp |
| logibridge/trucks/{id}/inference | every 10 s | 1 | Feeds the drift monitor; duplicates ignored |
| logibridge/trucks/{id}/control/anomaly | manual | 1 | Lab-only: switches the simulator mode mid-run |

Periodic telemetry is not retained. Alert delivery to the operations centre does not rely on MQTT QoS: alerts go into a durable outbox and are marked sent only after the backend echoes the alert UUID.

## Preprocessing
5-sample moving average per stream, 30 s windows every 10 s, a window is emitted only when both streams have reached its end time. Six features: temperature mean, standard deviation and rate of change (°C/min, least-squares slope); vibration RMS, peak and kurtosis of the filtered RMS series. Normalisation uses means and standard deviations from a separate 10-minute clean run, saved once as training_stats.npy and never recomputed live.

## Fusion choice
Feature-level fusion: each sensor is summarised independently over the same window, then the six values are concatenated. Data-level fusion would need resampling 1 Hz and 0.5 Hz streams onto one timeline (or the raw 500 Hz waveform) and a bigger model. Decision-level fusion would need two separately trained and calibrated models and a rule to resolve disagreements, and would lose the interaction between rising temperature and compressor vibration that defines the Critical class.

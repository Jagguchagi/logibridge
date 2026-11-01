# B1/B2 hardware selection: worked numbers

Prices and power are the brief's figures, not current quotes.

| Option | INR / truck | 85 trucks | 265 trucks | Power | vs 10 W AI budget |
|---|---:|---:|---:|---:|---|
| Raspberry Pi 5 (8 GB) + AI HAT+ | 15,000 | 12.75 lakh | 39.75 lakh | 7.5 W | Within |
| Jetson Orin Nano Super | 45,000 | 38.25 lakh | 1.19 crore | 15 W | Exceeds |
| STM32H7 custom MCU | 3,500 | 2.98 lakh | 9.28 lakh | 0.4 W | Well within |

Points for your Constraint Triangle argument (use your course's exact vertex names):
- Jetson: far more compute than a 6-input MLP needs, breaks the 10 W budget, and costs three times the Pi.
- MCU: cheapest and lowest power, but no Linux, so no Docker, Mosquitto or Ansible as the brief requires; it needs a firmware toolchain (e.g. TFLite Micro) and a different update path. Check model and runtime size against the specific part's datasheet SRAM/flash.
- Pi 5: meets the 10 W budget with margin, runs the full Linux stack the brief uses, and the 6-32-16-3 MLP (803 parameters) runs comfortably on its CPU. The Hailo HAT is not used by this code.
- Latency: the 90 s SLA leaves roughly 45 s after windowing. The Pi and Jetson run Linux and can be benchmarked with this repo; the MCU's latency and memory fit are NOT measured here and must come from the part's datasheet or a TFLite Micro build. Measure, do not assume.

## B2 Roofline (brief's hypothetical workload, not this MLP)
- Arithmetic intensity = 45 MFLOP / 18 MB = 2.5 FLOP/byte.
- Ridge point = 16 GFLOP/s / 12 GB/s = 1.33 FLOP/byte.
- 2.5 > 1.33, so the workload is compute-bound. Attainable throughput = min(16, 12 x 2.5) = 16 GFLOP/s, giving a lower bound of 45e6 / 16e9 = 2.8 ms per inference.
- Optimisation that helps a compute-bound model: reduce FLOPs (structured pruning that physically removes neurons) and use faster integer arithmetic (INT8 with SIMD). Reducing memory traffic alone would not help.

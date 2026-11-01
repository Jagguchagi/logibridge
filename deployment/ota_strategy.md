# E3 OTA strategy: worked numbers

Brief: 280 KB INT8 model (0.28 MB decimal), 85 trucks, INR 0.10/MB, update every 6 weeks.

| Strategy | Downloads per cycle | MB | INR |
|---|---|---:|---:|
| Full replacement | 85 x new model | 23.8 | 2.38 |
| Canary (10, then 75) | 10 + 75 x new model | 2.8 + 21.0 | 0.28 + 2.10 = 2.38 |
| Shadow mode | 85 x new model (old stays active) | 23.8 | 2.38 |

Model download cost is the same for all three; the differences are risk and side costs. Shadow mode also needs extra compute and any comparison data uploaded (state your assumption), and does not protect cargo until promoted. Full replacement exposes all 85 trucks to a bad model at once. Canary limits exposure to 10 trucks while confirming Critical recall and alert rates, and with the previous model kept on each truck, rollback needs no download. Rural coverage gaps mean some trucks will update late under any strategy; the playbook is idempotent so re-running it is safe.

Cost per year: about 8.7 cycles x INR 2.38 = about INR 21 for the fleet; bandwidth cost is negligible, safety is the deciding factor.

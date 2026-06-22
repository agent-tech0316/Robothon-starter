# Fleet Stress Benchmark

This benchmark is a fast-forward warehouse digital-twin stress test. It does not render the UI and does not step MuJoCo every second. Instead, it uses a minute-resolution benchmark-only traffic model calibrated from the runtime layout, robot fleet, SKU weights, pick difficulty, tile distances, and planner-off versus local-planner behavior.

## Benchmark Scale

- Scenario matrix: 54 scenarios = 3 load levels x 3 SKU mixes x 3 pick difficulty levels x 2 congestion modes
- Paired planner runs: 54 planner-off/local comparisons
- Horizon: 6.0 simulated warehouse hours per scenario
- Total simulated warehouse hours: 324.0
- Total simulated robot-hours: 2916.0
- Tick model: 1-minute fast-forward ticks, no browser or video rendering
- Congestion shock coverage: 27 nominal scenarios + 27 aisle-surge scenarios

## Headline Results

- Safety pass rate: 100.0% (54 / 54 paired scenarios)
- Collision violations: 0
- Tile-lock overlap violations: 0
- Average planner throughput uplift: 30.74%
- Best planner throughput uplift: 97.42%
- Local planner improved throughput in 48 / 54 scenarios
- Average local-planner throughput: 311.12 orders/hour
- Average planner-off throughput: 227.15 orders/hour

## Why This Matters

The main submission already shows 9 AEGIS robots sharing aisles with zero collisions. This benchmark adds the missing stress-test evidence: the same fleet is evaluated across load, SKU weight mix, pick difficulty, and aisle-surge congestion without relying on a UI recording. That turns the project from a single demo into a repeatable warehouse optimization benchmark.

## Scenario Pair Summary

| Scenario | Shock | Off THR | Local THR | Uplift | Local completion | Safety |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| high_balanced_easy_aisle_surge | aisle_surge | 270.0 | 401.33 | 48.64% | 61.85% | pass |
| high_balanced_easy_nominal | nominal | 276.67 | 537.33 | 94.21% | 99.51% | pass |
| high_balanced_hard_aisle_surge | aisle_surge | 256.33 | 322.67 | 25.88% | 49.68% | pass |
| high_balanced_hard_nominal | nominal | 270.83 | 365.33 | 34.89% | 67.65% | pass |
| high_balanced_nominal_aisle_surge | aisle_surge | 270.0 | 374.67 | 38.77% | 57.67% | pass |
| high_balanced_nominal_nominal | nominal | 273.83 | 421.0 | 53.75% | 77.96% | pass |
| high_heavy_easy_aisle_surge | aisle_surge | 270.0 | 375.0 | 38.89% | 57.83% | pass |
| high_heavy_easy_nominal | nominal | 271.33 | 535.67 | 97.42% | 99.2% | pass |
| high_heavy_hard_aisle_surge | aisle_surge | 236.17 | 294.67 | 24.77% | 45.45% | pass |
| high_heavy_hard_nominal | nominal | 270.0 | 337.0 | 24.81% | 62.41% | pass |
| high_heavy_nominal_aisle_surge | aisle_surge | 265.67 | 341.33 | 28.48% | 52.54% | pass |
| high_heavy_nominal_nominal | nominal | 270.5 | 393.83 | 45.59% | 72.93% | pass |
| high_light_easy_aisle_surge | aisle_surge | 270.33 | 413.0 | 52.78% | 63.69% | pass |
| high_light_easy_nominal | nominal | 284.0 | 539.33 | 89.9% | 99.88% | pass |
| high_light_hard_aisle_surge | aisle_surge | 265.17 | 336.67 | 26.96% | 51.9% | pass |
| high_light_hard_nominal | nominal | 278.0 | 380.0 | 36.69% | 70.37% | pass |
| high_light_nominal_aisle_surge | aisle_surge | 270.0 | 402.67 | 49.14% | 61.96% | pass |
| high_light_nominal_nominal | nominal | 280.83 | 465.17 | 65.64% | 86.14% | pass |
| low_balanced_easy_aisle_surge | aisle_surge | 152.67 | 153.83 | 0.76% | 100.0% | pass |
| low_balanced_easy_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_balanced_hard_aisle_surge | aisle_surge | 154.0 | 154.67 | 0.44% | 99.89% | pass |
| low_balanced_hard_nominal | nominal | 119.67 | 119.83 | 0.13% | 99.86% | pass |
| low_balanced_nominal_aisle_surge | aisle_surge | 154.33 | 152.5 | -1.19% | 99.89% | pass |
| low_balanced_nominal_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_heavy_easy_aisle_surge | aisle_surge | 154.17 | 152.67 | -0.97% | 100.0% | pass |
| low_heavy_easy_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_heavy_hard_aisle_surge | aisle_surge | 153.5 | 153.5 | 0.0% | 99.89% | pass |
| low_heavy_hard_nominal | nominal | 119.83 | 119.83 | 0.0% | 99.86% | pass |
| low_heavy_nominal_aisle_surge | aisle_surge | 152.67 | 155.0 | 1.53% | 99.89% | pass |
| low_heavy_nominal_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_light_easy_aisle_surge | aisle_surge | 154.0 | 154.17 | 0.11% | 100.0% | pass |
| low_light_easy_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_light_hard_aisle_surge | aisle_surge | 153.83 | 153.33 | -0.33% | 100.0% | pass |
| low_light_hard_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_light_nominal_aisle_surge | aisle_surge | 153.17 | 152.67 | -0.33% | 100.0% | pass |
| low_light_nominal_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| medium_balanced_easy_aisle_surge | aisle_surge | 272.0 | 454.67 | 67.16% | 100.0% | pass |
| medium_balanced_easy_nominal | nominal | 285.0 | 387.5 | 35.96% | 100.0% | pass |
| medium_balanced_hard_aisle_surge | aisle_surge | 268.67 | 347.33 | 29.28% | 76.39% | pass |
| medium_balanced_hard_nominal | nominal | 275.67 | 380.0 | 37.85% | 98.49% | pass |
| medium_balanced_nominal_aisle_surge | aisle_surge | 270.5 | 453.5 | 67.65% | 99.38% | pass |
| medium_balanced_nominal_nominal | nominal | 282.33 | 387.67 | 37.31% | 99.96% | pass |
| medium_heavy_easy_aisle_surge | aisle_surge | 269.83 | 448.0 | 66.03% | 98.82% | pass |
| medium_heavy_easy_nominal | nominal | 278.67 | 387.17 | 38.93% | 100.0% | pass |
| medium_heavy_hard_aisle_surge | aisle_surge | 259.33 | 315.33 | 21.59% | 69.43% | pass |
| medium_heavy_hard_nominal | nominal | 270.0 | 343.17 | 27.1% | 88.64% | pass |
| medium_heavy_nominal_aisle_surge | aisle_surge | 269.67 | 382.83 | 41.96% | 84.2% | pass |
| medium_heavy_nominal_nominal | nominal | 273.83 | 386.17 | 41.03% | 99.91% | pass |
| medium_light_easy_aisle_surge | aisle_surge | 271.67 | 453.5 | 66.93% | 100.0% | pass |
| medium_light_easy_nominal | nominal | 296.5 | 387.33 | 30.63% | 100.0% | pass |
| medium_light_hard_aisle_surge | aisle_surge | 270.67 | 373.17 | 37.87% | 81.83% | pass |
| medium_light_hard_nominal | nominal | 283.83 | 373.67 | 31.65% | 96.68% | pass |
| medium_light_nominal_aisle_surge | aisle_surge | 270.83 | 455.33 | 68.12% | 99.89% | pass |
| medium_light_nominal_nominal | nominal | 287.0 | 385.67 | 34.38% | 100.0% | pass |

## Reproduce

```bash
python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 54
```

Outputs:

- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_summary.json`
- `submissions/warehouse_quadbot_atomic_demos/FLEET_STRESS_BENCHMARK.md`

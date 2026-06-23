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
- Average planner throughput uplift: 32.92%
- Best planner throughput uplift: 99.63%
- Local planner improved throughput in 35 / 54 scenarios
- Average local-planner throughput: 362.32 orders/hour
- Average planner-off throughput: 267.16 orders/hour

## Why This Matters

The main submission shows 9 AEGIS robots sharing aisles with zero collisions, and this benchmark can also scale the same layout to 9 heterogeneous robots. The stress test evaluates load, SKU weight mix, pick difficulty, aisle-surge congestion, and robot end-effector specialization without relying on a UI recording. That turns the project from a single demo into a repeatable warehouse optimization benchmark.

## Scenario Pair Summary

| Scenario | Shock | Off THR | Local THR | Uplift | Local completion | Safety |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| high_balanced_easy_aisle_surge | aisle_surge | 273.83 | 540.0 | 97.2% | 83.23% | pass |
| high_balanced_easy_nominal | nominal | 373.5 | 536.33 | 43.6% | 99.32% | pass |
| high_balanced_hard_aisle_surge | aisle_surge | 270.67 | 519.17 | 91.81% | 79.93% | pass |
| high_balanced_hard_nominal | nominal | 297.67 | 533.33 | 79.17% | 98.77% | pass |
| high_balanced_nominal_aisle_surge | aisle_surge | 272.33 | 538.33 | 97.68% | 82.86% | pass |
| high_balanced_nominal_nominal | nominal | 328.0 | 535.0 | 63.11% | 99.07% | pass |
| high_heavy_easy_aisle_surge | aisle_surge | 270.5 | 540.0 | 99.63% | 83.27% | pass |
| high_heavy_easy_nominal | nominal | 318.67 | 517.5 | 62.39% | 95.83% | pass |
| high_heavy_hard_aisle_surge | aisle_surge | 270.0 | 485.67 | 79.88% | 74.91% | pass |
| high_heavy_hard_nominal | nominal | 276.67 | 507.83 | 83.55% | 94.04% | pass |
| high_heavy_nominal_aisle_surge | aisle_surge | 270.33 | 533.33 | 97.29% | 82.09% | pass |
| high_heavy_nominal_nominal | nominal | 298.33 | 525.33 | 76.09% | 97.28% | pass |
| high_light_easy_aisle_surge | aisle_surge | 284.17 | 540.0 | 90.03% | 83.27% | pass |
| high_light_easy_nominal | nominal | 484.83 | 539.33 | 11.24% | 99.88% | pass |
| high_light_hard_aisle_surge | aisle_surge | 272.17 | 537.83 | 97.61% | 82.91% | pass |
| high_light_hard_nominal | nominal | 315.33 | 524.0 | 66.18% | 97.04% | pass |
| high_light_nominal_aisle_surge | aisle_surge | 274.17 | 539.5 | 96.78% | 83.02% | pass |
| high_light_nominal_nominal | nominal | 361.0 | 538.5 | 49.17% | 99.72% | pass |
| low_balanced_easy_aisle_surge | aisle_surge | 153.0 | 153.83 | 0.54% | 100.0% | pass |
| low_balanced_easy_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_balanced_hard_aisle_surge | aisle_surge | 154.33 | 154.83 | 0.32% | 100.0% | pass |
| low_balanced_hard_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_balanced_nominal_aisle_surge | aisle_surge | 154.33 | 152.67 | -1.08% | 100.0% | pass |
| low_balanced_nominal_nominal | nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_heavy_easy_aisle_surge | aisle_surge | 154.5 | 152.67 | -1.18% | 100.0% | pass |
| low_heavy_easy_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_heavy_hard_aisle_surge | aisle_surge | 153.83 | 153.67 | -0.1% | 100.0% | pass |
| low_heavy_hard_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_heavy_nominal_aisle_surge | aisle_surge | 152.83 | 155.17 | 1.53% | 100.0% | pass |
| low_heavy_nominal_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_light_easy_aisle_surge | aisle_surge | 154.5 | 154.17 | -0.21% | 100.0% | pass |
| low_light_easy_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_light_hard_aisle_surge | aisle_surge | 154.33 | 153.33 | -0.65% | 100.0% | pass |
| low_light_hard_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| low_light_nominal_aisle_surge | aisle_surge | 153.33 | 152.67 | -0.43% | 100.0% | pass |
| low_light_nominal_nominal | nominal | 120.0 | 120.0 | 0.0% | 100.0% | pass |
| medium_balanced_easy_aisle_surge | aisle_surge | 454.67 | 454.67 | 0.0% | 100.0% | pass |
| medium_balanced_easy_nominal | nominal | 387.17 | 387.5 | 0.09% | 100.0% | pass |
| medium_balanced_hard_aisle_surge | aisle_surge | 276.0 | 454.5 | 64.67% | 99.96% | pass |
| medium_balanced_hard_nominal | nominal | 387.67 | 385.83 | -0.47% | 100.0% | pass |
| medium_balanced_nominal_aisle_surge | aisle_surge | 297.67 | 456.17 | 53.25% | 99.96% | pass |
| medium_balanced_nominal_nominal | nominal | 387.0 | 387.67 | 0.17% | 99.96% | pass |
| medium_heavy_easy_aisle_surge | aisle_surge | 286.67 | 452.33 | 57.79% | 99.78% | pass |
| medium_heavy_easy_nominal | nominal | 385.67 | 387.0 | 0.34% | 99.96% | pass |
| medium_heavy_hard_aisle_surge | aisle_surge | 272.5 | 453.67 | 66.48% | 99.89% | pass |
| medium_heavy_hard_nominal | nominal | 297.83 | 387.0 | 29.94% | 99.96% | pass |
| medium_heavy_nominal_aisle_surge | aisle_surge | 276.0 | 454.17 | 64.55% | 99.89% | pass |
| medium_heavy_nominal_nominal | nominal | 386.0 | 386.5 | 0.13% | 100.0% | pass |
| medium_light_easy_aisle_surge | aisle_surge | 454.67 | 453.5 | -0.26% | 100.0% | pass |
| medium_light_easy_nominal | nominal | 386.17 | 387.33 | 0.3% | 100.0% | pass |
| medium_light_hard_aisle_surge | aisle_surge | 285.33 | 455.83 | 59.76% | 99.96% | pass |
| medium_light_hard_nominal | nominal | 387.33 | 386.5 | -0.21% | 100.0% | pass |
| medium_light_nominal_aisle_surge | aisle_surge | 454.83 | 455.67 | 0.18% | 99.96% | pass |
| medium_light_nominal_nominal | nominal | 386.33 | 385.67 | -0.17% | 100.0% | pass |

## Reproduce

```bash
python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 54
```

Outputs:

- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_summary.json`
- `submissions/warehouse_quadbot_atomic_demos/FLEET_STRESS_BENCHMARK.md`

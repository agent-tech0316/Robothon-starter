# Fleet Stress Benchmark

This benchmark is a fast-forward warehouse digital-twin stress test. It does not render the UI and does not step MuJoCo every second. Instead, it uses a minute-resolution benchmark-only traffic model calibrated from the runtime layout, robot fleet, SKU weights, pick difficulty, tile distances, and planner-off versus local-planner behavior.

## Benchmark Scale

- Scenario matrix: 27 scenarios = 3 load levels x 3 SKU mixes x 3 pick difficulty levels
- Paired planner runs: 27 planner-off/local comparisons
- Horizon: 6.0 simulated warehouse hours per scenario
- Total simulated warehouse hours: 162.0
- Total simulated robot-hours: 1458.0
- Tick model: 1-minute fast-forward ticks, no browser or video rendering

## Headline Results

- Safety pass rate: 100.0% (27 / 27 paired scenarios)
- Collision violations: 0
- Tile-lock overlap violations: 0
- Average planner throughput uplift: 31.72%
- Best planner throughput uplift: 93.99%
- Local planner improved throughput in 27 / 27 scenarios
- Average local-planner throughput: 313.1 orders/hour
- Average planner-off throughput: 225.12 orders/hour

## Why This Matters

The main submission already shows 9 AEGIS robots sharing aisles with zero collisions. This benchmark adds the missing stress-test evidence: the same fleet is evaluated across load, SKU weight mix, and pick difficulty variations without relying on a UI recording. That turns the project from a single demo into a repeatable warehouse optimization benchmark.

## Scenario Pair Summary

| Scenario | Off THR | Local THR | Uplift | Local completion | Safety |
| --- | ---: | ---: | ---: | ---: | --- |
| high_balanced_easy | 277.17 | 537.67 | 93.99% | 99.57% | pass |
| high_balanced_hard | 270.5 | 368.83 | 36.35% | 68.3% | pass |
| high_balanced_nominal | 273.83 | 419.17 | 53.08% | 77.62% | pass |
| high_heavy_easy | 270.83 | 510.0 | 88.31% | 94.44% | pass |
| high_heavy_hard | 269.83 | 339.67 | 25.88% | 62.9% | pass |
| high_heavy_nominal | 270.17 | 393.83 | 45.77% | 72.93% | pass |
| high_light_easy | 282.5 | 539.33 | 90.91% | 99.88% | pass |
| high_light_hard | 278.67 | 376.83 | 35.22% | 69.78% | pass |
| high_light_nominal | 281.83 | 461.33 | 63.69% | 85.43% | pass |
| low_balanced_easy | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_balanced_hard | 119.67 | 119.83 | 0.13% | 99.86% | pass |
| low_balanced_nominal | 119.67 | 120.0 | 0.28% | 100.0% | pass |
| low_heavy_easy | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_heavy_hard | 119.67 | 119.83 | 0.13% | 99.86% | pass |
| low_heavy_nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_light_easy | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_light_hard | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| low_light_nominal | 119.83 | 120.0 | 0.14% | 100.0% | pass |
| medium_balanced_easy | 284.67 | 387.0 | 35.95% | 100.0% | pass |
| medium_balanced_hard | 275.5 | 380.33 | 38.05% | 98.4% | pass |
| medium_balanced_nominal | 278.67 | 385.33 | 38.27% | 99.96% | pass |
| medium_heavy_easy | 278.33 | 386.67 | 38.93% | 100.0% | pass |
| medium_heavy_hard | 270.0 | 348.83 | 29.2% | 90.33% | pass |
| medium_heavy_nominal | 274.5 | 387.17 | 41.05% | 100.0% | pass |
| medium_light_easy | 297.0 | 390.0 | 31.31% | 100.0% | pass |
| medium_light_hard | 282.33 | 375.5 | 33.0% | 96.99% | pass |
| medium_light_nominal | 284.0 | 386.5 | 36.09% | 100.0% | pass |

## Reproduce

```bash
python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 27
```

Outputs:

- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_summary.json`
- `submissions/warehouse_quadbot_atomic_demos/FLEET_STRESS_BENCHMARK.md`

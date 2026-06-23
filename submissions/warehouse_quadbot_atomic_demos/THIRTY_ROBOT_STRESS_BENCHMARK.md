# 30-Robot Heterogeneous Fleet Stress Benchmark

This benchmark is a fast-forward warehouse digital-twin stress test. It does not render the UI and does not step MuJoCo every second. Instead, it uses a minute-resolution benchmark-only traffic model calibrated from the runtime layout, robot fleet, SKU weights, pick difficulty, tile distances, and planner-off versus local-planner behavior.

## Benchmark Scale

- Scenario matrix: 54 scenarios = 3 load levels x 3 SKU mixes x 3 pick difficulty levels x 2 congestion modes
- Paired planner runs: 54 planner-off/local comparisons
- Horizon: 6.0 simulated warehouse hours per scenario
- Total simulated warehouse hours: 324.0
- Total simulated robot-hours: 9720.0
- Fleet size: 30 AEGIS quadrupeds
- End-effector mix: 8 parallel grippers, 9 dexterous hands, 8 electromagnets, 5 slide-rail tools
- Demand scale: 2.684x versus the 9-robot default load
- Tick model: 1-minute fast-forward ticks, no browser or video rendering
- Congestion shock coverage: 27 nominal scenarios + 27 aisle-surge scenarios

## Headline Results

- Safety pass rate: 100.0% (54 / 54 paired scenarios)
- Collision violations: 0
- Tile-lock overlap violations: 0
- Average planner throughput uplift: 60.27%
- Best planner throughput uplift: 185.23%
- Local planner improved throughput in 48 / 54 scenarios
- Average local-planner throughput: 1018.28 orders/hour
- Average planner-off throughput: 614.62 orders/hour

## Why This Matters

The main submission shows 9 AEGIS robots sharing aisles with zero collisions, and this benchmark can also scale the same layout to 30 heterogeneous robots. The stress test evaluates load, SKU weight mix, pick difficulty, aisle-surge congestion, and robot end-effector specialization without relying on a UI recording. That turns the project from a single demo into a repeatable warehouse optimization benchmark.

## Scenario Pair Summary

| Scenario | Shock | Off THR | Local THR | Uplift | Local completion | Safety |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| high_balanced_easy_aisle_surge | aisle_surge | 605.0 | 1717.83 | 183.94% | 99.85% | pass |
| high_balanced_easy_nominal | nominal | 880.0 | 1461.5 | 66.08% | 99.98% | pass |
| high_balanced_hard_aisle_surge | aisle_surge | 602.33 | 1718.0 | 185.23% | 99.9% | pass |
| high_balanced_hard_nominal | nominal | 743.83 | 1460.5 | 96.35% | 100.0% | pass |
| high_balanced_nominal_aisle_surge | aisle_surge | 603.67 | 1716.0 | 184.26% | 99.81% | pass |
| high_balanced_nominal_nominal | nominal | 850.0 | 1460.17 | 71.78% | 100.0% | pass |
| high_heavy_easy_aisle_surge | aisle_surge | 600.33 | 1681.83 | 180.15% | 97.73% | pass |
| high_heavy_easy_nominal | nominal | 771.33 | 1459.5 | 89.22% | 99.9% | pass |
| high_heavy_hard_aisle_surge | aisle_surge | 598.83 | 1689.83 | 182.19% | 98.28% | pass |
| high_heavy_hard_nominal | nominal | 664.17 | 1460.67 | 119.92% | 99.97% | pass |
| high_heavy_nominal_aisle_surge | aisle_surge | 600.17 | 1681.0 | 180.09% | 97.71% | pass |
| high_heavy_nominal_nominal | nominal | 713.83 | 1458.67 | 104.34% | 99.86% | pass |
| high_light_easy_aisle_surge | aisle_surge | 639.83 | 1720.33 | 168.87% | 100.0% | pass |
| high_light_easy_nominal | nominal | 897.0 | 1460.0 | 62.76% | 100.0% | pass |
| high_light_hard_aisle_surge | aisle_surge | 604.17 | 1718.5 | 184.44% | 99.89% | pass |
| high_light_hard_nominal | nominal | 860.33 | 1459.5 | 69.64% | 100.0% | pass |
| high_light_nominal_aisle_surge | aisle_surge | 627.33 | 1721.17 | 174.36% | 99.98% | pass |
| high_light_nominal_nominal | nominal | 891.33 | 1462.0 | 64.02% | 100.0% | pass |
| low_balanced_easy_aisle_surge | aisle_surge | 390.5 | 392.83 | 0.6% | 100.0% | pass |
| low_balanced_easy_nominal | nominal | 333.0 | 335.33 | 0.7% | 100.0% | pass |
| low_balanced_hard_aisle_surge | aisle_surge | 390.67 | 393.17 | 0.64% | 100.0% | pass |
| low_balanced_hard_nominal | nominal | 333.5 | 334.83 | 0.4% | 100.0% | pass |
| low_balanced_nominal_aisle_surge | aisle_surge | 391.17 | 391.5 | 0.08% | 100.0% | pass |
| low_balanced_nominal_nominal | nominal | 332.83 | 334.0 | 0.35% | 100.0% | pass |
| low_heavy_easy_aisle_surge | aisle_surge | 390.83 | 392.17 | 0.34% | 100.0% | pass |
| low_heavy_easy_nominal | nominal | 333.5 | 334.33 | 0.25% | 100.0% | pass |
| low_heavy_hard_aisle_surge | aisle_surge | 390.17 | 391.0 | 0.21% | 100.0% | pass |
| low_heavy_hard_nominal | nominal | 335.17 | 333.33 | -0.55% | 100.0% | pass |
| low_heavy_nominal_aisle_surge | aisle_surge | 391.67 | 392.17 | 0.13% | 100.0% | pass |
| low_heavy_nominal_nominal | nominal | 333.33 | 335.17 | 0.55% | 100.0% | pass |
| low_light_easy_aisle_surge | aisle_surge | 390.17 | 392.83 | 0.68% | 100.0% | pass |
| low_light_easy_nominal | nominal | 334.67 | 334.17 | -0.15% | 100.0% | pass |
| low_light_hard_aisle_surge | aisle_surge | 392.17 | 392.0 | -0.04% | 100.0% | pass |
| low_light_hard_nominal | nominal | 334.0 | 333.5 | -0.15% | 100.0% | pass |
| low_light_nominal_aisle_surge | aisle_surge | 391.5 | 391.17 | -0.08% | 100.0% | pass |
| low_light_nominal_nominal | nominal | 335.0 | 334.5 | -0.15% | 100.0% | pass |
| medium_balanced_easy_aisle_surge | aisle_surge | 675.5 | 1198.17 | 77.38% | 100.0% | pass |
| medium_balanced_easy_nominal | nominal | 901.67 | 1018.67 | 12.98% | 100.0% | pass |
| medium_balanced_hard_aisle_surge | aisle_surge | 625.0 | 1197.67 | 91.63% | 100.0% | pass |
| medium_balanced_hard_nominal | nominal | 863.17 | 1017.0 | 17.82% | 100.0% | pass |
| medium_balanced_nominal_aisle_surge | aisle_surge | 656.0 | 1198.33 | 82.67% | 100.0% | pass |
| medium_balanced_nominal_nominal | nominal | 896.0 | 1017.83 | 13.6% | 100.0% | pass |
| medium_heavy_easy_aisle_surge | aisle_surge | 636.5 | 1198.83 | 88.35% | 100.0% | pass |
| medium_heavy_easy_nominal | nominal | 892.5 | 1017.33 | 13.99% | 100.0% | pass |
| medium_heavy_hard_aisle_surge | aisle_surge | 608.0 | 1198.33 | 97.09% | 100.0% | pass |
| medium_heavy_hard_nominal | nominal | 790.5 | 1017.83 | 28.76% | 100.0% | pass |
| medium_heavy_nominal_aisle_surge | aisle_surge | 622.17 | 1197.67 | 92.5% | 100.0% | pass |
| medium_heavy_nominal_nominal | nominal | 873.5 | 1017.33 | 16.47% | 100.0% | pass |
| medium_light_easy_aisle_surge | aisle_surge | 703.83 | 1197.67 | 70.16% | 100.0% | pass |
| medium_light_easy_nominal | nominal | 1014.83 | 1017.33 | 0.25% | 100.0% | pass |
| medium_light_hard_aisle_surge | aisle_surge | 665.83 | 1198.17 | 79.95% | 100.0% | pass |
| medium_light_hard_nominal | nominal | 889.33 | 1018.0 | 14.47% | 100.0% | pass |
| medium_light_nominal_aisle_surge | aisle_surge | 696.0 | 1198.33 | 72.17% | 100.0% | pass |
| medium_light_nominal_nominal | nominal | 901.83 | 1017.5 | 12.83% | 100.0% | pass |

## Reproduce

```bash
python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 54 --fleet-size 30 --output submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_30robots.json --report submissions/warehouse_quadbot_atomic_demos/THIRTY_ROBOT_STRESS_BENCHMARK.md
```

Outputs:

- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_30robots.json`
- `submissions/warehouse_quadbot_atomic_demos/THIRTY_ROBOT_STRESS_BENCHMARK.md`

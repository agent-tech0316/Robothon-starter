Registration UUID: 13b27675-9c26-49df-9014-cb31f33f9df8

# Judge Scorecard

**Agentic Warehouse Quadbot Benchmark:** 54-scenario fleet stress testing, 30-robot heterogeneous scaling, and MuJoCo 6-DOF plus end-effector contact validation.

| Signal | Result |
| --- | --- |
| Fleet task | 9 AEGIS quadrupeds in the live UI plus a 30-robot heterogeneous fleet stress extension |
| Stress benchmark | 54 six-hour scenarios / 108 planner runs / 9,720 simulated robot-hours at 30 robots |
| Safety | 100% pass, 0 collisions, 0 tile-lock overlaps |
| Planner value | +60.27% average throughput uplift, +185.23% best uplift vs planner-off baseline in the 30-robot stress extension |
| High-load result | 91 / 140 orders, 364 orders/hour, 0 movement safety violations |
| MuJoCo depth | 14 evidence clips, generated MJCF, touch sensors, collision geoms, contact traces, 3-robot corridor physics, heterogeneous dexterous/magnet/rail end-effectors |
| 6-DOF + tool proof | 630 gripper/package contacts; heterogeneous tool contacts: 1077 dexterous/fragile, 508 magnet/metal, 1020 rail/tote |
| Demo | 1:27.58 AI-judge cut with Web/MuJoCo layered validation, expanded live runtime decision replay, and 3-robot corridor physics, benchmark proof, contact sheet, 6-DOF grasp, and handoff |

Run first: `python examples/run_agentech_judge_review.py`. Read first: `submissions/warehouse_quadbot_atomic_demos/JUDGE_SCORECARD.md`.

# Project Summary

Agentic Warehouse Quadbot Fulfillment Simulator is Agentech's FFAI Robothon 2026 entry. It is best read as a benchmark: a multi-agent warehouse order fulfillment stress test connected to mission, workflow, skill graph, runtime scheduling, KPI benchmarking, MuJoCo physical action evidence, and a mission-control UI.

The core challenge is fleet-level coordination: one robot can move a parcel, but many robots sharing narrow aisles create traffic, priority conflicts, deadlock risk, and tile-lock contention. This submission evaluates whether the whole warehouse keeps moving safely and efficiently under load.

Judge-facing distinction: this is not only a multi-robot clip. It is a scalable warehouse benchmark. MuJoCo proves the atomic robot skills are physically plausible; the runtime proves that fleet decisions improve throughput under congestion, SKU-weight variation, pick difficulty, and long-horizon load.

Latest judge fast path: `python examples/run_agentech_judge_review.py` prints artifact readiness, 54-scenario stress benchmark results, the 30-robot heterogeneous extension, medium/high runtime metrics, 14 MuJoCo evidence clips, 6-DOF grasp contact proof, heterogeneous end-effector contact proof, 3-robot corridor physics, and rubric mapping without requiring the dashboard UI.

# Robot Platform

Faraday Future AEGIS quadruped, with a BASE_LINK-mounted basket and a Futurist-right-arm-derived six-axis front manipulator. MuJoCo evidence clips validate walking, payload carrying, shelf pickup, basket contact, robot-to-robot handoff, 6-DOF overhead grasp sweeps, a three-AEGIS corridor scene with loaded obstacle avoidance, and mixed end-effectors: dexterous hand for fragile/shape-sensitive payloads, electromagnet for metal payloads, and slide rail for guided tote transfer.

# Task Goal

Fulfill warehouse outbound orders with multiple quadruped robots on a discrete tile grid while managing congestion, tile reservations, rack obstacles, SKU weight/difficulty, and throughput.

# Agentic Workflow Design

Mission -> Workflow -> Skill Graph -> Runtime -> Scheduler -> Tile Locks -> Benchmark Metrics -> UI + MuJoCo Evidence

The runtime uses four-direction movement, atomic source+destination locks, deadlock recovery, and generated low/medium/high load profiles.

# Key Innovations

- Warehouse optimization framed as a mission/workflow/skill-graph runtime rather than low-level robot control.
- Fleet-level benchmark: 9 robots must share discrete aisles, reserve tiles, avoid deadlocks, handle priority pressure, and improve throughput together.
- Local planner multi-port conveyor selection improves high-load throughput from 64/hr planner-off to 364/hr local (+468.8%) while preserving zero movement safety violations.
- MuJoCo used as physical evidence for grasp/load/obstacle/small-fleet physics while the web runtime handles scalable agentic planning, congestion analysis, route optimization, and throughput benchmarks.
- MuJoCo evidence scorecard makes physical validation inspectable: joints, actuators, sensors, contact counters, payload response, and two-robot handoff scene depth.
- Added judge-facing MuJoCo videos beyond the main demo: `six_dof_grasp_sweep_wood.mp4`, `six_dof_grasp_sweep_metal.mp4`, and `fleet_physics_corridor.mp4`, showing six-axis parcel handling plus three-AEGIS loaded corridor avoidance.
- Added heterogeneous MuJoCo end-effector lab: `effector_mix_lab.mp4` and trajectory JSON prove dexterous-hand/fragile, electromagnet/metal, and slide-rail/tote contact paths with 1077, 508, and 1020 contacts respectively.
- Added 30-robot heterogeneous fleet scaling: 8 grippers, 9 dexterous hands, 8 electromagnets, and 5 slide-rail tools across 54 six-hour scenarios / 9,720 robot-hours, achieving +60.27% average throughput uplift and 100% safety pass.
- Heavy 6-DOF grasp evidence records 630 gripper/package contacts, 220 left-finger contacts, 250 right-finger contacts, and 36 dual-finger grasp frames; the heavy handoff records 279 receiver-gripper/package contacts.
- Runtime snapshots expose robot state, order state, movement locks, rack-blocking, congestion, conveyor door/unload tiles, and KPI metrics directly to the dashboard.
- One-command AI judge fast path reduces review friction and directly addresses the prior UI-complexity feedback.
- New default AI Decision Board plus tabbed Agentic Planner graph/table/text view makes scheduler intent visible: selected robot, reserved tile lock, next skill, mission/workflow/skill/runtime/KPI path, and text decision are shown above the live map.
- Default simplified UI mode directly addresses prior judge feedback: first screen now shows throughput, safety, MuJoCo proof, Agentic Planner graph, AI decision, and the live map; dense ops panels are one click away.
- Dashboard benchmark proof strip exposes the medium planner-off baseline, local-planner result, and zero safety violations in the first KPI panel.
- Simplified Judge Review Path reduces UI scanning cost by surfacing fleet size, planner uplift, safety, replans, and MuJoCo skill proof in one narrow rail.
- Multi-wall outbound model uses four exterior conveyor ports; each belt sits outside the warehouse boundary with an outer roll-up door line and one valid in-warehouse edge unload tile, giving the planner real exit-selection pressure instead of a broad fake drop zone.
- Accelerated 30-robot heterogeneous fleet stress benchmark runs 54 six-hour nominal/aisle-surge scenarios / 108 raw planner runs / 9,720 simulated robot-hours, with 100% safety pass rate and +60.27% average planner throughput uplift.

# Benchmark Results

| Load | Completed / Created | Throughput | Avg lock wait | Safety violations |
| --- | ---: | ---: | ---: | ---: |
| Low | 24 / 27 | 96/hr | 2.89 ticks | 0 |
| Medium | 77 / 84 | 308/hr | 30.67 ticks | 0 |
| High | 91 / 140 | 364/hr | 38.56 ticks | 0 |

Safety violations include blocked tiles, non-cardinal moves, robot collisions, and lock overlaps.

# Fleet Stress Benchmark

`python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 54` generates the default 9-robot stress report. The 30-robot extension is regenerated with `--fleet-size 30 --output submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_30robots.json --report submissions/warehouse_quadbot_atomic_demos/THIRTY_ROBOT_STRESS_BENCHMARK.md`. Headline 30-robot result: 54/54 paired scenarios pass safety checks, 0 collisions, 0 lock overlaps, +60.27% average planner throughput uplift, +185.23% best-case uplift.

# Demo Video

Final 1-3 minute demo video: `submissions/warehouse_quadbot_atomic_demos/demo.mp4`

The final video is now a 1:27.58 AI-judge review cut. The final cut opens with a Web Runtime vs MuJoCo Physics title card, then live runtime decision footage: 9 robots moving, tile locks, AI decision text, selected robot, next skill, order pressure, KPI proof, 54-scenario benchmark numbers, contact-sheet evidence, 6-DOF MuJoCo grasp/handoff proof, and the new 3-AEGIS corridor physics clip.

Included evidence clips:

- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_live_decision_replay.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/fleet_physics_corridor.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/effector_mix_lab.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_30robots.json`
- `submissions/warehouse_quadbot_atomic_demos/THIRTY_ROBOT_STRESS_BENCHMARK.md`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/*.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/six_dof_grasp_sweep_wood.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/six_dof_grasp_sweep_metal.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/*.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/physics_evidence_contact_sheet.png`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/clip_manifest.json` with contact totals and six-axis joint traces

# Run Instructions

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python examples/run_agentech_judge_review.py
python examples/build_integrated_demo_data.py
python examples/run_warehouse_runtime.py --load medium --planner local --ticks 900 --print-summary
python -m http.server 8765 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8765/submissions/warehouse_quadbot_atomic_demos/ui/index.html
```


# Validation Status

Clean-copy validation passed with Python 3.12: dependency install, runtime data generation, medium benchmark run, pytest smoke tests, MuJoCo shelf-pick smoke generation, and HTTP resource checks for UI/runtime/video artifacts.

Final demo video is included as `submissions/warehouse_quadbot_atomic_demos/demo.mp4`; the latest 1:27.58 judge-cut video audit passed locally with layered Web/MuJoCo validation, expanded live runtime footage, and 3-robot MuJoCo corridor physics.

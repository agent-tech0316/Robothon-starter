Registration UUID: 13b27675-9c26-49df-9014-cb31f33f9df8

# Project Summary

Agentic Warehouse Quadbot Fulfillment Simulator is Agentech's FFAI Robothon 2026 entry. It demonstrates a multi-agent warehouse order fulfillment simulator that connects mission, workflow, skill graph, runtime scheduling, KPI benchmarking, MuJoCo physical action evidence, and a mission-control UI.

The core challenge is fleet-level coordination: one robot can move a parcel, but many robots sharing narrow aisles create traffic, priority conflicts, deadlock risk, and tile-lock contention. This submission evaluates whether the whole warehouse keeps moving safely and efficiently under load.

# Robot Platform

Faraday Future AEGIS quadruped, with a BASE_LINK-mounted basket and a Futurist-right-arm-derived front manipulator. MuJoCo evidence clips validate walking, payload carrying, shelf pickup, basket contact, and robot-to-robot handoff.

# Task Goal

Fulfill warehouse outbound orders with multiple quadruped robots on a discrete tile grid while managing congestion, tile reservations, rack obstacles, SKU weight/difficulty, and throughput.

# Agentic Workflow Design

Mission -> Workflow -> Skill Graph -> Runtime -> Scheduler -> Tile Locks -> Benchmark Metrics -> UI + MuJoCo Evidence

The runtime uses four-direction movement, atomic source+destination locks, deadlock recovery, and generated low/medium/high load profiles.

# Key Innovations

- Warehouse optimization framed as a mission/workflow/skill-graph runtime rather than low-level robot control.
- Fleet-level benchmark: 9 robots must share discrete aisles, reserve tiles, avoid deadlocks, handle priority pressure, and improve throughput together.
- Local planner route-window reservation improves medium throughput by +12.5% versus planner-off while preserving zero movement safety violations.
- MuJoCo used as physical evidence for atomic skills while fleet planning stays in a scalable tile-level simulator.
- Runtime snapshots expose robot state, order state, movement locks, rack-blocking, congestion, and KPI metrics directly to the dashboard.
- AI-judge-friendly static UI and generated artifacts make the project understandable without extra explanation.
- Dashboard benchmark proof strip exposes the medium planner-off baseline, local-planner result, and zero safety violations in the first KPI panel.
- Simplified Judge Review Path reduces UI scanning cost by surfacing fleet size, planner uplift, safety, replans, and MuJoCo skill proof in one narrow rail.

# Benchmark Results

| Load | Completed / Created | Throughput | Avg lock wait | Safety violations |
| --- | ---: | ---: | ---: | ---: |
| Low | 25 / 27 | 100/hr | 3.44 ticks | 0 |
| Medium | 81 / 84 | 324/hr | 41.78 ticks | 0 |
| High | 124 / 140 | 496/hr | 120.67 ticks | 0 |

Safety violations include blocked tiles, non-cardinal moves, robot collisions, and lock overlaps.

# Demo Video

Final 1-3 minute demo video: `submissions/warehouse_quadbot_atomic_demos/demo.mp4`

The final video is already trimmed to 1:05.97 and follows a fast review path: identity, 9-robot warehouse runtime, locks/replans, KPI proof, and MuJoCo evidence.

Included evidence clips:

- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/*.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/*.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/physics_evidence_contact_sheet.png`

# Run Instructions

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
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

Final demo video is included as `submissions/warehouse_quadbot_atomic_demos/demo.mp4`; post-video audit passed locally.

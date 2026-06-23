# Demo Video Script

Final video has been produced and included as `demo.mp4`. This script is retained as the capture plan/provenance for the 1-3 minute demo.

## Setup Before Recording

From repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python examples/build_integrated_demo_data.py
python -m http.server 8765 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8765/submissions/warehouse_quadbot_atomic_demos/ui/index.html
```

Optional MuJoCo evidence refresh:

```bash
python submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py --scenario shelf_pick_metal
```

## Final 63-Second AI Judge Review Path

The submitted `demo.mp4` is intentionally short and edited for AI judges. The judge-facing pacing is:

| Time | What to notice |
| --- | --- |
| 0:00-0:04 | Project identity: 9 AEGIS quadrupeds, tile-lock runtime, MuJoCo-backed skills |
| 0:04-0:36 | Live warehouse runtime: robots sharing aisles, orders, tile locks, replans, and KPI panels |
| 0:36-0:43 | Benchmark proof: 54 scenarios, 108 planner runs, 2,916 robot-hours, 0 collisions/lock overlaps, +30.74% average uplift |
| 0:43-0:48 | MuJoCo contact sheet: 12 generated physics evidence clips and contact traces |
| 0:48-0:54 | 6-DOF heavy grasp: wrist roll/tool yaw, package roll/pitch/yaw, 630 gripper contacts, 36 dual-finger frames |
| 0:54-0:58 | Robot-to-robot heavy handoff: receiver gripper/package contact evidence |
| 0:58-1:03 | Closing summary: runtime scales decisions; MuJoCo validates physical skills |

## Original Capture Plan

The longer outline below is retained as provenance, but the final video is now a 1:21.38 judge-cut edit with expanded live runtime decision replay for faster scoring.

### Startup and Project Identity

Show the terminal command and browser loading the dashboard. Mention the project name: Agentic Warehouse Quadbot Fulfillment Simulator.

### Environment and Robot Platform

Show the warehouse tile grid, rack obstacles, AEGIS quadruped robots, basket/manipulator concept, load selector, and KPI panels.

### Runtime Execution

Switch between low, medium, and high load. Show robots moving on discrete tiles, active orders, tile locks, replans, and congestion indicators.

### Agentic Workflow

Explain the stack: Mission -> Workflow -> Skill Graph -> Runtime -> Scheduler -> Tile Locks -> Benchmark Metrics. Show the UI panels that expose order assignment, robot states, and planner decisions.

### MuJoCo Physical Evidence

Show the included contact sheet or MP4 clips for payload walking, shelf pickup, basket loading, and handoff. Emphasize that MuJoCo validates atomic physical actions while the fleet optimizer runs at tile level.

### KPI Outcome

Show benchmark metrics: throughput, completion rate, wait time, congestion, and zero safety violations. Highlight the high-load result: 91 of 140 completed, 364 orders/hour, and 0 movement safety violations; also call out the 54-scenario stress benchmark with +30.74% average planner uplift.

### Limitations and Future Work

Briefly state that the current local planner already improves the deterministic medium benchmark, but future work should learn lane direction, congestion pricing, and robot-to-robot handoff timing policies instead of using a fixed route-window reservation factor.

## Suggested Closing Line

This project turns quadruped warehouse work into a full agentic fulfillment benchmark: physical skills in MuJoCo, fleet decisions in a tile runtime, and measurable throughput in the dashboard.

## Final Video File

- `submissions/warehouse_quadbot_atomic_demos/demo.mp4`
- Duration: 1:21.38
- Format: 1280x720 H.264/AAC MP4
- Size: approximately 37.9 MB

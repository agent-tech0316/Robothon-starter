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

## Shot List

### 0:00-0:15 - Startup and Project Identity

Show the terminal command and browser loading the dashboard. Mention the project name: Agentic Warehouse Quadbot Fulfillment Simulator.

### 0:15-0:35 - Environment and Robot Platform

Show the warehouse tile grid, rack obstacles, AEGIS quadruped robots, basket/manipulator concept, load selector, and KPI panels.

### 0:35-0:65 - Runtime Execution

Switch between low, medium, and high load. Show robots moving on discrete tiles, active orders, tile locks, replans, and congestion indicators.

### 0:65-1:25 - Agentic Workflow

Explain the stack: Mission -> Workflow -> Skill Graph -> Runtime -> Scheduler -> Tile Locks -> Benchmark Metrics. Show the UI panels that expose order assignment, robot states, and planner decisions.

### 1:25-1:50 - MuJoCo Physical Evidence

Show the included contact sheet or MP4 clips for payload walking, shelf pickup, basket loading, and handoff. Emphasize that MuJoCo validates atomic physical actions while the fleet optimizer runs at tile level.

### 1:50-2:15 - KPI Outcome

Show benchmark metrics: throughput, completion rate, wait time, congestion, and zero safety violations. Highlight the medium result: 81 of 84 completed, 324 orders/hour, +12.5% over planner-off, 0 collisions and 0 lock overlaps.

### 2:15-2:45 - Limitations and Future Work

Briefly state that the current local planner already improves the deterministic medium benchmark, but future work should learn lane direction, congestion pricing, and robot-to-robot handoff timing policies instead of using a fixed route-window reservation factor.

## Suggested Closing Line

This project turns quadruped warehouse work into a full agentic fulfillment benchmark: physical skills in MuJoCo, fleet decisions in a tile runtime, and measurable throughput in the dashboard.

## Final Video File

- `submissions/warehouse_quadbot_atomic_demos/demo.mp4`
- Duration: 1:05.97
- Format: 1280x720 H.264/AAC MP4
- Size: approximately 9.8 MB

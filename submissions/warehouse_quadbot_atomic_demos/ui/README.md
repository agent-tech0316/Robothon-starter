# Agentic Warehouse Runtime UI

This is a standalone presentation UI for the warehouse optimization submission. It is intentionally not a low-level robot control panel. The screen shows the higher-level system:

Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization

## Technical Stack

- Static HTML/CSS/JavaScript
- Canvas 2D for the pseudo-3D isometric warehouse stage
- DOM/CSS for runtime controls, metrics, logs, and MuJoCo evidence panels
- No npm install, no bundler, no external network dependency

## Run

From the repository root, serve the repo over HTTP so relative JSON and video assets load cleanly:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/submissions/warehouse_quadbot_atomic_demos/ui/index.html
```

The UI is designed as a fixed 3840x2160 16:9 surface. At a 3840x2160 browser window it renders 1:1 for capture. Smaller browser windows preview the same surface by scaling it down.

The UI reads generated runtime files from:

```text
submissions/warehouse_quadbot_atomic_demos/outputs/runtime_snapshot_{low,medium,high}.json
submissions/warehouse_quadbot_atomic_demos/outputs/benchmark_metrics_{low,medium,high}.json
```

The MuJoCo videos are loaded from:

```text
submissions/warehouse_quadbot_atomic_demos/outputs/
```

## Integration Contract

Runtime-linked robot drawing uses `robot.visualPose` derived from runtime snapshot routes and `movement_locks`. Runtime routes are open paths; the UI does not close the last route point back to the first. The UI includes a mock fallback for direct file opening or missing JSON.

For the UI-to-runtime handoff contract, see:

```text
submissions/warehouse_quadbot_atomic_demos/ui/UI_DESIGN_HANDOFF.md
```

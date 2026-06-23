# Submission Manifest

Project: Agentic Warehouse Quadbot Fulfillment Simulator  
Team: Agentech  
Registration UUID: 13b27675-9c26-49df-9014-cb31f33f9df8

This submission is intentionally organized as a repository-level project with the judged entry rooted at `submissions/warehouse_quadbot_atomic_demos/`.

## Judge Entry Point

Start here:

- `submissions/warehouse_quadbot_atomic_demos/README.md`
- `submissions/warehouse_quadbot_atomic_demos/JUDGE_FAST_PATH.md`
- `submissions/warehouse_quadbot_atomic_demos/PROJECT_WRITEUP.md`
- `submissions/warehouse_quadbot_atomic_demos/registration.json`
- `submissions/warehouse_quadbot_atomic_demos/PR_DESCRIPTION.md`
- `submissions/warehouse_quadbot_atomic_demos/demo.mp4`

## Source Code Included

Runtime and benchmark code:

- `warehouse_runtime/`
- `examples/run_agentech_judge_review.py`
- `examples/build_integrated_demo_data.py`
- `examples/run_warehouse_runtime.py`
- `examples/run_fleet_stress_benchmark.py`
- `tests/test_runtime_smoke.py`

Configuration and schemas:

- `configs/runtime.yaml`
- `configs/scheduler_policy.yaml`
- `configs/skill_graph.yaml`
- `configs/benchmark.yaml`
- `configs/mission_layout.yaml`
- `schemas/warehouse_schema.json`
- `schemas/order_schema.json`
- `schemas/robot_schema.json`

Submission-local MuJoCo and UI code:

- `submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py`
- `submissions/warehouse_quadbot_atomic_demos/mujoco_minimal/`
- `submissions/warehouse_quadbot_atomic_demos/mujoco_physics_evidence/`
- `submissions/warehouse_quadbot_atomic_demos/ui/`

## MuJoCo Assets Included

Starter repository robot assets reused by this project:

- `assets/Aegis/urdf/Aegis_mujoco.urdf`
- `assets/Futurist/futurist.urdf`
- `assets/Futurist/meshes/`
- `assets/Master/`

Submission-local generated and hand-authored MuJoCo evidence:

- `submissions/warehouse_quadbot_atomic_demos/mujoco_minimal/*.xml`
- `submissions/warehouse_quadbot_atomic_demos/mujoco_physics_evidence/*.xml`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/*.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/six_dof_grasp_sweep_wood.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/six_dof_grasp_sweep_metal.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/*.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/clip_manifest.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/physics_evidence_contact_sheet.png`

## Runtime Artifacts Included

Generated benchmark outputs used by the UI:

- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_snapshot_low.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_snapshot_medium.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_snapshot_high.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/benchmark_metrics_low.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/benchmark_metrics_medium.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/benchmark_metrics_high.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_events_low.jsonl`
- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_events_medium.jsonl`
- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_events_high.jsonl`
- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_summary.json`
- `submissions/warehouse_quadbot_atomic_demos/FLEET_STRESS_BENCHMARK.md`

## Default Run Path

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python examples/run_agentech_judge_review.py
python examples/build_integrated_demo_data.py
python examples/run_warehouse_runtime.py --load medium --planner local --ticks 900 --print-summary
python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 54
python submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py --scenario shelf_pick_metal
python submissions/warehouse_quadbot_atomic_demos/mujoco_physics_evidence/main.py --clip all --fps 18 --width 720 --height 406
python -m http.server 8765 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8765/submissions/warehouse_quadbot_atomic_demos/ui/index.html
```

## External Services

No external service is required for default judging. Optional OpenAI planner mode exists, but default reproducibility uses the local planner and requires no API key.

## Final Artifact Status

The final demo video is included as `submissions/warehouse_quadbot_atomic_demos/demo.mp4`. The accelerated fleet benchmark outputs and 12 MuJoCo physics evidence clips are also included and can be regenerated with the default run path above.

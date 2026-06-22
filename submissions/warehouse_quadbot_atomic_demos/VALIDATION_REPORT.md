# Validation Report

Project: Agentic Warehouse Quadbot Fulfillment Simulator  
Team: Agentech  
Validation date: 2026-06-21  
Registration UUID: 13b27675-9c26-49df-9014-cb31f33f9df8

## Official Requirement Cross-Check

| Requirement | Status | Evidence |
| --- | --- | --- |
| Project under `submissions/<project>/` | Passed | `submissions/warehouse_quadbot_atomic_demos/` |
| Project source code included | Passed | `warehouse_runtime/`, `examples/`, `configs/`, `schemas/`, submission-local scripts |
| MuJoCo assets included | Passed | `assets/Aegis/`, `assets/Futurist/`, submission-local XML/MJCF evidence modules |
| Run instructions included | Passed | `README.md`, `PROJECT_WRITEUP.md`, `SUBMISSION_MANIFEST.md` |
| `registration.json` included | Passed | Exact UUID verified |
| Same UUID in PR description | Passed | `PR_DESCRIPTION.md` begins with exact required UUID line |
| Demo video included or linked | Passed | `submissions/warehouse_quadbot_atomic_demos/demo.mp4` |

## Environment Used

- Python 3.12 clean environment
- `python -m pip install -r requirements.txt`
- Local planner mode for default reproducibility
- No API keys required

Note: macOS system Python 3.9 was tested and rejected for final instructions because the current MuJoCo dependency resolves cleanly with Python 3.12 wheels on this machine.

## Commands Validated

```bash
python examples/build_integrated_demo_data.py
python examples/run_warehouse_runtime.py --load medium --planner local --ticks 900 --print-summary
python -m pytest tests/test_runtime_smoke.py
python submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py --scenario shelf_pick_metal
python -m http.server 8877 --bind 127.0.0.1
```

HTTP resources checked successfully from the clean-copy server:

- `submissions/warehouse_quadbot_atomic_demos/ui/index.html`
- `submissions/warehouse_quadbot_atomic_demos/outputs/runtime_snapshot_medium.json`
- `submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/empty_walk.mp4`

## Runtime Validation Result

Medium-load local planner run completed successfully after route-window reservation with:

- Created orders: 84
- Completed orders: 81
- Throughput: 324 orders/hour
- Average completion: 42.30 ticks
- Average lock wait: 41.78 ticks
- Robot utilization: 48.4%
- Blocked-tile route violations: 0
- Route cardinality violations: 0
- Collision violations: 0
- Lock overlap violations: 0

## Fleet Stress Benchmark Validation

The accelerated benchmark-only fleet stress runner was executed successfully:

```bash
.venv312/bin/python examples/run_fleet_stress_benchmark.py --hours 6 --scenario-limit 54
```

Result summary:

- Scenario matrix: 54 scenarios
- Paired planner runs: 54 runs
- Simulated warehouse hours: 162
- Simulated robot-hours: 2,916
- Safety pass rate: 100%
- Collision violations: 0
- Tile-lock overlap violations: 0
- Average planner throughput uplift: +30.74%
- Best planner throughput uplift: +97.42%
- Wall-clock runtime: about 3.1 seconds on the local validation machine

Generated artifacts:

- `submissions/warehouse_quadbot_atomic_demos/FLEET_STRESS_BENCHMARK.md`
- `submissions/warehouse_quadbot_atomic_demos/outputs/fleet_stress_benchmark_summary.json`

## Artifact Hygiene

Passed checks:

- No local absolute machine paths inside `submissions/warehouse_quadbot_atomic_demos/`
- No `.DS_Store`, `__pycache__`, or `*.pyc` artifacts inside submission folder
- No files over 50MB inside submission folder
- Submission `outputs/` artifacts are explicitly unignored for commit
- `.venv/` and `.venv312/` remain ignored


## Latest Local Verification Pass

Run date: 2026-06-21 16:54 PDT

Passed in the project workspace using `.venv312` / Python 3.12.13:

```bash
.venv312/bin/python -m pip install -r requirements.txt
.venv312/bin/python examples/build_integrated_demo_data.py
.venv312/bin/python examples/run_warehouse_runtime.py --load medium --planner local --ticks 900 --output-dir /tmp/ff-robothon-final-runtime --run-id final_validation_medium --print-summary
.venv312/bin/python -m pytest tests/test_runtime_smoke.py -p no:cacheprovider
node --check submissions/warehouse_quadbot_atomic_demos/ui/app.js
.venv312/bin/python submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py --scenario shelf_pick_metal
.venv312/bin/python -m http.server 8891 --bind 127.0.0.1
```

Temporary HTTP checks returned `200 OK` for:

- UI HTML
- medium runtime JSON
- MuJoCo MP4 asset

The temporary HTTP server was stopped after validation.

## Demo Video Integration

Final demo video was integrated after recording:

- Source located from the user desktop export.
- Compressed to submission-safe MP4.
- Output: `submissions/warehouse_quadbot_atomic_demos/demo.mp4`
- Properties: 1:05.97, 1280x720, H.264 video, AAC audio, approximately 9.8 MB.
- README, PR description, manifest, write-up, and checklist were updated to reference the file.

## Remaining Final Check

Post-video audit passed locally: no video placeholder remains, no local absolute paths were found, no cache artifacts were found, and no submission file exceeds 50MB. Before opening the actual PR, confirm the staged file list matches the intended submission package.

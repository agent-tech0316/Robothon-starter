# Submission Checklist

Project: Agentic Warehouse Quadbot Fulfillment Simulator
Team: Agentech
Registration UUID: 13b27675-9c26-49df-9014-cb31f33f9df8

## Required Deliverables

- [x] Project source code included
- [x] MuJoCo XML/MJCF/URDF evidence modules included
- [x] AEGIS/Futurist/Master assets available in repo `assets/`
- [x] Runtime configs, schemas, and benchmark generator included
- [x] Runtime output JSON/JSONL generated for low/medium/high
- [x] MuJoCo evidence MP4 clips included
- [x] Final `demo.mp4` video file added to submission folder.
- [x] README prepared for AI judges
- [x] `PROJECT_WRITEUP.md` created
- [x] `registration.json` created with exact UUID
- [x] PR description draft created
- [x] `DEMO_VIDEO_SCRIPT.md` created for the final recording pass.
- [x] `VALIDATION_REPORT.md` created.
- [x] `SUBMISSION_MANIFEST.md` created.
- [x] Final 1-3 minute demo video finalized and included as `demo.mp4`
- [x] Clean-copy run test completed from a fresh Python 3.12 environment

## Known Blockers Before PR Submission

1. Final demo video is included as `demo.mp4`.
2. Post-video audit passed locally: no video placeholders, no local absolute paths, no cache artifacts, and no files over 50MB.
3. Planner-off and local-planner benchmarks currently have equal throughput in the deterministic medium scenario; this should be presented honestly as current limitation unless planner tuning is added later.

## Validation Commands

```bash
python examples/build_integrated_demo_data.py
python examples/run_warehouse_runtime.py --load medium --planner local --ticks 900 --print-summary
python submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py --scenario shelf_pick_metal
python -m http.server 8765 --bind 127.0.0.1
```

## Validation Performed On 2026-06-21

- [x] `registration.json` UUID checked exactly.
- [x] Submission README/write-up/PR description contain required project identity.
- [x] No local machine absolute paths remain inside `submissions/warehouse_quadbot_atomic_demos/`.
- [x] Python syntax check passed for runtime, CLI, integrated data builder, and MuJoCo generator.
- [x] `python examples/build_integrated_demo_data.py` regenerated low/medium/high runtime files.
- [x] `python examples/run_warehouse_runtime.py --load medium --planner local --ticks 900 --print-summary` passed.
- [x] Runtime smoke/invariant tests passed via direct importlib invocation because system Python lacks `pytest`.
- [x] `node --check submissions/warehouse_quadbot_atomic_demos/ui/app.js` passed with bundled Node.
- [x] HTTP resource check passed for UI HTML, medium runtime JSON, and MuJoCo MP4 via temporary local server.
- [x] `.DS_Store`, `__pycache__`, and `*.pyc` removed from submission folder.
- [x] `.gitignore` updated so this submission's `outputs/` artifacts can be committed while `.venv/` and `.venv312/` remain ignored.
- [x] Clean-copy validation passed in a temporary clean-copy using Python 3.12.
- [x] Clean-copy dependency install passed via `python -m pip install -r requirements.txt`.
- [x] Clean-copy `python -m pytest tests/test_runtime_smoke.py` passed.
- [x] Clean-copy MuJoCo generator smoke passed for `--scenario shelf_pick_metal`.
- [x] Clean-copy HTTP resource check passed for UI HTML, medium runtime JSON, and MP4 asset.
- [x] Temporary clean-copy directory removed after validation.
- [x] Python 3.9 system environment was tested and rejected for final instructions because current MuJoCo wheels require a newer Python on this machine.
- [x] Latest local `.venv312` validation passed with Python 3.12.13.
- [x] Latest runtime data regeneration passed.
- [x] Latest medium benchmark CLI run passed.
- [x] Latest pytest run passed with cache disabled.
- [x] Latest UI JavaScript syntax check passed.
- [x] Latest MuJoCo shelf-pick smoke passed.
- [x] Latest HTTP resource check passed and temporary server was stopped.
- [x] Post-video audit passed after adding `demo.mp4`.

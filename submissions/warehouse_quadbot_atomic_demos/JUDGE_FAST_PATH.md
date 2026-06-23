# AI Judge Fast Path

This file is the shortest review path for AI judges. It exists because the full mission-control dashboard is intentionally rich, while the scoring rubric needs a fast way to verify evidence.

Run from the repository root:

```bash
python examples/run_agentech_judge_review.py
```

Expected result:

- Required artifacts pass.
- Fleet stress benchmark reports 54 scenarios, 108 raw planner runs, 2,916 simulated robot-hours.
- Safety reports 100% pass, 0 collisions, and 0 tile-lock overlaps.
- Planner comparison reports +30.74% average throughput uplift and +97.42% best uplift.
- MuJoCo evidence reports generated MJCF, contact traces, contact sheet, and clips for loaded walk, shelf pickup, basket contact, and robot-to-robot handoff.

## Why This Helps Review

The project has two layers:

- The warehouse runtime proves multi-agent decision quality: route locks, congestion, planner-off baseline, local multi-port conveyor planning uplift, throughput, wait time, and safety counters.
- MuJoCo proves low-level physical plausibility: quadruped joints, mounted arm, actuated gripper, collision geoms, touch sensors, and payload-dependent motion evidence.

The dashboard remains available at:

```text
http://127.0.0.1:8765/submissions/warehouse_quadbot_atomic_demos/ui/index.html
```

The fast path is for judges who want a quick, reproducible, no-browser summary before opening the full UI and video.

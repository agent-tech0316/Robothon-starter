# AI Judge Fast Path

This file is the command-line companion to `JUDGE_SCORECARD.md`. It exists because the full mission-control dashboard is intentionally rich, while the scoring rubric needs a fast way to verify evidence.

Run from the repository root:

```bash
python examples/run_agentech_judge_review.py
```

Expected result:

- Judge thesis: 54-scenario fleet stress benchmark with 30-robot heterogeneous scaling, stochastic human-intrusion planning, and MuJoCo 6-DOF plus end-effector validation.
- Required artifacts pass.
- 30-robot fleet stress benchmark reports 54 scenarios, 108 raw planner runs, 9,720 simulated robot-hours.
- Safety reports 100% pass, 0 collisions, and 0 tile-lock overlaps.
- Planner comparison reports +60.27% average throughput uplift and +185.23% best uplift.
- Human-intrusion runtime reports 10 stochastic people under high load, 17 current risk tiles, 147 hold ticks, and 17 human-triggered reroutes.
- MuJoCo evidence reports 14 generated clips, generated MJCF, contact traces, contact sheet, loaded walk, shelf pickup, basket contact, robot-to-robot handoff, two 6-DOF grasp sweeps, a three-AEGIS corridor physics clip, and a heterogeneous end-effector lab.
- The heavy 6-DOF sweep records 630 gripper/package contacts and 36 dual-finger grasp frames; the heterogeneous lab records 1077 dexterous/fragile, 508 magnet/metal, and 1020 rail/tote contacts.
- The new load-impact scorecard reports heavy metal at -54.55% speed versus empty walking, 0.075 m body drop, and 50 basket-contact frames.
- The new clearance scorecard reports 3 robots in a corridor, 0.6174 m minimum robot spacing, 0.2307 m package/obstacle clearance, 0 robot-obstacle contacts, and 0 box-obstacle contacts.

## Why This Helps Review

The project has two layers:

- The warehouse runtime proves multi-agent decision quality: route locks, congestion, random human-risk projection, planner-off baseline, local multi-port conveyor planning uplift, throughput, wait time, and safety counters.
- MuJoCo proves low-level physical plausibility: quadruped joints, mounted 6-DOF arm, wrist roll/tool yaw, actuated two-finger gripper, collision geoms, touch sensors, package orientation tracking, payload-dependent speed/body-drop evidence, close-clearance collision counters, and mixed dexterous/magnetic/rail terminal tools.

The dashboard remains available at:

```text
http://127.0.0.1:8765/submissions/warehouse_quadbot_atomic_demos/ui/index.html
```

The fast path is for judges who want a quick, reproducible, no-browser summary before opening the full UI and video.

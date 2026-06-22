# MuJoCo Physics Evidence Clips

This module generates short MuJoCo clips for the UI robot-state panel.

It complements the existing visual sprite work by adding explicit MuJoCo
evidence for:

- richer quadruped leg joints
- a six-axis mounted manipulator
- two actuated gripper fingers
- package/gripper collision
- package/basket collision
- package/shelf collision
- robot-to-robot handoff contact
- payload-dependent loading time, leg compression, and walking speed

The shelf height is intentionally normalized: every package is placed at a
reachable warehouse handoff height so this module can focus on manipulation and
contact evidence instead of vertical storage planning.


## Judge Evidence Scorecard

| Evidence axis | Submitted proof | Why it matters |
| --- | --- | --- |
| Robot body depth | AEGIS-style quadruped body, leg joints, mounted arm, gripper slides, collision geoms | Shows MuJoCo is used for robot structure, not only a rendered box |
| Control depth | Position actuators drive legs, arm joints, gripper fingers, and handoff receiver joints | Connects visible actions to actuated robot degrees of freedom |
| Sensor depth | Touch sensors report gripper/package, package/basket, package/shelf, and receiver handoff contacts | Makes contact evidence machine-readable for judges |
| Payload behavior | Cardboard, wood, and metal payloads change gait speed, loading time, and leg compression | Links warehouse SKU weight to physical robot behavior |
| Handoff evidence | Two-robot handoff scene compiles 43 joints, 40 actuators, 27 sensors, and 72 geoms | Keeps the robot-to-robot transfer grounded in MuJoCo physics |

## Run

From the repository root:

```bash
python3 -m pip install mujoco imageio pillow
python3 submissions/warehouse_quadbot_atomic_demos/mujoco_physics_evidence/main.py
```

Outputs are written to:

```text
submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/
```

The main UI handoff file is:

```text
submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/clip_manifest.json
```

Each clip also has a same-name JSON trace with contact totals and sampled robot
state.

On macOS, MuJoCo offscreen rendering may require a normal CoreGraphics/OpenGL
session. If rendering fails in a sandbox, run the same command from a terminal
with access to the desktop graphics context.

## Clip Set

- `rest_idle.mp4`
- `empty_stance.mp4`
- `empty_walk.mp4`
- `loaded_walk_cardboard.mp4`
- `loaded_walk_wood.mp4`
- `loaded_walk_metal.mp4`
- `shelf_pick_cardboard.mp4`
- `shelf_pick_wood.mp4`
- `shelf_pick_metal.mp4`
- `handoff_metal.mp4`

Generated QA preview:

- `outputs/physics_evidence_contact_sheet.png`

## UI Contract

Use `../outputs/physics_evidence/clip_manifest.json` as the source of truth. For each clip it
contains:

- relative video path
- clip kind
- payload key, mass, loading time, gait speed, and leg compression
- generated MJCF scene path
- contact totals for gripper/package, package/basket, package/shelf, and
  receiver-gripper handoff
- MuJoCo depth summary: joint counts, actuator coverage, sensor coverage

Representative compiled model stats:

- Shelf pick scene: 22 joints, 20 actuators, 14 sensors, 46 geoms.
- Handoff scene: 43 joints, 40 actuators, 27 sensors, 72 geoms.
- Loaded walk scene: 22 joints, 20 actuators, 14 sensors, 39 geoms.

## Modeling Notes

The manipulator is procedural MJCF rather than a downloaded mesh asset. Its
joint hierarchy follows the common six-axis industrial arm pattern used by
open-source MuJoCo models such as the MuJoCo Menagerie UR5e:
`shoulder_pan`, `shoulder_lift`, `elbow`, `wrist_1`, `wrist_2`, and `wrist_3`.

The gripper follows the same evidence idea used in Panda/Robotiq-style models:
collision-enabled fingers, fingertip contact regions, and gripper/basket touch
sensors. Relevant public references:

- https://github.com/google-deepmind/mujoco_menagerie/tree/main/universal_robots_ur5e
- https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda
- https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotiq_2f85

This remains an atomic physical evidence layer. It does not implement warehouse
route planning, scheduling, throughput optimization, or a full grasp controller.

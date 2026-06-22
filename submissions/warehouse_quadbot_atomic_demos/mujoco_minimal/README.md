# Minimal MuJoCo Pickup And Delivery

This folder is the smallest MuJoCo validation layer for the warehouse Robothon
submission.

It intentionally contains only:

- one robot
- one shelf
- one SKU
- one pickup
- one delivery

It does not implement warehouse optimization, scheduling, multi-agent behavior,
benchmarking, database state, or UI logic.

## Files

- `scene.xml` defines the warehouse floor, shelf, SKU, delivery bin, sensors,
  actuators, and includes the robot file.
- `robot.xml` defines a minimal actuated warehouse robot with planar slide
  joints, an arm lift joint, and two actuated gripper fingers.
- `main.py` runs one deterministic pickup-and-delivery sequence and writes a
  JSON trace.

## MuJoCo Depth Covered

- MJCF split across `scene.xml` and `robot.xml`.
- Contact geoms for shelf, SKU, delivery bin, gripper fingers, and floor.
- Robot joints for base motion, lift motion, and finger motion.
- Position actuators for robot motion and gripper closure.
- Sensors for SKU pose, gripper pose, robot joint position, arm lift position,
  and gripper touch.
- Physics stepping through MuJoCo.

## Run

From the repository root:

```bash
python3 -m pip install mujoco
python3 submissions/warehouse_quadbot_atomic_demos/mujoco_minimal/main.py
```

The script writes:

```text
submissions/warehouse_quadbot_atomic_demos/outputs/mujoco_minimal/minimal_pick_delivery_trace.json
```

## Scope

This is a low-level validation scene. The full warehouse optimizer should call
or reference this layer only as evidence that a representative physical action
is plausible in MuJoCo.

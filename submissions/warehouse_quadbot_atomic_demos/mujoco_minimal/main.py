from __future__ import annotations

import json
import math
from pathlib import Path

try:
    import mujoco
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: mujoco. Install with `python3 -m pip install mujoco` "
        "or run inside the Robothon starter environment."
    ) from exc


ROOT = Path(__file__).resolve().parent
SCENE = ROOT / "scene.xml"
OUTPUT_DIR = ROOT.parent / "outputs" / "mujoco_minimal"

PICK_X = 0.355
DROP_X = 1.255
DROP_WORLD_X = 0.90
DROP_Y = -0.36


def obj_id(model: mujoco.MjModel, kind: mujoco.mjtObj, name: str) -> int:
    found = mujoco.mj_name2id(model, kind, name)
    if found < 0:
        raise RuntimeError(f"Missing MuJoCo object: {name}")
    return found


def distance(a, b) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def set_free_body_pose(model: mujoco.MjModel, data: mujoco.MjData, joint_id: int, pos) -> None:
    qpos_adr = model.jnt_qposadr[joint_id]
    qvel_adr = model.jnt_dofadr[joint_id]
    data.qpos[qpos_adr : qpos_adr + 3] = pos
    data.qpos[qpos_adr + 3 : qpos_adr + 7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[qvel_adr : qvel_adr + 6] = 0.0


def set_controls(data: mujoco.MjData, actuator_ids: dict[str, int], targets: dict[str, float]) -> None:
    for name, value in targets.items():
        data.ctrl[actuator_ids[name]] = value


def phase_targets(t: float) -> tuple[str, dict[str, float]]:
    if t < 0.25:
        return "settle", {
            "drive_x": 0.0,
            "drive_y": 0.0,
            "lift_arm": 0.02,
            "close_left_finger": 0.0,
            "close_right_finger": 0.0,
        }
    if t < 1.80:
        return "approach_shelf", {
            "drive_x": PICK_X,
            "drive_y": 0.0,
            "lift_arm": 0.075,
            "close_left_finger": 0.0,
            "close_right_finger": 0.0,
        }
    if t < 2.40:
        return "single_pickup", {
            "drive_x": PICK_X,
            "drive_y": 0.0,
            "lift_arm": 0.075,
            "close_left_finger": 0.025,
            "close_right_finger": 0.025,
        }
    if t < 3.10:
        return "clear_shelf", {
            "drive_x": PICK_X,
            "drive_y": DROP_Y,
            "lift_arm": 0.085,
            "close_left_finger": 0.025,
            "close_right_finger": 0.025,
        }
    if t < 4.55:
        return "carry_to_delivery", {
            "drive_x": DROP_X,
            "drive_y": DROP_Y,
            "lift_arm": 0.085,
            "close_left_finger": 0.025,
            "close_right_finger": 0.025,
        }
    if t < 4.95:
        return "single_delivery", {
            "drive_x": DROP_X,
            "drive_y": DROP_Y,
            "lift_arm": 0.02,
            "close_left_finger": 0.025,
            "close_right_finger": 0.025,
        }
    return "release_and_retreat", {
        "drive_x": 1.05,
        "drive_y": DROP_Y,
        "lift_arm": 0.04,
        "close_left_finger": 0.0,
        "close_right_finger": 0.0,
    }


def contact_seen(data: mujoco.MjData, geom_a: int, geom_b: int) -> bool:
    for index in range(data.ncon):
        contact = data.contact[index]
        if {contact.geom1, contact.geom2} == {geom_a, geom_b}:
            return True
    return False


def run() -> dict:
    model = mujoco.MjModel.from_xml_path(str(SCENE))
    data = mujoco.MjData(model)

    actuator_ids = {
        name: obj_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
        for name in (
            "drive_x",
            "drive_y",
            "lift_arm",
            "close_left_finger",
            "close_right_finger",
        )
    }
    gripper_site = obj_id(model, mujoco.mjtObj.mjOBJ_SITE, "gripper_site")
    sku_site = obj_id(model, mujoco.mjtObj.mjOBJ_SITE, "sku_site")
    sku_joint = obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, "sku_free")
    sku_geom = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, "sku_geom")
    shelf_geom = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, "shelf_geom")
    delivery_geom = obj_id(model, mujoco.mjtObj.mjOBJ_GEOM, "delivery_geom")

    trace = []
    attached = False
    picked = False
    delivered = False
    shelf_contacts = 0
    delivery_contacts = 0

    total_steps = int(6.0 / model.opt.timestep)
    for step in range(total_steps):
        t = step * model.opt.timestep
        phase, targets = phase_targets(t)
        set_controls(data, actuator_ids, targets)

        if attached:
            gripper_pos = data.site_xpos[gripper_site]
            set_free_body_pose(
                model,
                data,
                sku_joint,
                [gripper_pos[0], gripper_pos[1], gripper_pos[2] - 0.01],
            )
            mujoco.mj_forward(model, data)

        mujoco.mj_step(model, data)

        gripper_pos = data.site_xpos[gripper_site]
        sku_pos = data.site_xpos[sku_site]
        gripper_to_sku = distance(gripper_pos, sku_pos)

        if contact_seen(data, sku_geom, shelf_geom):
            shelf_contacts += 1
        if contact_seen(data, sku_geom, delivery_geom):
            delivery_contacts += 1

        if phase in {"approach_shelf", "single_pickup"} and t > 0.6 and not attached and gripper_to_sku < 0.06:
            attached = True
            picked = True

        if phase == "release_and_retreat" and attached:
            attached = False

        if step % 40 == 0:
            trace.append(
                {
                    "t": round(t, 3),
                    "phase": phase,
                    "sku_pos": [round(float(v), 4) for v in sku_pos],
                    "gripper_pos": [round(float(v), 4) for v in gripper_pos],
                    "attached": attached,
                }
            )

    final_sku = data.site_xpos[sku_site]
    delivered = (
        picked
        and abs(float(final_sku[0]) - DROP_WORLD_X) < 0.16
        and abs(float(final_sku[1]) - DROP_Y) < 0.10
        and float(final_sku[2]) < 0.14
    )

    summary = {
        "success": bool(delivered),
        "picked": bool(picked),
        "delivered": bool(delivered),
        "final_sku_position": [round(float(v), 4) for v in final_sku],
        "contact_steps": {
            "sku_shelf": shelf_contacts,
            "sku_delivery_bin": delivery_contacts,
        },
        "mujoco_depth_features": {
            "mjcf_files": ["scene.xml", "robot.xml"],
            "collision_geoms": ["shelf_geom", "sku_geom", "delivery_geom", "left_finger_geom", "right_finger_geom"],
            "joints": ["robot_x", "robot_y", "arm_lift", "left_finger", "right_finger", "sku_free"],
            "actuators": list(actuator_ids.keys()),
            "sensors": ["sku_position", "gripper_position", "robot_x_position", "arm_lift_position", "gripper_touch"],
        },
        "trace": trace,
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "minimal_pick_delivery_trace.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "trace"}, indent=2))
    print(f"Wrote {output_path}")
    return summary


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["success"] else 1)

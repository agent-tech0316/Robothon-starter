from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import imageio.v3 as iio
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_URDF = ROOT / "assets" / "Aegis" / "urdf" / "Aegis_mujoco.urdf"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "outputs"
FUTURIST_ASSET_DIR = ROOT / "assets" / "Futurist"


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)

LEGS = ("FL", "FR", "RR", "RL")
BOX_SIZE = (0.115, 0.085, 0.065)
TILE_SIZE = 1.0

BOX_STYLES = {
    "cardboard": {
        "label": "normal cardboard",
        "rgba": [0.72, 0.43, 0.20, 1.0],
        "mass": 0.8,
        "loading_time_s": 1.20,
        "grip_close_s": 0.24,
        "walk_speed_mps": 0.55,
        "leg_compression_m": 0.010,
        "difficulty": "easy",
    },
    "wood": {
        "label": "medium wood",
        "rgba": [0.50, 0.28, 0.11, 1.0],
        "mass": 2.0,
        "loading_time_s": 1.55,
        "grip_close_s": 0.34,
        "walk_speed_mps": 0.43,
        "leg_compression_m": 0.030,
        "difficulty": "medium",
    },
    "metal": {
        "label": "heavy metal",
        "rgba": [0.55, 0.60, 0.64, 1.0],
        "mass": 4.0,
        "loading_time_s": 2.05,
        "grip_close_s": 0.46,
        "walk_speed_mps": 0.31,
        "leg_compression_m": 0.055,
        "difficulty": "hard",
    },
}

LEGACY_SCENARIOS = ("arm_showcase", "shelf_pick", "handoff")
STATE_SCENARIOS = (
    "fleet_physics_corridor",
    "effector_mix_lab",
    "rest_idle",
    "empty_stance",
    "empty_walk",
    "loaded_walk_cardboard",
    "loaded_walk_wood",
    "loaded_walk_metal",
    "shelf_pick_cardboard",
    "shelf_pick_wood",
    "shelf_pick_metal",
    "handoff_metal",
)
ALL_SCENARIOS = LEGACY_SCENARIOS + STATE_SCENARIOS
SCENARIO_DURATIONS = {
    "arm_showcase": 2.2,
    "shelf_pick": 2.3,
    "handoff": 2.3,
    "rest_idle": 1.4,
    "empty_stance": 1.4,
    "empty_walk": 1.8,
    "loaded_walk_cardboard": 1.8,
    "loaded_walk_wood": 1.8,
    "loaded_walk_metal": 1.8,
    "shelf_pick_cardboard": 2.2,
    "shelf_pick_wood": 2.3,
    "shelf_pick_metal": 2.5,
    "handoff_metal": 2.4,
    "fleet_physics_corridor": 3.2,
    "effector_mix_lab": 3.4,
}

FUTURIST_ARM_JOINTS = (
    "idx20_right_arm_joint1",
    "idx21_right_arm_joint2",
    "idx22_right_arm_joint3",
    "idx23_right_arm_joint4",
    "idx24_right_arm_joint5",
    "idx25_right_arm_joint6",
    "idx26_right_arm_joint7",
)
FUTURIST_ARM_LIMITS = (
    (-2.967, 2.967),
    (-1.658062761, 0.523598767),
    (-2.967, 2.967),
    (0.0, 2.094395067),
    (-2.87979, 2.87979),
    (-0.785398, 0.785398),
    (-0.5236, 0.5236),
)
FUTURIST_ARM_MESHES = (
    "right_arm_link01_hull",
    "right_arm_link02_hull",
    "right_arm_link03_hull",
    "right_arm_link04_hull",
    "right_arm_link05_hull",
    "right_arm_link06_hull",
    "right_arm_link07_hull",
    "right_hand_hull",
    "right_wrist_motor_A_hull",
    "right_wrist_motor_B_hull",
    "right_wrist_rod_A_hull",
    "right_wrist_rod_B_hull",
)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if value <= edge0:
        return 0.0
    if value >= edge1:
        return 1.0
    x = (value - edge0) / (edge1 - edge0)
    return x * x * (3.0 - 2.0 * x)


def lerp(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def lerp_pose(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def lerp_tuple(a: tuple[float, ...], b: tuple[float, ...], t: float) -> tuple[float, ...]:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(len(a)))


def scenario_kind(scenario: str) -> str:
    if scenario.startswith("effector_mix"):
        return "effector_mix"
    if scenario.startswith("fleet_physics"):
        return "fleet_physics"
    if scenario.startswith("loaded_walk_"):
        return "loaded_walk"
    if scenario.startswith("shelf_pick_") or scenario == "shelf_pick":
        return "shelf_pick"
    if scenario.startswith("handoff") or scenario == "handoff":
        return "handoff"
    return scenario


def scenario_payload_style(scenario: str) -> str:
    for style in BOX_STYLES:
        if scenario.endswith(f"_{style}"):
            return style
    if scenario == "handoff" or scenario.startswith("fleet_physics") or scenario.startswith("effector_mix"):
        return "metal"
    if scenario == "arm_showcase":
        return "wood"
    return "wood"


def rig_prefix(name: str) -> str:
    return {"receiver_rig": "r_", "third_rig": "t_"}.get(name, "")


def rig_joint_name(name: str, suffix: str) -> str:
    return f"{rig_prefix(name)}rig_{suffix}"


def rig_body_name(name: str, suffix: str) -> str:
    return f"{rig_prefix(name)}rig_{suffix}"


def rig_site_name(name: str, suffix: str) -> str:
    return f"{rig_prefix(name)}rig_{suffix}"


def quat_from_yaw(yaw: float) -> list[float]:
    return [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]


def quat_mul(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> list[float]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ]


def quat_normalize(q: list[float] | np.ndarray) -> list[float]:
    arr = np.asarray(q, dtype=float)
    norm = float(np.linalg.norm(arr))
    if norm <= 1e-9:
        return [1.0, 0.0, 0.0, 0.0]
    return (arr / norm).tolist()


def quat_slerp(a: list[float], b: list[float], t: float) -> list[float]:
    t = float(np.clip(t, 0.0, 1.0))
    qa = np.asarray(quat_normalize(a), dtype=float)
    qb = np.asarray(quat_normalize(b), dtype=float)
    dot = float(np.dot(qa, qb))
    if dot < 0.0:
        qb = -qb
        dot = -dot
    if dot > 0.9995:
        return quat_normalize((qa + t * (qb - qa)).tolist())
    theta_0 = math.acos(float(np.clip(dot, -1.0, 1.0)))
    theta = theta_0 * t
    sin_theta = math.sin(theta)
    sin_theta_0 = math.sin(theta_0)
    s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s1 = sin_theta / sin_theta_0
    return quat_normalize((s0 * qa + s1 * qb).tolist())


def quat_from_yaw_pitch(yaw: float, pitch: float) -> list[float]:
    yaw_q = (math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0))
    pitch_q = (math.cos(pitch / 2.0), 0.0, math.sin(pitch / 2.0), 0.0)
    return quat_mul(yaw_q, pitch_q)


def add_position_actuator(
    spec: mujoco.MjSpec,
    *,
    name: str,
    joint: str,
    kp: float,
    kv: float,
    ctrlrange: tuple[float, float],
) -> None:
    spec.add_actuator(
        name=name,
        trntype=mujoco.mjtTrn.mjTRN_JOINT,
        target=joint,
        gaintype=mujoco.mjtGain.mjGAIN_FIXED,
        gainprm=[kp, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        biastype=mujoco.mjtBias.mjBIAS_AFFINE,
        biasprm=[0, -kp, -kv, 0, 0, 0, 0, 0, 0, 0],
        ctrllimited=True,
        ctrlrange=list(ctrlrange),
    )


def add_jointpos_sensor(spec: mujoco.MjSpec, name: str, joint: str) -> None:
    spec.add_sensor(
        name=name,
        type=mujoco.mjtSensor.mjSENS_JOINTPOS,
        objtype=mujoco.mjtObj.mjOBJ_JOINT,
        objname=joint,
    )


def add_framepos_sensor(spec: mujoco.MjSpec, name: str, site: str) -> None:
    spec.add_sensor(
        name=name,
        type=mujoco.mjtSensor.mjSENS_FRAMEPOS,
        objtype=mujoco.mjtObj.mjOBJ_SITE,
        objname=site,
    )


def add_touch_sensor(spec: mujoco.MjSpec, name: str, site: str) -> None:
    spec.add_sensor(
        name=name,
        type=mujoco.mjtSensor.mjSENS_TOUCH,
        objtype=mujoco.mjtObj.mjOBJ_SITE,
        objname=site,
    )


def set_freejoint_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    joint_name: str,
    pos: tuple[float, float, float],
    yaw: float = 0.0,
) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        return
    qpos_addr = int(model.jnt_qposadr[joint_id])
    data.qpos[qpos_addr : qpos_addr + 3] = pos
    data.qpos[qpos_addr + 3 : qpos_addr + 7] = quat_from_yaw(yaw)


def set_freejoint_pose_quat(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    joint_name: str,
    pos: tuple[float, float, float],
    quat: list[float],
) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        return
    qpos_addr = int(model.jnt_qposadr[joint_id])
    data.qpos[qpos_addr : qpos_addr + 3] = pos
    data.qpos[qpos_addr + 3 : qpos_addr + 7] = quat


def set_joint(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str, value: float) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        return
    qpos_addr = int(model.jnt_qposadr[joint_id])
    if model.jnt_limited[joint_id]:
        low, high = model.jnt_range[joint_id]
        value = float(np.clip(value, low, high))
    data.qpos[qpos_addr] = value


def body_position(model: mujoco.MjModel, data: mujoco.MjData, body_name: str) -> list[float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id < 0:
        return [0.0, 0.0, 0.0]
    return data.xpos[body_id].copy().round(5).tolist()


def body_quat(model: mujoco.MjModel, data: mujoco.MjData, body_name: str) -> list[float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id < 0:
        return [1.0, 0.0, 0.0, 0.0]
    return quat_normalize(data.xquat[body_id].copy())


def site_position(model: mujoco.MjModel, data: mujoco.MjData, site_name: str) -> tuple[float, float, float]:
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if site_id < 0:
        return (0.0, 0.0, 0.0)
    pos = data.site_xpos[site_id]
    return (float(pos[0]), float(pos[1]), float(pos[2]))


def body_local_point(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_name: str,
    local_point: tuple[float, float, float],
) -> tuple[float, float, float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id < 0:
        return local_point
    xmat = data.xmat[body_id].reshape(3, 3)
    xpos = data.xpos[body_id]
    world = xpos + xmat @ np.array(local_point)
    return (float(world[0]), float(world[1]), float(world[2]))


def contact_counters(model: mujoco.MjModel, data: mujoco.MjData) -> dict[str, int]:
    counters = {
        "gripper_box": 0,
        "receiver_gripper_box": 0,
        "box_basket": 0,
        "box_shelf": 0,
        "arm_basket": 0,
        "robot_obstacle": 0,
        "box_obstacle": 0,
        "dexterous_fragile": 0,
        "magnet_metal": 0,
        "rail_tote": 0,
        "total_contacts": int(data.ncon),
    }
    for idx in range(data.ncon):
        contact = data.contact[idx]
        names = [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(contact.geom1)) or "",
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(contact.geom2)) or "",
        ]
        joined = " ".join(names)
        has_box = any(token in joined for token in ("box", "target_box", "transfer_box"))
        has_gripper = "gripper" in joined
        has_basket = "basket" in joined
        has_shelf = "pickup_shelf" in joined
        has_obstacle = "avoidance" in joined
        has_dexterous = "dexterous" in joined
        has_fragile = "fragile_vial" in joined
        has_magnet = "electromagnet" in joined
        has_metal_puck = "metal_puck" in joined
        has_slide_rail = "slide_rail" in joined
        has_rail_tote = "rail_tote" in joined
        has_arm = "arm_" in joined or "gripper" in joined

        if has_gripper and has_box:
            counters["gripper_box"] += 1
        if has_box and ("receiver_rig_gripper" in joined or "r_rig_gripper" in joined):
            counters["receiver_gripper_box"] += 1
        if has_box and has_basket:
            counters["box_basket"] += 1
        if has_box and has_shelf:
            counters["box_shelf"] += 1
        if has_arm and has_basket:
            counters["arm_basket"] += 1
        if has_obstacle and has_box:
            counters["box_obstacle"] += 1
        elif has_obstacle:
            counters["robot_obstacle"] += 1
        if has_dexterous and has_fragile:
            counters["dexterous_fragile"] += 1
        if has_magnet and has_metal_puck:
            counters["magnet_metal"] += 1
        if has_slide_rail and has_rail_tote:
            counters["rail_tote"] += 1
    return counters


def add_tile(world: mujoco.MjsBody, name: str, center: tuple[float, float], rgba: list[float]) -> None:
    world.add_geom(
        name=name,
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[center[0], center[1], 0.004],
        size=[TILE_SIZE / 2.0, TILE_SIZE / 2.0, 0.004],
        rgba=rgba,
        contype=1,
        conaffinity=1,
    )


def add_floor_and_lights(world: mujoco.MjsBody) -> None:
    world.add_geom(
        name="floor",
        type=mujoco.mjtGeom.mjGEOM_PLANE,
        size=[0, 0, 0.05],
        rgba=[0.045, 0.052, 0.060, 1.0],
    )
    world.add_light(pos=[0, -2.2, 3.0], dir=[0.0, 0.45, -1.0], diffuse=[1.0, 1.0, 1.0])
    world.add_light(pos=[-2.0, 1.2, 2.0], dir=[0.6, -0.25, -1.0], diffuse=[0.55, 0.60, 0.70])


def add_payload_box(
    world: mujoco.MjsBody,
    name: str,
    style: str,
    pos: tuple[float, float, float],
) -> None:
    cfg = BOX_STYLES[style]
    body = world.add_body(name=name, pos=pos)
    body.add_freejoint(name=f"{name}_freejoint")
    body.add_geom(
        name=f"{name}_geom",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=BOX_SIZE,
        mass=cfg["mass"],
        rgba=cfg["rgba"],
        friction=[0.8, 0.05, 0.02],
        contype=1,
        conaffinity=1,
    )
    body.add_site(
        name=f"{name}_site",
        pos=[0, 0, 0],
        size=[BOX_SIZE[0], BOX_SIZE[1], BOX_SIZE[2]],
        rgba=[1.0, 1.0, 1.0, 0.04],
    )
    if style == "metal":
        body.add_geom(
            name=f"{name}_shine",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0, 0, BOX_SIZE[2] + 0.002],
            size=[BOX_SIZE[0] * 0.92, BOX_SIZE[1] * 0.92, 0.004],
            rgba=[0.86, 0.90, 0.92, 0.55],
            contype=0,
            conaffinity=0,
        )
    elif style == "cardboard":
        body.add_geom(
            name=f"{name}_tape",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0, 0, BOX_SIZE[2] + 0.003],
            size=[0.012, BOX_SIZE[1] * 1.02, 0.004],
            rgba=[0.92, 0.82, 0.55, 1.0],
            contype=0,
            conaffinity=0,
        )


def add_fragile_vial(world: mujoco.MjsBody, name: str, pos: tuple[float, float, float]) -> None:
    body = world.add_body(name=name, pos=pos)
    body.add_freejoint(name=f"{name}_freejoint")
    body.add_geom(
        name=f"{name}_glass",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        size=[0.042, 0.095],
        mass=0.45,
        rgba=[0.74, 0.95, 1.0, 0.46],
        friction=[1.2, 0.04, 0.02],
        contype=1,
        conaffinity=1,
    )
    body.add_geom(
        name=f"{name}_cap",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        pos=[0.0, 0.0, 0.108],
        size=[0.045, 0.016],
        rgba=[0.95, 0.30, 0.36, 1.0],
        contype=1,
        conaffinity=1,
    )


def add_metal_puck(world: mujoco.MjsBody, name: str, pos: tuple[float, float, float]) -> None:
    body = world.add_body(name=name, pos=pos)
    body.add_freejoint(name=f"{name}_freejoint")
    body.add_geom(
        name=f"{name}_ferrous",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        size=[0.070, 0.038],
        mass=2.8,
        rgba=[0.62, 0.68, 0.72, 1.0],
        friction=[0.9, 0.05, 0.02],
        contype=1,
        conaffinity=1,
    )


def add_rail_tote(world: mujoco.MjsBody, name: str, pos: tuple[float, float, float]) -> None:
    body = world.add_body(name=name, pos=pos)
    body.add_freejoint(name=f"{name}_freejoint")
    body.add_geom(
        name=f"{name}_crate",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=[0.115, 0.070, 0.040],
        mass=1.4,
        rgba=[0.28, 0.66, 0.78, 1.0],
        friction=[0.42, 0.02, 0.01],
        contype=1,
        conaffinity=1,
    )


def add_world_accessory_rig(world: mujoco.MjsBody, name: str) -> None:
    rig = world.add_body(name=name, pos=[0, 0, 0])
    rig.add_freejoint(name=f"{name}_freejoint")

    basket_rgba = [0.02, 0.08, 0.10, 1.0]
    rail_rgba = [0.00, 0.55, 0.70, 1.0]
    rig.add_geom(
        name=f"{name}_basket_floor",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[-0.08, 0.0, 0.205],
        size=[0.17, 0.125, 0.018],
        rgba=basket_rgba,
        contype=1,
        conaffinity=1,
        group=2,
    )
    for suffix, pos, size in [
        ("left_rail", [-0.08, 0.135, 0.265], [0.18, 0.014, 0.070]),
        ("right_rail", [-0.08, -0.135, 0.265], [0.18, 0.014, 0.070]),
        ("front_rail", [0.105, 0.0, 0.265], [0.014, 0.125, 0.070]),
        ("back_rail", [-0.265, 0.0, 0.265], [0.014, 0.125, 0.070]),
    ]:
        rig.add_geom(
            name=f"{name}_basket_{suffix}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=pos,
            size=size,
            rgba=rail_rgba,
            contype=1,
            conaffinity=1,
            group=2,
        )

    rig.add_site(
        name=f"{name}_basket_payload_site",
        pos=[-0.08, 0.0, 0.285],
        size=[0.045],
        rgba=[0.0, 0.9, 0.8, 0.10],
    )
    rig.add_site(
        name=f"{name}_basket_touch_site",
        pos=[-0.08, 0.0, 0.225],
        size=[0.18, 0.12, 0.030],
        rgba=[0.0, 0.9, 0.8, 0.06],
    )

    # Six-axis, front-mounted arm in local rig space: base yaw, shoulder, elbow,
    # wrist pitch, wrist roll, and tool yaw. The rig is scripted to follow the
    # quadruped pose, while its links and fingers keep collision geoms in MuJoCo.
    rig.add_geom(
        name=f"{name}_arm_mast",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0.20, -0.04, 0.25, 0.20, -0.04, 0.44],
        size=[0.024],
        rgba=[0.98, 0.63, 0.12, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    base_yaw = rig.add_body(name=f"{name}_arm_base_yaw", pos=[0.20, -0.04, 0.44])
    base_yaw.add_joint(
        name=f"{name}_base_yaw_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 0, 1],
        limited=True,
        range=[-2.7, 2.7],
        damping=0.25,
    )
    base_yaw.add_geom(
        name=f"{name}_arm_turntable",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        pos=[0.0, 0.0, 0.010],
        size=[0.050, 0.018],
        rgba=[0.10, 0.12, 0.14, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    shoulder = base_yaw.add_body(name=f"{name}_arm_shoulder", pos=[0.0, 0.0, 0.030])
    shoulder.add_joint(
        name=f"{name}_shoulder_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-2.8, 2.9],
        damping=0.25,
    )
    shoulder.add_geom(
        name=f"{name}_arm_upper",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0.0, 0.0, 0.0, 0.18, 0.0, 0.060],
        size=[0.022],
        rgba=[1.00, 0.75, 0.18, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    elbow = shoulder.add_body(name=f"{name}_arm_elbow", pos=[0.18, 0.0, 0.060])
    elbow.add_joint(
        name=f"{name}_elbow_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-1.7, 1.7],
        damping=0.25,
    )
    elbow.add_geom(
        name=f"{name}_arm_forearm",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0.0, 0.0, 0.0, 0.18, 0.0, -0.050],
        size=[0.020],
        rgba=[0.98, 0.55, 0.12, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    wrist = elbow.add_body(name=f"{name}_arm_wrist", pos=[0.18, 0.0, -0.050])
    wrist.add_joint(
        name=f"{name}_wrist_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-1.6, 1.6],
        damping=0.20,
    )
    wrist.add_geom(
        name=f"{name}_arm_wrist_pitch_link",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0.0, 0.0, 0.0, 0.060, 0.0, 0.0],
        size=[0.018],
        rgba=[0.95, 0.42, 0.10, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    wrist_roll = wrist.add_body(name=f"{name}_arm_wrist_roll", pos=[0.060, 0.0, 0.0])
    wrist_roll.add_joint(
        name=f"{name}_wrist_roll_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[1, 0, 0],
        limited=True,
        range=[-3.1, 3.1],
        damping=0.16,
    )
    wrist_roll.add_geom(
        name=f"{name}_arm_roll_collar",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        pos=[0.018, 0.0, 0.0],
        size=[0.024, 0.020],
        rgba=[0.08, 0.09, 0.10, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    tool = wrist_roll.add_body(name=f"{name}_arm_tool", pos=[0.050, 0.0, 0.0])
    tool.add_joint(
        name=f"{name}_tool_yaw_joint",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 0, 1],
        limited=True,
        range=[-2.8, 2.8],
        damping=0.16,
    )
    tool.add_geom(
        name=f"{name}_gripper_palm",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.045, 0.0, 0.0],
        size=[0.036, 0.060, 0.020],
        rgba=[0.08, 0.09, 0.10, 1.0],
        contype=1,
        conaffinity=1,
        group=2,
        mass=0.10,
        friction=[1.1, 0.07, 0.03],
    )
    tool.add_site(
        name=f"{name}_gripper_site",
        pos=[0.142, 0.0, -0.004],
        size=[0.026],
        rgba=[0.0, 0.55, 1.0, 0.14],
    )
    for suffix, sign in [("left", 1.0), ("right", -1.0)]:
        finger = tool.add_body(name=f"{name}_gripper_{suffix}_body", pos=[0.102, sign * 0.102, -0.006])
        finger.add_joint(
            name=f"{name}_{suffix}_finger_slide",
            type=mujoco.mjtJoint.mjJNT_SLIDE,
            axis=[0, 1, 0],
            limited=True,
            range=[-0.030, 0.030],
            damping=0.25,
        )
        finger.add_geom(
            name=f"{name}_gripper_{suffix}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.030, 0.0, 0.0],
            size=[0.066, 0.010, 0.017],
            rgba=[0.04, 0.045, 0.050, 1.0],
            contype=1,
            conaffinity=1,
            group=2,
            mass=0.06,
            friction=[1.35, 0.09, 0.03],
        )
        finger.add_geom(
            name=f"{name}_gripper_{suffix}_pad",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.074, -sign * 0.002, 0.0],
            size=[0.024, 0.006, 0.025],
            rgba=[0.14, 0.15, 0.15, 1.0],
            contype=1,
            conaffinity=1,
            group=2,
            mass=0.03,
            friction=[1.7, 0.11, 0.04],
        )
        finger.add_site(
            name=f"{name}_gripper_{suffix}_touch_site",
            pos=[0.074, -sign * 0.004, 0.0],
            size=[0.034, 0.018, 0.030],
            rgba=[0.0, 0.55, 1.0, 0.08],
        )


def add_shelf(world: mujoco.MjsBody, name: str, x: float, y: float) -> None:
    shelf_rgba = [0.12, 0.17, 0.20, 1.0]
    deck_rgba = [0.25, 0.31, 0.35, 1.0]
    post_offsets = [(-0.33, -0.24), (-0.33, 0.24), (0.33, -0.24), (0.33, 0.24)]
    for idx, (dx, dy) in enumerate(post_offsets):
        world.add_geom(
            name=f"{name}_post_{idx}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[x + dx, y + dy, 0.36],
            size=[0.025, 0.025, 0.35],
            rgba=shelf_rgba,
            contype=1,
            conaffinity=1,
        )
    for idx, z in enumerate((0.18, 0.38, 0.58)):
        world.add_geom(
            name=f"{name}_deck_{idx}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[x, y, z],
            size=[0.36, 0.27, 0.025],
            rgba=deck_rgba,
            friction=[0.9, 0.05, 0.02],
            contype=1,
            conaffinity=1,
        )


def add_quadbot_accessories(spec: mujoco.MjSpec, futurist_asset_dir: Path = FUTURIST_ASSET_DIR) -> None:
    base = spec.body("BASE_LINK")
    if base is None:
        raise ValueError("Missing BASE_LINK in Aegis URDF")

    for mesh in FUTURIST_ARM_MESHES:
        mesh_path = futurist_asset_dir / f"{mesh}.stl"
        if mesh_path.exists() and spec.mesh(f"rig_{mesh}") is None:
            spec.add_mesh(name=f"rig_{mesh}", file=str(mesh_path), scale=[0.62, 0.62, 0.62])

    basket_rgba = [0.04, 0.070, 0.085, 1.0]
    rail_rgba = [0.00, 0.42, 0.55, 1.0]
    base.add_geom(
        name="rig_basket_floor",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[-0.08, 0.0, 0.205],
        size=[0.18, 0.125, 0.018],
        rgba=basket_rgba,
        contype=1,
        conaffinity=1,
        group=2,
        friction=[1.0, 0.06, 0.02],
    )
    for suffix, pos, size in [
        ("left_rail", [-0.08, 0.135, 0.265], [0.18, 0.014, 0.070]),
        ("right_rail", [-0.08, -0.135, 0.265], [0.18, 0.014, 0.070]),
        ("front_rail", [0.105, 0.0, 0.265], [0.014, 0.125, 0.070]),
        ("back_rail", [-0.265, 0.0, 0.265], [0.014, 0.125, 0.070]),
    ]:
        base.add_geom(
            name=f"rig_basket_{suffix}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=pos,
            size=size,
            rgba=rail_rgba,
            contype=1,
            conaffinity=1,
            group=2,
            friction=[1.0, 0.06, 0.02],
        )
    base.add_site(
        name="rig_basket_payload_site",
        pos=[-0.08, 0.0, 0.285],
        size=[0.045],
        rgba=[0.0, 0.9, 0.8, 0.10],
    )
    base.add_site(
        name="rig_basket_touch_site",
        pos=[-0.08, 0.0, 0.225],
        size=[0.18, 0.12, 0.030],
        rgba=[0.0, 0.9, 0.8, 0.06],
    )

    base.add_geom(
        name="rig_arm_mount_mast",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0.20, -0.04, 0.24, 0.20, -0.04, 0.39],
        size=[0.026],
        rgba=[0.08, 0.10, 0.12, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )
    base_link = base.add_body(name="rig_right_arm_link_base", pos=[0.20, -0.04, 0.39])
    base_link.add_geom(
        name="rig_right_arm_base_plate",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        size=[0.052, 0.018],
        rgba=[0.10, 0.12, 0.14, 1.0],
        contype=0,
        conaffinity=0,
        group=2,
    )

    link01 = base_link.add_body(name="rig_right_arm_link01", pos=[0.0, 0.0, 0.070])
    link01.add_joint(
        name="rig_idx20_right_arm_joint1",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 0, 1],
        limited=True,
        range=[-2.967, 2.967],
        damping=0.28,
    )
    link01.add_geom(name="rig_right_arm_link01_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link01_hull", rgba=[0.96, 0.62, 0.14, 1.0], contype=0, conaffinity=0, group=2)
    link01.add_geom(name="rig_right_arm_link01_collision", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0.0, 0.0, 0.0, 0.095, 0.0, 0.030], size=[0.024], rgba=[0.96, 0.62, 0.14, 0.22], contype=0, conaffinity=0, group=3)

    link02 = link01.add_body(name="rig_right_arm_link02", pos=[0.095, 0.0, 0.030])
    link02.add_joint(
        name="rig_idx21_right_arm_joint2",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-1.658062761, 0.523598767],
        damping=0.28,
    )
    link02.add_geom(name="rig_right_arm_link02_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link02_hull", rgba=[1.0, 0.72, 0.18, 1.0], contype=0, conaffinity=0, group=2)
    link02.add_geom(name="rig_right_arm_link02_collision", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0.0, 0.0, 0.0, 0.125, 0.0, 0.020], size=[0.022], rgba=[1.0, 0.72, 0.18, 0.22], contype=0, conaffinity=0, group=3)

    link03 = link02.add_body(name="rig_right_arm_link03", pos=[0.125, 0.0, 0.020])
    link03.add_joint(
        name="rig_idx22_right_arm_joint3",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[1, 0, 0],
        limited=True,
        range=[-2.967, 2.967],
        damping=0.22,
    )
    link03.add_geom(name="rig_right_arm_link03_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link03_hull", rgba=[0.96, 0.55, 0.12, 1.0], contype=0, conaffinity=0, group=2)
    link03.add_geom(name="rig_right_arm_link03_collision", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0.0, 0.0, 0.0, 0.100, 0.0, -0.030], size=[0.020], rgba=[0.96, 0.55, 0.12, 0.22], contype=0, conaffinity=0, group=3)

    link04 = link03.add_body(name="rig_right_arm_link04", pos=[0.100, 0.0, -0.030])
    link04.add_joint(
        name="rig_idx23_right_arm_joint4",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[0.0, 2.094395067],
        damping=0.25,
    )
    link04.add_geom(name="rig_right_arm_link04_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link04_hull", rgba=[0.96, 0.62, 0.14, 1.0], contype=0, conaffinity=0, group=2)
    link04.add_geom(name="rig_right_arm_link04_collision", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0.0, 0.0, 0.0, 0.105, 0.0, -0.025], size=[0.020], rgba=[0.96, 0.62, 0.14, 0.22], contype=0, conaffinity=0, group=3)

    link05 = link04.add_body(name="rig_right_arm_link05", pos=[0.105, 0.0, -0.025])
    link05.add_joint(
        name="rig_idx24_right_arm_joint5",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[1, 0, 0],
        limited=True,
        range=[-2.87979, 2.87979],
        damping=0.20,
    )
    link05.add_geom(name="rig_right_arm_link05_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link05_hull", rgba=[0.95, 0.48, 0.10, 1.0], contype=0, conaffinity=0, group=2)
    link05.add_geom(name="rig_right_arm_link05_collision", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0.0, 0.0, 0.0, 0.075, 0.0, -0.020], size=[0.018], rgba=[0.95, 0.48, 0.10, 0.22], contype=0, conaffinity=0, group=3)
    for suffix, y in (("A", 0.026), ("B", -0.026)):
        motor = link05.add_body(name=f"rig_right_wrist_motor_{suffix}", pos=[0.012, y, -0.020])
        motor.add_geom(name=f"rig_right_wrist_motor_{suffix}_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname=f"rig_right_wrist_motor_{suffix}_hull", rgba=[0.10, 0.12, 0.14, 1.0], contype=0, conaffinity=0, group=2)
        rod = motor.add_body(name=f"rig_right_wrist_rod_{suffix}", pos=[0.044, 0.0, -0.040])
        rod.add_geom(name=f"rig_right_wrist_rod_{suffix}_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname=f"rig_right_wrist_rod_{suffix}_hull", rgba=[0.16, 0.18, 0.20, 1.0], contype=0, conaffinity=0, group=2)

    link06 = link05.add_body(name="rig_right_arm_link06", pos=[0.075, 0.0, -0.020])
    link06.add_joint(
        name="rig_idx25_right_arm_joint6",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-0.785398, 0.785398],
        damping=0.18,
    )
    link06.add_geom(name="rig_right_arm_link06_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link06_hull", rgba=[0.08, 0.09, 0.10, 1.0], contype=0, conaffinity=0, group=2)

    link07 = link06.add_body(name="rig_right_arm_link07", pos=[0.062, 0.0, -0.012])
    link07.add_joint(
        name="rig_idx26_right_arm_joint7",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[1, 0, 0],
        limited=True,
        range=[-0.5236, 0.5236],
        damping=0.18,
    )
    link07.add_geom(name="rig_right_arm_link07_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_arm_link07_hull", rgba=[0.08, 0.09, 0.10, 1.0], contype=0, conaffinity=0, group=2)

    hand = link07.add_body(name="rig_right_hand", pos=[0.052, 0.0, 0.0])
    hand.add_geom(name="rig_right_hand_visual", type=mujoco.mjtGeom.mjGEOM_MESH, meshname="rig_right_hand_hull", rgba=[0.10, 0.11, 0.12, 1.0], contype=0, conaffinity=0, group=2)
    hand.add_geom(
        name="rig_gripper_palm",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.038, 0.0, 0.0],
        size=[0.038, 0.060, 0.022],
        rgba=[0.10, 0.11, 0.12, 1.0],
        contype=1,
        conaffinity=1,
        group=2,
        mass=0.10,
        friction=[1.1, 0.07, 0.03],
    )
    hand.add_site(
        name="rig_gripper_site",
        pos=[0.142, 0.0, -0.004],
        size=[0.026],
        rgba=[0.0, 0.55, 1.0, 0.14],
    )
    for suffix, sign in [("left", 1.0), ("right", -1.0)]:
        finger = hand.add_body(name=f"rig_gripper_{suffix}_body", pos=[0.102, sign * 0.102, -0.006])
        finger.add_joint(
            name=f"rig_{suffix}_finger_slide",
            type=mujoco.mjtJoint.mjJNT_SLIDE,
            axis=[0, 1, 0],
            limited=True,
            range=[-0.030, 0.030],
            damping=0.25,
        )
        finger.add_geom(
            name=f"rig_gripper_{suffix}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.030, 0.0, 0.0],
            size=[0.066, 0.010, 0.017],
            rgba=[0.04, 0.045, 0.050, 1.0],
            contype=1,
            conaffinity=1,
            group=2,
            mass=0.06,
            friction=[1.35, 0.09, 0.03],
        )
        finger.add_geom(
            name=f"rig_gripper_{suffix}_pad",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.074, -sign * 0.002, 0.0],
            size=[0.024, 0.006, 0.025],
            rgba=[0.14, 0.15, 0.15, 1.0],
            contype=1,
            conaffinity=1,
            group=2,
            mass=0.03,
            friction=[1.7, 0.11, 0.04],
        )
        finger.add_site(
            name=f"rig_gripper_{suffix}_touch_site",
            pos=[0.074, -sign * 0.004, 0.0],
            size=[0.034, 0.018, 0.030],
            rgba=[0.0, 0.55, 1.0, 0.08],
        )


def build_aegis_spec(urdf_path: Path, *, accessories: bool) -> mujoco.MjSpec:
    spec = mujoco.MjSpec.from_file(str(urdf_path))
    spec.visual.global_.offwidth = 1280
    spec.visual.global_.offheight = 720
    spec.option.timestep = 0.002
    spec.option.gravity = [0.0, 0.0, -9.81]
    base = spec.body("BASE_LINK")
    if base is None:
        raise ValueError("Missing BASE_LINK in Aegis URDF")
    base.add_freejoint(name="floating_base_joint")
    if accessories:
        futurist_asset_dir = urdf_path.resolve().parents[2] / "Futurist"
        add_quadbot_accessories(spec, futurist_asset_dir)
    return spec


def add_aegis_leg_actuators_and_sensors(spec: mujoco.MjSpec, prefix: str = "") -> None:
    ranges = {
        "ABAD_JOINT": (-0.75, 0.75),
        "HIP_JOINT": (-1.25, 1.45),
        "KNEE_JOINT": (-2.20, -0.15),
    }
    for leg in LEGS:
        for suffix, ctrlrange in ranges.items():
            joint = f"{prefix}{leg}_{suffix}"
            add_position_actuator(spec, name=f"{joint}_position", joint=joint, kp=120, kv=10, ctrlrange=ctrlrange)
            add_jointpos_sensor(spec, name=f"{joint}_pos", joint=joint)


def add_rig_actuators_and_sensors(spec: mujoco.MjSpec, prefix: str = "") -> None:
    ranges = {
        **dict(zip(FUTURIST_ARM_JOINTS, FUTURIST_ARM_LIMITS)),
        "left_finger_slide": (-0.030, 0.030),
        "right_finger_slide": (-0.030, 0.030),
    }
    for joint_suffix, ctrlrange in ranges.items():
        joint = f"{prefix}rig_{joint_suffix}"
        add_position_actuator(spec, name=f"{joint}_position", joint=joint, kp=150, kv=10, ctrlrange=ctrlrange)
        add_jointpos_sensor(spec, name=f"{joint}_pos", joint=joint)

    add_framepos_sensor(spec, name=f"{prefix}rig_gripper_framepos", site=f"{prefix}rig_gripper_site")
    add_framepos_sensor(spec, name=f"{prefix}rig_basket_framepos", site=f"{prefix}rig_basket_payload_site")
    add_touch_sensor(spec, name=f"{prefix}rig_left_finger_touch", site=f"{prefix}rig_gripper_left_touch_site")
    add_touch_sensor(spec, name=f"{prefix}rig_right_finger_touch", site=f"{prefix}rig_gripper_right_touch_site")
    add_touch_sensor(spec, name=f"{prefix}rig_basket_touch", site=f"{prefix}rig_basket_touch_site")


def add_end_effector_variant(spec: mujoco.MjSpec, prefix: str, variant: str) -> None:
    hand = spec.body(f"{prefix}rig_right_hand")
    if hand is None:
        return
    if variant == "dexterous_hand":
        hand.add_site(name=f"{prefix}rig_dexterous_tool_site", pos=[0.152, 0.0, -0.006], size=[0.020], rgba=[0.80, 0.95, 1.0, 0.18])
        hand.add_geom(name=f"{prefix}rig_dexterous_palm_pad", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.104, 0.0, -0.006], size=[0.030, 0.052, 0.018], rgba=[0.12, 0.16, 0.18, 1.0], contype=1, conaffinity=1, group=2, mass=0.04, friction=[1.9, 0.12, 0.05])
        for idx, (name, y, z, angle) in enumerate([("thumb", -0.050, -0.018, -0.35), ("index", -0.020, 0.020, 0.10), ("middle", 0.016, 0.022, 0.02), ("ring", 0.050, 0.014, -0.08)]):
            finger = hand.add_body(name=f"{prefix}rig_dexterous_{name}_body", pos=[0.126, y, z])
            finger.add_geom(name=f"{prefix}rig_dexterous_{name}", type=mujoco.mjtGeom.mjGEOM_CAPSULE, fromto=[0.0, 0.0, 0.0, 0.065, 0.012 * math.sin(angle), 0.014 * math.cos(angle)], size=[0.010], rgba=[0.22, 0.25, 0.27, 1.0], contype=1, conaffinity=1, group=2, mass=0.025, friction=[2.1, 0.13, 0.05])
            finger.add_geom(name=f"{prefix}rig_dexterous_{name}_tip", type=mujoco.mjtGeom.mjGEOM_SPHERE, pos=[0.070, 0.012 * math.sin(angle), 0.014 * math.cos(angle)], size=[0.014], rgba=[0.06, 0.07, 0.08, 1.0], contype=1, conaffinity=1, group=2, mass=0.012, friction=[2.3, 0.14, 0.05])
    elif variant == "electromagnet":
        hand.add_site(name=f"{prefix}rig_magnet_tool_site", pos=[0.160, 0.0, -0.004], size=[0.022], rgba=[0.40, 0.70, 1.0, 0.20])
        hand.add_geom(name=f"{prefix}rig_electromagnet_core", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0.125, 0.0, -0.004], size=[0.052, 0.018], rgba=[0.10, 0.16, 0.22, 1.0], contype=1, conaffinity=1, group=2, mass=0.12, friction=[1.4, 0.07, 0.03])
        hand.add_geom(name=f"{prefix}rig_electromagnet_field", type=mujoco.mjtGeom.mjGEOM_CYLINDER, pos=[0.154, 0.0, -0.004], size=[0.078, 0.006], rgba=[0.20, 0.70, 1.0, 0.18], contype=0, conaffinity=0, group=2)
    elif variant == "slide_rail":
        hand.add_site(name=f"{prefix}rig_slide_rail_site", pos=[0.150, 0.0, -0.030], size=[0.020], rgba=[0.20, 1.0, 0.75, 0.20])
        hand.add_geom(name=f"{prefix}rig_slide_rail_left", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.120, 0.034, -0.030], size=[0.094, 0.006, 0.009], rgba=[0.04, 0.20, 0.18, 1.0], contype=1, conaffinity=1, group=2, mass=0.05, friction=[0.25, 0.01, 0.01])
        hand.add_geom(name=f"{prefix}rig_slide_rail_right", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.120, -0.034, -0.030], size=[0.094, 0.006, 0.009], rgba=[0.04, 0.20, 0.18, 1.0], contype=1, conaffinity=1, group=2, mass=0.05, friction=[0.25, 0.01, 0.01])
        hand.add_geom(name=f"{prefix}rig_slide_rail_carriage", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.156, 0.0, -0.018], size=[0.040, 0.050, 0.010], rgba=[0.10, 0.55, 0.45, 1.0], contype=1, conaffinity=1, group=2, mass=0.05, friction=[0.35, 0.02, 0.01])


def add_scene_common(spec: mujoco.MjSpec, scenario: str) -> None:
    world = spec.worldbody
    add_floor_and_lights(world)
    kind = scenario_kind(scenario)
    payload_style = scenario_payload_style(scenario)

    if kind == "arm_showcase":
        for center, name, color in [
            ((-0.75, 0.0), "tile_inventory", [0.075, 0.105, 0.125, 1.0]),
            ((0.25, 0.0), "tile_quadbot", [0.085, 0.135, 0.120, 1.0]),
            ((1.25, 0.0), "tile_output", [0.120, 0.100, 0.070, 1.0]),
        ]:
            add_tile(world, name, center, color)
        add_payload_box(world, "cardboard_box", "cardboard", (-0.85, -0.18, 0.12))
        add_payload_box(world, "wood_box", "wood", (-0.55, 0.0, 0.12))
        add_payload_box(world, "metal_box", "metal", (-0.85, 0.18, 0.12))

    elif kind == "shelf_pick":
        add_tile(world, "tile_shelf", (-0.5, 0.0), [0.075, 0.100, 0.125, 1.0])
        add_tile(world, "tile_quadbot", (0.5, 0.0), [0.085, 0.135, 0.120, 1.0])
        add_shelf(world, "pickup_shelf", -0.5, 0.0)
        add_payload_box(world, "target_box", payload_style, (-0.16, -0.02, 0.472))

    elif kind == "handoff":
        add_tile(world, "tile_sender", (-0.55, 0.0), [0.105, 0.115, 0.145, 1.0])
        add_tile(world, "tile_receiver", (0.55, 0.0), [0.085, 0.135, 0.110, 1.0])
        add_payload_box(world, "transfer_box", payload_style, (-0.63, 0.0, 0.625))

    elif kind == "effector_mix":
        for center, name, color in [
            ((-1.25, 0.72), "tile_dexterous_fragile", [0.075, 0.105, 0.125, 1.0]),
            ((0.00, -0.60), "tile_magnet_metal", [0.090, 0.110, 0.135, 1.0]),
            ((1.25, 0.72), "tile_slide_rail", [0.085, 0.135, 0.120, 1.0]),
        ]:
            add_tile(world, name, center, color)
        add_fragile_vial(world, "fragile_vial", (-1.02, 0.72, 0.58))
        add_metal_puck(world, "metal_puck", (0.20, -0.60, 0.54))
        add_rail_tote(world, "rail_tote", (1.02, 0.72, 0.50))
        world.add_geom(name="fragile_station", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[-1.02, 0.72, 0.10], size=[0.20, 0.16, 0.030], rgba=[0.20, 0.30, 0.34, 1.0], contype=1, conaffinity=1)
        world.add_geom(name="metal_station", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[0.20, -0.60, 0.10], size=[0.18, 0.18, 0.030], rgba=[0.24, 0.25, 0.27, 1.0], contype=1, conaffinity=1)
        world.add_geom(name="rail_station", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[1.02, 0.72, 0.10], size=[0.22, 0.15, 0.030], rgba=[0.18, 0.32, 0.30, 1.0], contype=1, conaffinity=1)

    elif kind == "fleet_physics":
        for x in (-1.5, -0.75, 0.0, 0.75, 1.5):
            for y in (-0.5, 0.5):
                color = [0.070, 0.105, 0.125, 1.0] if y < 0 else [0.085, 0.135, 0.120, 1.0]
                add_tile(world, f"tile_corridor_{x}_{y}", (x, y), color)
        world.add_geom(
            name="avoidance_pillar",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.0, 0.0, 0.30],
            size=[0.16, 0.20, 0.30],
            rgba=[0.45, 0.16, 0.10, 1.0],
            friction=[1.0, 0.08, 0.03],
            contype=1,
            conaffinity=1,
        )
        world.add_geom(
            name="avoidance_clearance_ring",
            type=mujoco.mjtGeom.mjGEOM_CYLINDER,
            pos=[0.0, 0.0, 0.018],
            size=[0.46, 0.010],
            rgba=[1.0, 0.65, 0.08, 0.20],
            contype=0,
            conaffinity=0,
        )
        add_payload_box(world, "target_box", payload_style, (-1.25, 0.32, 0.62))

    elif kind in {"rest_idle", "empty_stance", "empty_walk", "loaded_walk"}:
        add_tile(world, "tile_quadbot", (0.0, 0.0), [0.085, 0.135, 0.120, 1.0])
        if kind in {"empty_walk", "loaded_walk"}:
            add_tile(world, "tile_progress", (0.65, 0.0), [0.105, 0.115, 0.145, 1.0])
        if kind == "loaded_walk":
            add_payload_box(world, "target_box", payload_style, (0.0, 0.0, 0.625))


def style_model_for_video(model: mujoco.MjModel) -> None:
    body_shell = np.array([0.92, 0.95, 1.00, 1.0], dtype=np.float32)
    hip_shell = np.array([0.95, 0.47, 0.12, 1.0], dtype=np.float32)
    leg_shell = np.array([0.18, 0.22, 0.28, 1.0], dtype=np.float32)
    foot_shell = np.array([0.05, 0.06, 0.07, 1.0], dtype=np.float32)

    for geom_id in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id) or ""
        if (
            name.startswith("tile_")
            or name.startswith("pickup_shelf")
            or name.startswith("cardboard_box")
            or name.startswith("wood_box")
            or name.startswith("metal_box")
            or name.startswith("target_box")
            or name.startswith("transfer_box")
            or name.startswith("avoidance")
            or name.startswith("fragile_vial")
            or name.startswith("metal_puck")
            or name.startswith("rail_tote")
            or name.endswith("_station")
            or "dexterous" in name
            or "electromagnet" in name
            or "slide_rail" in name
            or "basket" in name
            or "arm_" in name
            or "gripper" in name
            or model.geom_group[geom_id] == 4
            or name == "floor"
        ):
            continue

        if model.geom_group[geom_id] == 0:
            model.geom_rgba[geom_id] = [0.0, 0.0, 0.0, 0.0]
            continue

        body_name = mujoco.mj_id2name(
            model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[geom_id])
        ) or ""
        if "BASE_LINK" in body_name:
            model.geom_rgba[geom_id] = body_shell
        elif "ABAD" in body_name or "HIP" in body_name:
            model.geom_rgba[geom_id] = hip_shell
        elif "FOOT" in body_name:
            model.geom_rgba[geom_id] = foot_shell
        else:
            model.geom_rgba[geom_id] = leg_shell


def build_model(urdf_path: Path, scenario: str) -> mujoco.MjModel:
    spec = build_aegis_spec(urdf_path, accessories=True)
    kind = scenario_kind(scenario)
    if kind in {"handoff", "fleet_physics", "effector_mix"}:
        receiver_frame = spec.worldbody.add_frame(name="receiver_attach_frame", pos=[0.0, 0.0, 0.0])
        receiver = build_aegis_spec(urdf_path, accessories=True)
        spec.attach(receiver, prefix="r_", frame=receiver_frame)
    if kind in {"fleet_physics", "effector_mix"}:
        traffic_frame = spec.worldbody.add_frame(name="traffic_attach_frame", pos=[0.0, 0.0, 0.0])
        traffic = build_aegis_spec(urdf_path, accessories=True)
        spec.attach(traffic, prefix="t_", frame=traffic_frame)

    if kind == "effector_mix":
        add_end_effector_variant(spec, "", "dexterous_hand")
        add_end_effector_variant(spec, "r_", "electromagnet")
        add_end_effector_variant(spec, "t_", "slide_rail")
    add_scene_common(spec, scenario)
    add_aegis_leg_actuators_and_sensors(spec, "")
    if kind in {"handoff", "fleet_physics", "effector_mix"}:
        add_aegis_leg_actuators_and_sensors(spec, "r_")
    if kind in {"fleet_physics", "effector_mix"}:
        add_aegis_leg_actuators_and_sensors(spec, "t_")
    add_rig_actuators_and_sensors(spec, "")
    if kind in {"handoff", "fleet_physics", "effector_mix"}:
        add_rig_actuators_and_sensors(spec, "r_")
    if kind in {"fleet_physics", "effector_mix"}:
        add_rig_actuators_and_sensors(spec, "t_")
    model = spec.compile()
    style_model_for_video(model)
    return model


def set_aegis_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    prefix: str = "",
    pos: tuple[float, float, float],
    yaw: float,
    time_s: float,
    moving: bool = False,
    leg_compression: float = 0.0,
    gait_speed: float = 1.0,
) -> None:
    settle = smoothstep(0.0, 0.5, time_s)
    bob = (0.010 if moving else 0.004) * math.sin(2.0 * math.pi * (1.6 if moving else 0.65) * time_s)
    adjusted_pos = (pos[0], pos[1], pos[2] - leg_compression + bob)
    set_freejoint_pose(model, data, f"{prefix}floating_base_joint", adjusted_pos, yaw)
    gait = 2.0 * math.pi * 0.6 * max(0.25, gait_speed) * time_s
    stride = 0.075 if moving else 0.025
    hip_base = 0.58 + 2.1 * leg_compression
    knee_base = -1.08 - 3.1 * leg_compression
    for idx, leg in enumerate(LEGS):
        phase = 0.0 if leg in {"FL", "RR"} else math.pi
        wave = math.sin(gait + phase + idx * 0.4)
        counter = math.cos(gait + phase)
        idle = stride * wave
        set_joint(model, data, f"{prefix}{leg}_ABAD_JOINT", settle * (0.06 * math.sin(gait + phase)))
        set_joint(model, data, f"{prefix}{leg}_HIP_JOINT", hip_base + idle)
        set_joint(model, data, f"{prefix}{leg}_KNEE_JOINT", knee_base - (0.055 if moving else 0.015) * max(0.0, counter))


def set_arm_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    prefix: str = "",
    yaw: float,
    shoulder: float,
    elbow: float,
    wrist: float,
) -> None:
    set_joint(model, data, f"{prefix}arm_yaw", yaw)
    set_joint(model, data, f"{prefix}arm_shoulder_joint", shoulder)
    set_joint(model, data, f"{prefix}arm_elbow_joint", elbow)
    set_joint(model, data, f"{prefix}arm_wrist_joint", wrist)


def set_rig_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    name: str,
    pos: tuple[float, float, float],
    yaw: float,
) -> None:
    # The arm and basket are now true BASE_LINK children on the AEGIS model.
    # Their world pose comes from the quadruped floating base, so no extra
    # freejoint sync is needed here.
    return


def set_rig_arm_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    name: str,
    shoulder: float,
    elbow: float,
    wrist: float,
    base_yaw: float = 0.0,
    wrist_roll: float = 0.0,
    tool_yaw: float = 0.0,
) -> None:
    values = (
        base_yaw,
        shoulder,
        0.35 * base_yaw + 0.25 * wrist_roll,
        elbow,
        wrist_roll,
        wrist,
        tool_yaw,
    )
    for suffix, value in zip(FUTURIST_ARM_JOINTS, values):
        set_joint(model, data, rig_joint_name(name, suffix), value)


def set_rig_arm_pose_tuple(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    *,
    name: str,
    pose: tuple[float, ...],
) -> None:
    if len(pose) == 6:
        base_yaw, shoulder, elbow, wrist, wrist_roll, tool_yaw = pose
        pose = (base_yaw, shoulder, 0.35 * base_yaw + 0.25 * wrist_roll, elbow, wrist_roll, wrist, tool_yaw)
    if len(pose) != len(FUTURIST_ARM_JOINTS):
        raise ValueError(f"Expected {len(FUTURIST_ARM_JOINTS)} arm values, got {len(pose)}")
    for suffix, value in zip(FUTURIST_ARM_JOINTS, pose):
        set_joint(model, data, rig_joint_name(name, suffix), value)


def set_rig_gripper(model: mujoco.MjModel, data: mujoco.MjData, *, name: str, closed: float) -> None:
    closed = float(np.clip(closed, 0.0, 1.0))
    open_left = 0.010
    open_right = -0.010
    closed_left = -0.020
    closed_right = 0.020
    set_joint(model, data, rig_joint_name(name, "left_finger_slide"), open_left * (1.0 - closed) + closed_left * closed)
    set_joint(model, data, rig_joint_name(name, "right_finger_slide"), open_right * (1.0 - closed) + closed_right * closed)


def apply_arm_showcase(model: mujoco.MjModel, data: mujoco.MjData, time_s: float, duration_s: float) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    set_aegis_pose(model, data, pos=(0.25, 0.0, 0.34), yaw=0.0, time_s=time_s)
    set_rig_pose(model, data, name="sender_rig", pos=(0.25, 0.0, 0.34), yaw=0.0)
    wave = math.sin(2.0 * math.pi * time_s / duration_s)
    set_rig_arm_pose(
        model,
        data,
        name="sender_rig",
        shoulder=-0.10 + 0.20 * wave,
        elbow=0.35 + 0.25 * math.sin(1.4 * time_s),
        wrist=0.35 * math.sin(2.0 * time_s),
    )
    set_rig_gripper(model, data, name="sender_rig", closed=0.55 + 0.45 * smoothstep(1.0, 2.0, time_s))
    set_arm_pose(
        model,
        data,
        yaw=0.30 * math.sin(1.3 * time_s),
        shoulder=-0.15 + 0.25 * wave,
        elbow=0.35 + 0.35 * smoothstep(1.0, duration_s - 1.0, time_s),
        wrist=0.25 * math.sin(2.1 * time_s),
    )

    set_freejoint_pose(model, data, "cardboard_box_freejoint", (-0.85, -0.18, 0.12), 0.0)
    set_freejoint_pose(model, data, "wood_box_freejoint", (0.17, 0.0, 0.63), 0.0)
    set_freejoint_pose(model, data, "metal_box_freejoint", (-0.85, 0.18, 0.12), 0.0)
    mujoco.mj_forward(model, data)


def apply_shelf_pick(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    time_s: float,
    duration_s: float,
    style: str = "wood",
) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    cfg = BOX_STYLES[style]
    set_aegis_pose(
        model,
        data,
        pos=(0.50, 0.0, 0.34),
        yaw=math.pi,
        time_s=time_s,
        leg_compression=float(cfg["leg_compression_m"]) * 0.45,
        gait_speed=0.55,
    )
    set_rig_pose(model, data, name="sender_rig", pos=(0.50, 0.0, 0.34), yaw=math.pi)

    reach = smoothstep(0.06, 0.36, time_s)
    close_start = 0.34
    close_end = min(duration_s - 1.05, close_start + float(cfg["grip_close_s"]))
    lift_start = close_end + 0.06
    carry_start = min(duration_s - 0.58, lift_start + 0.34 * float(cfg["loading_time_s"]))
    release_start = max(carry_start + 0.18, duration_s - 0.42)
    grasp = smoothstep(close_start, close_end, time_s)
    lift = smoothstep(lift_start, carry_start, time_s)
    carry = smoothstep(carry_start, release_start, time_s)
    release = smoothstep(release_start, duration_s - 0.05, time_s)

    idle_pose = (0.00, 0.48, -0.48, 0.10, 0.00, 0.00)
    reach_pose = (-0.05, 0.03, 0.78, -0.12, 0.18, -0.10)
    lift_pose = (0.05, -0.48, 0.43, 0.05, 0.08, 0.18)
    carry_pose = (0.12, -2.25, -0.72, 0.18, 0.16, 0.32)
    lower_pose = (0.10, -2.08, -0.98, 0.05, 0.02, 0.08)
    pose = lerp_tuple(idle_pose, reach_pose, reach)
    pose = lerp_tuple(pose, lift_pose, lift)
    pose = lerp_tuple(pose, carry_pose, carry)
    pose = lerp_tuple(pose, lower_pose, release)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=pose)
    set_rig_gripper(
        model,
        data,
        name="sender_rig",
        closed=grasp * (1.0 - 0.85 * release),
    )

    mujoco.mj_forward(model, data)
    shelf_pos = (-0.16, -0.02, 0.472)
    basket_site = site_position(model, data, rig_site_name("sender_rig", "basket_payload_site"))
    basket_pos = (basket_site[0], basket_site[1], basket_site[2] - 0.006)
    shelf_quat = quat_from_yaw_pitch(0.0, 0.0)
    basket_quat = quat_from_yaw_pitch(math.pi, 0.0)
    gripper_box_pos = site_position(model, data, rig_site_name("sender_rig", "gripper_site"))
    gripper_box_pos = (gripper_box_pos[0], gripper_box_pos[1], gripper_box_pos[2] - 0.006)
    gripper_box_quat = body_quat(model, data, rig_body_name("sender_rig", "right_hand"))
    if grasp < 1.0:
        grasp_blend = max(0.0, (grasp - 0.18) / 0.82)
        box_pos = lerp(shelf_pos, gripper_box_pos, grasp_blend)
        box_quat = quat_slerp(shelf_quat, gripper_box_quat, grasp_blend)
    elif release < 1.0:
        carry_lift = (gripper_box_pos[0], gripper_box_pos[1], gripper_box_pos[2] + 0.025 * lift)
        box_pos = lerp(carry_lift, basket_pos, release)
        box_quat = quat_slerp(gripper_box_quat, basket_quat, release)
    else:
        box_pos = basket_pos
        box_quat = basket_quat
    set_freejoint_pose_quat(model, data, "target_box_freejoint", box_pos, box_quat)
    mujoco.mj_forward(model, data)


def apply_handoff(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    time_s: float,
    duration_s: float,
    style: str = "metal",
) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    cfg = BOX_STYLES[style]
    compression = float(cfg["leg_compression_m"]) * 0.50
    set_aegis_pose(model, data, prefix="", pos=(-0.55, 0.0, 0.34), yaw=0.0, time_s=time_s, leg_compression=compression)
    set_aegis_pose(
        model,
        data,
        prefix="r_",
        pos=(0.55, 0.0, 0.34),
        yaw=math.pi,
        time_s=time_s,
        leg_compression=compression * 0.8,
    )
    set_rig_pose(model, data, name="sender_rig", pos=(-0.55, 0.0, 0.34), yaw=0.0)
    set_rig_pose(model, data, name="receiver_rig", pos=(0.55, 0.0, 0.34), yaw=math.pi)

    sender_lift = smoothstep(0.08, 0.48, time_s)
    sender_reach = smoothstep(0.42, 1.02, time_s)
    transfer = smoothstep(0.92, 1.42, time_s)
    receive = smoothstep(1.18, 1.66, time_s)
    lower = smoothstep(1.58, duration_s - 0.08, time_s)

    sender_idle = (0.00, -2.05, -0.82, 0.04, 0.00, 0.00)
    sender_meet = (0.08, 0.05, 0.50, -0.10, 0.08, -0.10)
    sender_release = (0.12, 0.10, 0.78, -0.16, 0.12, -0.02)
    sender_return = (0.00, -1.95, -0.80, 0.05, 0.00, 0.00)
    sender_pose = lerp_tuple(sender_idle, sender_meet, max(sender_lift, sender_reach))
    sender_pose = lerp_tuple(sender_pose, sender_release, transfer)
    sender_pose = lerp_tuple(sender_pose, sender_return, lower)

    receiver_ready = (-0.08, 0.08, 0.70, -0.12, -0.10, 0.12)
    receiver_basket = (0.08, -2.18, -0.88, 0.10, 0.05, 0.08)
    receiver_pose = lerp_tuple(receiver_ready, receiver_basket, lower)

    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=sender_pose)
    set_rig_arm_pose_tuple(model, data, name="receiver_rig", pose=receiver_pose)
    set_rig_gripper(model, data, name="sender_rig", closed=1.0 - 0.90 * smoothstep(1.05, 1.42, time_s))
    set_rig_gripper(
        model,
        data,
        name="receiver_rig",
        closed=smoothstep(0.88, 1.32, time_s) * (1.0 - 0.85 * smoothstep(duration_s - 0.32, duration_s - 0.06, time_s)),
    )

    mujoco.mj_forward(model, data)
    sender_basket_site = site_position(model, data, rig_site_name("sender_rig", "basket_payload_site"))
    receiver_basket_site = site_position(model, data, rig_site_name("receiver_rig", "basket_payload_site"))
    sender_basket = (sender_basket_site[0], sender_basket_site[1], sender_basket_site[2] - 0.006)
    receiver_basket = (receiver_basket_site[0], receiver_basket_site[1], receiver_basket_site[2] - 0.006)
    sender_grip_pos = site_position(model, data, rig_site_name("sender_rig", "gripper_site"))
    receiver_grip_pos = site_position(model, data, rig_site_name("receiver_rig", "gripper_site"))
    sender_grip_pos = (sender_grip_pos[0], sender_grip_pos[1], sender_grip_pos[2] - 0.006)
    receiver_grip_pos = (receiver_grip_pos[0], receiver_grip_pos[1], receiver_grip_pos[2] - 0.006)
    sender_grip_quat = body_quat(model, data, rig_body_name("sender_rig", "right_hand"))
    receiver_grip_quat = body_quat(model, data, rig_body_name("receiver_rig", "right_hand"))
    sender_basket_quat = quat_from_yaw_pitch(0.0, 0.0)
    receiver_basket_quat = quat_from_yaw_pitch(math.pi, 0.0)
    release = smoothstep(duration_s - 0.32, duration_s - 0.06, time_s)
    if sender_lift < 1.0:
        box_pos = lerp(sender_basket, sender_grip_pos, sender_lift)
        box_quat = quat_slerp(sender_basket_quat, sender_grip_quat, sender_lift)
    elif sender_reach < 1.0:
        box_pos = sender_grip_pos
        box_quat = sender_grip_quat
    elif transfer < 1.0:
        box_pos = lerp(sender_grip_pos, receiver_grip_pos, transfer)
        box_quat = quat_slerp(sender_grip_quat, receiver_grip_quat, transfer)
    elif receive < 1.0:
        box_pos = receiver_grip_pos
        box_quat = receiver_grip_quat
    elif release < 1.0:
        box_pos = receiver_grip_pos
        box_quat = receiver_grip_quat
    else:
        box_pos = receiver_basket
        box_quat = receiver_basket_quat
    if release > 0.0:
        box_pos = lerp(box_pos, receiver_basket, release)
        box_quat = quat_slerp(box_quat, receiver_basket_quat, release)
    set_freejoint_pose_quat(model, data, "transfer_box_freejoint", box_pos, box_quat)
    mujoco.mj_forward(model, data)


def apply_rest_idle(model: mujoco.MjModel, data: mujoco.MjData, time_s: float, duration_s: float) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    set_aegis_pose(
        model,
        data,
        pos=(0.0, 0.0, 0.335),
        yaw=0.0,
        time_s=time_s,
        leg_compression=0.060,
        gait_speed=0.30,
    )
    set_rig_pose(model, data, name="sender_rig", pos=(0.0, 0.0, 0.335), yaw=0.0)
    folded = (0.00, -1.95, -0.88, 0.58, 0.00, 0.00)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=folded)
    set_rig_gripper(model, data, name="sender_rig", closed=0.0)
    mujoco.mj_forward(model, data)


def apply_empty_stance(model: mujoco.MjModel, data: mujoco.MjData, time_s: float, duration_s: float) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    set_aegis_pose(
        model,
        data,
        pos=(0.0, 0.0, 0.345),
        yaw=0.0,
        time_s=time_s,
        leg_compression=0.016,
        gait_speed=0.55,
    )
    set_rig_pose(model, data, name="sender_rig", pos=(0.0, 0.0, 0.345), yaw=0.0)
    ready = (0.04, -1.25, -0.48, 0.36, 0.10 * math.sin(3.0 * time_s), 0.0)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=ready)
    set_rig_gripper(model, data, name="sender_rig", closed=0.12)
    mujoco.mj_forward(model, data)


def apply_empty_walk(model: mujoco.MjModel, data: mujoco.MjData, time_s: float, duration_s: float) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    progress = smoothstep(0.0, duration_s, time_s)
    x = -0.28 + 0.72 * progress
    set_aegis_pose(
        model,
        data,
        pos=(x, 0.0, 0.345),
        yaw=0.0,
        time_s=time_s,
        moving=True,
        leg_compression=0.010,
        gait_speed=1.10,
    )
    set_rig_pose(model, data, name="sender_rig", pos=(x, 0.0, 0.345), yaw=0.0)
    carry_ready = (0.00, -1.38, -0.55, 0.42, 0.04 * math.sin(7.0 * time_s), 0.0)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=carry_ready)
    set_rig_gripper(model, data, name="sender_rig", closed=0.0)
    mujoco.mj_forward(model, data)


def apply_loaded_walk(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    time_s: float,
    duration_s: float,
    style: str,
) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    cfg = BOX_STYLES[style]
    progress = smoothstep(0.0, duration_s, time_s)
    distance = float(cfg["walk_speed_mps"]) * duration_s
    x = -0.28 + distance * progress
    compression = float(cfg["leg_compression_m"])
    set_aegis_pose(
        model,
        data,
        pos=(x, 0.0, 0.345),
        yaw=0.0,
        time_s=time_s,
        moving=True,
        leg_compression=compression,
        gait_speed=max(0.45, float(cfg["walk_speed_mps"]) / 0.50),
    )
    set_rig_pose(model, data, name="sender_rig", pos=(x, 0.0, 0.345), yaw=0.0)
    loaded_pose = (0.00, -1.50, -0.62, 0.50, 0.03 * math.sin(5.0 * time_s), 0.0)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=loaded_pose)
    set_rig_gripper(model, data, name="sender_rig", closed=0.0)
    mujoco.mj_forward(model, data)
    basket_site = site_position(model, data, rig_site_name("sender_rig", "basket_payload_site"))
    sway = 0.010 * math.sin(8.0 * time_s) * (1.0 + 6.0 * compression)
    box_pos = (basket_site[0], basket_site[1] + sway, basket_site[2] - 0.006)
    box_quat = quat_from_yaw_pitch(0.0, 0.06 * math.sin(5.0 * time_s) * (1.0 + compression * 8.0))
    set_freejoint_pose_quat(model, data, "target_box_freejoint", box_pos, box_quat)
    mujoco.mj_forward(model, data)


def curved_lane_pose(start: tuple[float, float], mid: tuple[float, float], end: tuple[float, float], progress: float) -> tuple[float, float]:
    progress = float(np.clip(progress, 0.0, 1.0))
    if progress < 0.5:
        local = progress / 0.5
        return (start[0] * (1.0 - local) + mid[0] * local, start[1] * (1.0 - local) + mid[1] * local)
    local = (progress - 0.5) / 0.5
    return (mid[0] * (1.0 - local) + end[0] * local, mid[1] * (1.0 - local) + end[1] * local)


def fleet_clearance_metrics(model: mujoco.MjModel, data: mujoco.MjData) -> dict[str, float]:
    positions = [
        np.asarray(body_position(model, data, "BASE_LINK")[:2], dtype=float),
        np.asarray(body_position(model, data, "r_BASE_LINK")[:2], dtype=float),
        np.asarray(body_position(model, data, "t_BASE_LINK")[:2], dtype=float),
    ]
    pairwise = [float(np.linalg.norm(a - b)) for idx, a in enumerate(positions) for b in positions[idx + 1:]]
    obstacle = np.asarray([0.0, 0.0], dtype=float)
    obstacle_clearances = [float(np.linalg.norm(pos - obstacle) - 0.36) for pos in positions]
    return {
        "min_robot_spacing_m": round(min(pairwise), 4),
        "min_obstacle_clearance_m": round(min(obstacle_clearances), 4),
    }


def apply_fleet_physics(model: mujoco.MjModel, data: mujoco.MjData, time_s: float, duration_s: float) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    cfg = BOX_STYLES["metal"]
    p = smoothstep(0.0, duration_s, time_s)
    sender_xy = curved_lane_pose((-1.35, 0.32), (-0.05, 0.62), (1.22, 0.30), p)
    receiver_wait = smoothstep(0.84, 1.0, p)
    receiver_xy = curved_lane_pose((1.38, -0.48), (1.28, -0.46), (0.92, -0.42), receiver_wait)
    traffic_release = smoothstep(0.58, 0.96, p)
    traffic_xy = curved_lane_pose((-0.20, -1.05), (0.22, -1.08), (0.78, -1.02), traffic_release)

    set_aegis_pose(model, data, prefix="", pos=(sender_xy[0], sender_xy[1], 0.345), yaw=0.08, time_s=time_s, moving=True, leg_compression=float(cfg["leg_compression_m"]), gait_speed=0.78)
    set_aegis_pose(model, data, prefix="r_", pos=(receiver_xy[0], receiver_xy[1], 0.345), yaw=math.pi - 0.04, time_s=time_s, moving=p > 0.84, leg_compression=0.012, gait_speed=0.65)
    set_aegis_pose(model, data, prefix="t_", pos=(traffic_xy[0], traffic_xy[1], 0.345), yaw=0.02, time_s=time_s, moving=p > 0.58, leg_compression=0.010, gait_speed=0.55)

    carry_pose = (0.02, -1.92, -0.74, 0.36, 0.12 * math.sin(4.2 * time_s), 0.05)
    handoff_pose = (0.08, -0.10, 0.64, -0.06, 0.10, -0.04)
    sender_pose = lerp_tuple(carry_pose, handoff_pose, smoothstep(0.66, 0.86, p))
    receiver_pose = lerp_tuple((-0.08, 0.06, 0.70, -0.12, -0.08, 0.10), (0.08, -2.05, -0.82, 0.10, 0.04, 0.05), smoothstep(0.88, 1.0, p))
    traffic_pose = (0.00, -1.55, -0.60, 0.48, 0.00, 0.00)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=sender_pose)
    set_rig_arm_pose_tuple(model, data, name="receiver_rig", pose=receiver_pose)
    set_rig_arm_pose_tuple(model, data, name="third_rig", pose=traffic_pose)
    set_rig_gripper(model, data, name="sender_rig", closed=1.0 - 0.85 * smoothstep(0.78, 0.90, p))
    set_rig_gripper(model, data, name="receiver_rig", closed=smoothstep(0.70, 0.86, p) * (1.0 - 0.75 * smoothstep(0.94, 1.0, p)))
    set_rig_gripper(model, data, name="third_rig", closed=0.0)
    mujoco.mj_forward(model, data)

    sender_basket_site = site_position(model, data, rig_site_name("sender_rig", "basket_payload_site"))
    sender_grip_site = site_position(model, data, rig_site_name("sender_rig", "gripper_site"))
    receiver_grip_site = site_position(model, data, rig_site_name("receiver_rig", "gripper_site"))
    receiver_basket_site = site_position(model, data, rig_site_name("receiver_rig", "basket_payload_site"))
    sender_basket = (sender_basket_site[0], sender_basket_site[1], sender_basket_site[2] - 0.006)
    sender_grip = (sender_grip_site[0], sender_grip_site[1], sender_grip_site[2] - 0.006)
    receiver_grip = (receiver_grip_site[0], receiver_grip_site[1], receiver_grip_site[2] - 0.006)
    receiver_basket = (receiver_basket_site[0], receiver_basket_site[1], receiver_basket_site[2] - 0.006)
    pickup = smoothstep(0.02, 0.16, p)
    transfer = smoothstep(0.70, 0.86, p)
    release = smoothstep(0.92, 1.0, p)
    if pickup < 1.0:
        box_pos = lerp(sender_grip, sender_basket, pickup)
        box_quat = quat_slerp(body_quat(model, data, rig_body_name("sender_rig", "right_hand")), quat_from_yaw_pitch(0.0, 0.04), pickup)
    elif transfer < 1.0:
        box_pos = lerp(sender_basket, receiver_grip, transfer)
        box_quat = quat_slerp(quat_from_yaw_pitch(0.0, 0.06 * math.sin(4.0 * time_s)), body_quat(model, data, rig_body_name("receiver_rig", "right_hand")), transfer)
    elif release < 1.0:
        box_pos = lerp(receiver_grip, receiver_basket, release)
        box_quat = quat_slerp(body_quat(model, data, rig_body_name("receiver_rig", "right_hand")), quat_from_yaw_pitch(math.pi, 0.0), release)
    else:
        box_pos = receiver_basket
        box_quat = quat_from_yaw_pitch(math.pi, 0.0)
    set_freejoint_pose_quat(model, data, "target_box_freejoint", box_pos, box_quat)
    mujoco.mj_forward(model, data)


def apply_effector_mix_lab(model: mujoco.MjModel, data: mujoco.MjData, time_s: float, duration_s: float) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    p = smoothstep(0.0, duration_s, time_s)
    set_aegis_pose(model, data, prefix="", pos=(-1.25, 0.72, 0.345), yaw=0.04, time_s=time_s, moving=False, leg_compression=0.018, gait_speed=0.45)
    set_aegis_pose(model, data, prefix="r_", pos=(0.00, -0.60, 0.345), yaw=0.08, time_s=time_s, moving=False, leg_compression=0.028, gait_speed=0.45)
    set_aegis_pose(model, data, prefix="t_", pos=(1.25, 0.72, 0.345), yaw=math.pi - 0.05, time_s=time_s, moving=False, leg_compression=0.014, gait_speed=0.45)
    dex_pose = (-0.20, -0.12, 0.78, -0.18, 0.30 * math.sin(2.4 * time_s), -0.16)
    magnet_pose = (0.04, -0.18, 0.62, -0.10, 0.05, 0.04)
    rail_pose = (-0.06, -0.08, 0.74, -0.16, -0.04, -0.10)
    set_rig_arm_pose_tuple(model, data, name="sender_rig", pose=dex_pose)
    set_rig_arm_pose_tuple(model, data, name="receiver_rig", pose=magnet_pose)
    set_rig_arm_pose_tuple(model, data, name="third_rig", pose=rail_pose)
    set_rig_gripper(model, data, name="sender_rig", closed=0.75 + 0.20 * smoothstep(0.10, 0.35, p))
    set_rig_gripper(model, data, name="receiver_rig", closed=0.08)
    set_rig_gripper(model, data, name="third_rig", closed=0.10)
    mujoco.mj_forward(model, data)

    dex_site = site_position(model, data, "rig_dexterous_tool_site")
    magnet_site = site_position(model, data, "r_rig_magnet_tool_site")
    rail_site = site_position(model, data, "t_rig_slide_rail_site")
    vial_pos = (dex_site[0] + 0.008 * math.sin(4.0 * time_s), dex_site[1], dex_site[2] - 0.006)
    puck_pos = (magnet_site[0], magnet_site[1], magnet_site[2] - 0.010 + 0.006 * math.sin(math.pi * p))
    slide = -0.052 + 0.104 * smoothstep(0.20, 0.88, p)
    tote_pos = (rail_site[0] + slide, rail_site[1], rail_site[2] - 0.004)
    set_freejoint_pose_quat(model, data, "fragile_vial_freejoint", vial_pos, quat_from_yaw_pitch(0.12 * math.sin(2.8 * time_s), 0.06))
    set_freejoint_pose_quat(model, data, "metal_puck_freejoint", puck_pos, quat_from_yaw_pitch(0.0, 0.0))
    set_freejoint_pose_quat(model, data, "rail_tote_freejoint", tote_pos, quat_from_yaw_pitch(math.pi, 0.0))
    mujoco.mj_forward(model, data)


def apply_scenario_state(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    scenario: str,
    time_s: float,
    duration_s: float,
) -> None:
    kind = scenario_kind(scenario)
    style = scenario_payload_style(scenario)
    if scenario == "arm_showcase":
        apply_arm_showcase(model, data, time_s, duration_s)
    elif kind == "shelf_pick":
        apply_shelf_pick(model, data, time_s, duration_s, style=style)
    elif kind == "handoff":
        apply_handoff(model, data, time_s, duration_s, style=style)
    elif kind == "rest_idle":
        apply_rest_idle(model, data, time_s, duration_s)
    elif kind == "empty_stance":
        apply_empty_stance(model, data, time_s, duration_s)
    elif kind == "empty_walk":
        apply_empty_walk(model, data, time_s, duration_s)
    elif kind == "loaded_walk":
        apply_loaded_walk(model, data, time_s, duration_s, style=style)
    elif kind == "fleet_physics":
        apply_fleet_physics(model, data, time_s, duration_s)
    elif kind == "effector_mix":
        apply_effector_mix_lab(model, data, time_s, duration_s)
    else:
        raise ValueError(f"Unknown scenario: {scenario}")


def update_camera(
    camera: mujoco.MjvCamera,
    scenario: str,
    time_s: float,
) -> None:
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    kind = scenario_kind(scenario)
    if scenario == "arm_showcase":
        camera.lookat[:] = [0.10, 0.0, 0.35]
        camera.distance = 2.05
        camera.azimuth = 118.0 + 8.0 * math.sin(0.35 * time_s)
        camera.elevation = -18.0
    elif kind == "shelf_pick":
        camera.lookat[:] = [0.03, 0.0, 0.38]
        camera.distance = 1.95
        camera.azimuth = 92.0
        camera.elevation = -17.0
    elif kind in {"rest_idle", "empty_stance", "empty_walk", "loaded_walk"}:
        look_x = 0.10 if kind in {"rest_idle", "empty_stance"} else 0.18
        camera.lookat[:] = [look_x, 0.0, 0.34]
        camera.distance = 1.65
        camera.azimuth = 118.0 + 4.0 * math.sin(0.7 * time_s)
        camera.elevation = -18.0
    elif kind == "effector_mix":
        camera.lookat[:] = [0.06, 0.22, 0.43]
        camera.distance = 3.30
        camera.azimuth = 105.0 + 4.0 * math.sin(0.35 * time_s)
        camera.elevation = -20.0
    elif kind == "fleet_physics":
        camera.lookat[:] = [0.02, 0.0, 0.40]
        camera.distance = 3.10
        camera.azimuth = 100.0 + 5.0 * math.sin(0.35 * time_s)
        camera.elevation = -21.0
    else:
        camera.lookat[:] = [0.0, 0.0, 0.38]
        camera.distance = 2.30
        camera.azimuth = 102.0
        camera.elevation = -16.0


def run_scenario(
    *,
    scenario: str,
    urdf_path: Path,
    output_dir: Path,
    duration_s: float,
    fps: int,
    width: int,
    height: int,
) -> dict:
    model = build_model(urdf_path, scenario)
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, width=width, height=height)
    camera = mujoco.MjvCamera()

    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / f"{scenario}.mp4"
    trajectory_path = output_dir / f"{scenario}_trajectory.json"
    kind = scenario_kind(scenario)
    payload_style = scenario_payload_style(scenario)

    frames: list[np.ndarray] = []
    trajectory: list[dict] = []
    contact_totals = {
        "gripper_box": 0,
        "receiver_gripper_box": 0,
        "box_basket": 0,
        "box_shelf": 0,
        "arm_basket": 0,
        "robot_obstacle": 0,
        "box_obstacle": 0,
        "dexterous_fragile": 0,
        "magnet_metal": 0,
        "rail_tote": 0,
        "total_contacts": 0,
    }
    total_frames = max(1, int(round(duration_s * fps)))
    for frame_idx in range(total_frames):
        time_s = frame_idx / fps
        apply_scenario_state(model, data, scenario, time_s, duration_s)
        contacts = contact_counters(model, data)
        for key, value in contacts.items():
            contact_totals[key] += int(value)
        update_camera(camera, scenario, time_s)
        renderer.update_scene(data, camera=camera)
        frames.append(renderer.render().copy())

        if frame_idx % max(1, fps // 5) == 0:
            sample = {
                "time_s": round(time_s, 3),
                "sender_base": body_position(model, data, "BASE_LINK"),
                "contacts": contacts,
            }
            if kind == "handoff":
                sample["receiver_base"] = body_position(model, data, "r_BASE_LINK")
                sample["box_pos"] = body_position(model, data, "transfer_box")
            elif kind == "fleet_physics":
                sample["receiver_base"] = body_position(model, data, "r_BASE_LINK")
                sample["traffic_base"] = body_position(model, data, "t_BASE_LINK")
                sample["box_pos"] = body_position(model, data, "target_box")
                sample["clearance"] = fleet_clearance_metrics(model, data)
            elif kind == "effector_mix":
                sample["dexterous_robot_base"] = body_position(model, data, "BASE_LINK")
                sample["magnet_robot_base"] = body_position(model, data, "r_BASE_LINK")
                sample["rail_robot_base"] = body_position(model, data, "t_BASE_LINK")
                sample["fragile_vial_pos"] = body_position(model, data, "fragile_vial")
                sample["metal_puck_pos"] = body_position(model, data, "metal_puck")
                sample["rail_tote_pos"] = body_position(model, data, "rail_tote")
            elif kind in {"shelf_pick", "loaded_walk"}:
                sample["box_pos"] = body_position(model, data, "target_box")
            elif scenario == "arm_showcase":
                sample["cardboard_pos"] = body_position(model, data, "cardboard_box")
                sample["wood_pos"] = body_position(model, data, "wood_box")
                sample["metal_pos"] = body_position(model, data, "metal_box")
            trajectory.append(sample)

    try:
        iio.imwrite(video_path, np.asarray(frames), fps=fps, codec="libx264")
    except Exception as exc:
        video_path = video_path.with_suffix(".gif")
        iio.imwrite(video_path, np.asarray(frames), fps=fps)
        fallback_reason = str(exc)
    else:
        fallback_reason = None

    summary = {
        "project": "Warehouse Quadbot Atomic Demos",
        "scenario": scenario,
        "scenario_kind": kind,
        "robot": "AEGIS quadruped with BASE_LINK-mounted basket and Futurist-right-arm-derived manipulator",
        "model": repo_relative(urdf_path),
        "video": repo_relative(video_path),
        "trajectory": repo_relative(trajectory_path),
        "duration_s": duration_s,
        "fps": fps,
        "payload": {
            "style": "heterogeneous",
            "items": ["fragile_vial", "metal_puck", "rail_tote"],
            "end_effectors": ["dexterous_hand", "electromagnet", "slide_rail"],
        }
        if kind == "effector_mix"
        else (None
        if kind in {"rest_idle", "empty_stance", "empty_walk", "arm_showcase"}
        else {
            "style": payload_style,
            "label": BOX_STYLES[payload_style]["label"],
            "mass_kg": BOX_STYLES[payload_style]["mass"],
            "difficulty": BOX_STYLES[payload_style]["difficulty"],
            "loading_time_s": BOX_STYLES[payload_style]["loading_time_s"],
            "grip_close_s": BOX_STYLES[payload_style]["grip_close_s"],
            "walk_speed_mps": BOX_STYLES[payload_style]["walk_speed_mps"],
            "leg_compression_m": BOX_STYLES[payload_style]["leg_compression_m"],
        }),
        "box_styles": BOX_STYLES,
        "tile_size_m": TILE_SIZE,
        "mujoco_depth": {
            "quadruped_leg_joints": 36 if kind in {"fleet_physics", "effector_mix"} else (12 if kind != "handoff" else 24),
            "arm_dof_per_robot": 7,
            "gripper_slide_joints_per_robot": 2,
            "collision_geoms": [
                "package box",
                "left/right gripper fingers and pads",
                "cargo basket floor and rails",
                "pickup shelf decks",
                "fleet corridor obstacle pillar",
                "fragile vial cylinder",
                "electromagnet contact plate",
                "low-friction slide rail carriage",
            ],
            "sensors": [
                "leg joint position",
                "Futurist right-arm joint position",
                "gripper frame position",
                "basket frame position",
                "left/right finger touch",
                "basket touch",
                "heterogeneous end-effector contact counters",
            ],
            "actuators": "position actuators on AEGIS leg joints, seven Futurist-derived arm joints, and two finger slide joints",
        },
        "contact_totals": contact_totals,
        "fleet_physics_metrics": fleet_clearance_metrics(model, data) if kind == "fleet_physics" else None,
        "end_effector_mix": {
            "dexterous_hand": "fragile cylindrical vial / high-friction multi-pad contact",
            "electromagnet": "ferrous metal puck / magnetic plate contact surrogate",
            "slide_rail": "low-friction rail tote / guided slide contact",
        } if kind == "effector_mix" else None,
        "physics_note": (
            "Package, shelf, basket, and gripper use MuJoCo collision geoms. "
            "During grasp and carry phases the package follows the wrist pose with "
            "matching orientation, then releases into the basket. This is still a "
            "scripted atomic-skill demo, not a full closed-loop grasp controller."
        ),
        "success": True,
        "trajectory_samples": trajectory,
    }
    if fallback_reason:
        summary["video_fallback_reason"] = fallback_reason
    trajectory_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {k: v for k, v in summary.items() if k != "trajectory_samples"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render warehouse quadbot atomic operation demos.")
    parser.add_argument("--urdf", type=Path, default=DEFAULT_URDF)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--scenario",
        choices=ALL_SCENARIOS + ("all",),
        default="all",
    )
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenarios = list(ALL_SCENARIOS) if args.scenario == "all" else [args.scenario]
    results = [
        run_scenario(
            scenario=scenario,
            urdf_path=args.urdf,
            output_dir=args.output_dir,
            duration_s=args.duration if args.duration is not None else SCENARIO_DURATIONS[scenario],
            fps=args.fps,
            width=args.width,
            height=args.height,
        )
        for scenario in scenarios
    ]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

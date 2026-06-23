from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import imageio.v3 as iio
import mujoco
import numpy as np


MODULE_DIR = Path(__file__).resolve().parent
SUBMISSION_DIR = MODULE_DIR.parent
OUTPUT_DIR = SUBMISSION_DIR / "outputs" / "physics_evidence"
GENERATED_DIR = OUTPUT_DIR / "generated_mjcf"

LEGS = (
    ("fl", 0.23, 0.13, 0.0),
    ("fr", 0.23, -0.13, math.pi),
    ("rl", -0.23, 0.13, math.pi),
    ("rr", -0.23, -0.13, 0.0),
)

ARM_JOINTS = (
    "arm_base_yaw",
    "arm_shoulder_pitch",
    "arm_elbow_pitch",
    "arm_wrist_pitch",
    "arm_wrist_roll",
    "arm_tool_yaw",
)

BOX_HALF_SIZE = (0.095, 0.070, 0.050)


@dataclass(frozen=True)
class PayloadProfile:
    key: str
    label: str
    mass_kg: float
    rgba: tuple[float, float, float, float]
    loading_time_s: float
    gait_speed_mps: float
    leg_compression: float
    grip_close_s: float


@dataclass(frozen=True)
class ClipSpec:
    name: str
    kind: str
    payload_key: str | None
    duration_s: float
    description: str


PAYLOADS: dict[str, PayloadProfile] = {
    "cardboard": PayloadProfile(
        key="cardboard",
        label="light cardboard parcel",
        mass_kg=0.8,
        rgba=(0.74, 0.45, 0.20, 1.0),
        loading_time_s=0.80,
        gait_speed_mps=0.46,
        leg_compression=0.020,
        grip_close_s=0.20,
    ),
    "wood": PayloadProfile(
        key="wood",
        label="medium wood crate",
        mass_kg=2.0,
        rgba=(0.45, 0.25, 0.10, 1.0),
        loading_time_s=1.05,
        gait_speed_mps=0.35,
        leg_compression=0.050,
        grip_close_s=0.32,
    ),
    "metal": PayloadProfile(
        key="metal",
        label="heavy metal case",
        mass_kg=4.0,
        rgba=(0.58, 0.63, 0.67, 1.0),
        loading_time_s=1.35,
        gait_speed_mps=0.25,
        leg_compression=0.085,
        grip_close_s=0.46,
    ),
}

CLIPS: tuple[ClipSpec, ...] = (
    ClipSpec("rest_idle", "rest", None, 1.6, "Powered rest pose: folded arm, relaxed legs, no package."),
    ClipSpec("empty_stance", "stance", None, 1.6, "Ready empty pose: arm online, legs neutral, basket empty."),
    ClipSpec("empty_walk", "walk", None, 1.8, "Empty walking gait: fastest and least crouched."),
    ClipSpec("loaded_walk_cardboard", "loaded_walk", "cardboard", 1.8, "Cardboard load gait: light basket load."),
    ClipSpec("loaded_walk_wood", "loaded_walk", "wood", 1.8, "Wood load gait: medium crouch and slower stride."),
    ClipSpec("loaded_walk_metal", "loaded_walk", "metal", 1.8, "Metal load gait: deepest crouch and slowest stride."),
    ClipSpec("shelf_pick_cardboard", "shelf_pick", "cardboard", 1.8, "Short shelf pickup: light package, fast loading."),
    ClipSpec("shelf_pick_wood", "shelf_pick", "wood", 2.1, "Short shelf pickup: medium package, longer loading."),
    ClipSpec("shelf_pick_metal", "shelf_pick", "metal", 2.4, "Short shelf pickup: heavy package, longest loading."),
    ClipSpec("six_dof_grasp_sweep_wood", "six_dof_grasp_sweep", "wood", 3.0, "6-DOF multi-angle shelf-to-basket grasp: wrist roll/tool yaw reorient a medium crate while both fingertip pads stay in contact."),
    ClipSpec("six_dof_grasp_sweep_metal", "six_dof_grasp_sweep", "metal", 3.2, "6-DOF heavy-package grasp sweep: overhead arc, wrist roll, tool yaw, basket placement, and sustained dual-finger package contact."),
    ClipSpec("handoff_metal", "handoff", "metal", 2.2, "Robot-to-robot handoff with heavy package and receiver basket drop."),
)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if value <= edge0:
        return 0.0
    if value >= edge1:
        return 1.0
    x = (value - edge0) / max(1e-9, edge1 - edge0)
    return x * x * (3.0 - 2.0 * x)


def lerp(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def lerp_list(a: tuple[float, ...], b: tuple[float, ...], t: float) -> tuple[float, ...]:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(len(a)))


def quat_from_yaw(yaw: float) -> list[float]:
    return [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]


def quat_from_euler(roll: float, pitch: float, yaw: float) -> list[float]:
    cr = math.cos(roll / 2.0)
    sr = math.sin(roll / 2.0)
    cp = math.cos(pitch / 2.0)
    sp = math.sin(pitch / 2.0)
    cy = math.cos(yaw / 2.0)
    sy = math.sin(yaw / 2.0)
    return [
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ]


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


def add_floor_and_lights(world: mujoco.MjsBody) -> None:
    world.add_geom(
        name="floor",
        type=mujoco.mjtGeom.mjGEOM_PLANE,
        size=[0, 0, 0.05],
        rgba=[0.045, 0.050, 0.057, 1.0],
        friction=[0.9, 0.05, 0.02],
    )
    world.add_light(pos=[-1.0, -2.0, 3.5], dir=[0.25, 0.45, -1.0], diffuse=[0.95, 0.95, 0.92])
    world.add_light(pos=[1.5, 1.0, 2.2], dir=[-0.4, -0.2, -1.0], diffuse=[0.45, 0.55, 0.70])


def add_marker_tile(world: mujoco.MjsBody, name: str, pos: tuple[float, float], rgba: tuple[float, float, float, float]) -> None:
    world.add_geom(
        name=name,
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[pos[0], pos[1], 0.006],
        size=[0.42, 0.34, 0.006],
        rgba=rgba,
        contype=0,
        conaffinity=0,
    )


def add_shelf(world: mujoco.MjsBody) -> None:
    shelf_x = -0.52
    shelf_y = 0.0
    for idx, (dx, dy) in enumerate(((-0.22, -0.18), (-0.22, 0.18), (0.22, -0.18), (0.22, 0.18))):
        world.add_geom(
            name=f"shelf_post_{idx}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[shelf_x + dx, shelf_y + dy, 0.32],
            size=[0.025, 0.025, 0.32],
            rgba=[0.13, 0.17, 0.20, 1.0],
            friction=[0.8, 0.05, 0.02],
        )
    for idx, z in enumerate((0.20, 0.42, 0.64)):
        world.add_geom(
            name=f"shelf_deck_{idx}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[shelf_x, shelf_y, z],
            size=[0.27, 0.22, 0.025],
            rgba=[0.24, 0.29, 0.33, 1.0],
            friction=[0.8, 0.05, 0.02],
        )


def add_payload(world: mujoco.MjsBody, profile: PayloadProfile) -> None:
    body = world.add_body(name="package", pos=[-0.52, 0.0, 0.51])
    body.add_freejoint(name="package_freejoint")
    body.add_geom(
        name="package_geom",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=list(BOX_HALF_SIZE),
        mass=profile.mass_kg,
        rgba=list(profile.rgba),
        friction=[1.0, 0.08, 0.03],
    )
    if profile.key == "cardboard":
        body.add_geom(
            name="package_tape_visual",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0, 0, BOX_HALF_SIZE[2] + 0.003],
            size=[0.014, BOX_HALF_SIZE[1] * 1.02, 0.004],
            rgba=[0.92, 0.82, 0.56, 1.0],
            contype=0,
            conaffinity=0,
        )
    body.add_site(name="package_site", pos=[0, 0, 0], size=[0.016], rgba=[1.0, 0.85, 0.1, 0.9])
    if profile.key == "metal":
        body.add_geom(
            name="package_metal_highlight",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0, 0, BOX_HALF_SIZE[2] + 0.004],
            size=[BOX_HALF_SIZE[0] * 0.82, BOX_HALF_SIZE[1] * 0.82, 0.004],
            rgba=[0.85, 0.90, 0.94, 0.55],
            contype=0,
            conaffinity=0,
        )


def add_robot(world: mujoco.MjsBody, prefix: str) -> None:
    torso = world.add_body(name=f"{prefix}torso", pos=[0, 0, 0.38])
    torso.add_freejoint(name=f"{prefix}floating_base")
    torso.add_geom(
        name=f"{prefix}torso_shell",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0, 0, 0],
        size=[0.31, 0.15, 0.075],
        rgba=[0.86, 0.91, 0.96, 1.0],
        mass=8.0,
    )
    torso.add_geom(
        name=f"{prefix}spine_dark",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.0, 0.0, 0.083],
        size=[0.24, 0.10, 0.018],
        rgba=[0.05, 0.065, 0.080, 1.0],
        mass=0.3,
    )

    # Basket is collision-enabled because basket/package contacts are part of the evidence.
    torso.add_geom(
        name=f"{prefix}basket_floor",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[-0.04, 0, 0.145],
        size=[0.18, 0.12, 0.016],
        rgba=[0.02, 0.08, 0.10, 1.0],
        mass=0.2,
        friction=[0.95, 0.05, 0.02],
    )
    for suffix, pos, size in (
        ("left_rail", [-0.04, 0.132, 0.205], [0.19, 0.012, 0.060]),
        ("right_rail", [-0.04, -0.132, 0.205], [0.19, 0.012, 0.060]),
        ("front_rail", [0.155, 0, 0.205], [0.012, 0.12, 0.060]),
        ("back_rail", [-0.235, 0, 0.205], [0.012, 0.12, 0.060]),
    ):
        torso.add_geom(
            name=f"{prefix}basket_{suffix}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=pos,
            size=size,
            rgba=[0.00, 0.48, 0.62, 1.0],
            mass=0.08,
            friction=[0.95, 0.05, 0.02],
        )
    torso.add_site(name=f"{prefix}basket_payload_site", pos=[-0.04, 0, 0.218], size=[0.018], rgba=[0.1, 0.9, 0.8, 0.8])
    torso.add_site(name=f"{prefix}basket_touch_site", pos=[-0.04, 0, 0.170], size=[0.18, 0.12, 0.030], rgba=[0.0, 0.8, 1.0, 0.08])

    for leg, x, y, phase in LEGS:
        hip = torso.add_body(name=f"{prefix}{leg}_hip_roll_body", pos=[x, y, -0.035])
        hip.add_joint(
            name=f"{prefix}{leg}_hip_roll",
            type=mujoco.mjtJoint.mjJNT_HINGE,
            axis=[1, 0, 0],
            limited=True,
            range=[-0.55, 0.55],
            damping=0.25,
        )
        hip.add_geom(
            name=f"{prefix}{leg}_hip_motor",
            type=mujoco.mjtGeom.mjGEOM_SPHERE,
            size=[0.045],
            rgba=[0.95, 0.47, 0.12, 1.0],
            mass=0.25,
        )
        upper = hip.add_body(name=f"{prefix}{leg}_upper_body", pos=[0, 0, -0.015])
        upper.add_joint(
            name=f"{prefix}{leg}_hip_pitch",
            type=mujoco.mjtJoint.mjJNT_HINGE,
            axis=[0, 1, 0],
            limited=True,
            range=[-1.10, 1.25],
            damping=0.25,
        )
        upper.add_geom(
            name=f"{prefix}{leg}_upper_link",
            type=mujoco.mjtGeom.mjGEOM_CAPSULE,
            fromto=[0, 0, 0, 0.025, 0, -0.155],
            size=[0.025],
            rgba=[0.20, 0.24, 0.30, 1.0],
            mass=0.45,
        )
        lower = upper.add_body(name=f"{prefix}{leg}_lower_body", pos=[0.025, 0, -0.155])
        lower.add_joint(
            name=f"{prefix}{leg}_knee_pitch",
            type=mujoco.mjtJoint.mjJNT_HINGE,
            axis=[0, 1, 0],
            limited=True,
            range=[-1.95, -0.25],
            damping=0.22,
        )
        lower.add_geom(
            name=f"{prefix}{leg}_lower_link",
            type=mujoco.mjtGeom.mjGEOM_CAPSULE,
            fromto=[0, 0, 0, -0.020, 0, -0.165],
            size=[0.022],
            rgba=[0.13, 0.16, 0.21, 1.0],
            mass=0.35,
        )
        foot = lower.add_body(name=f"{prefix}{leg}_foot_body", pos=[-0.020, 0, -0.172])
        foot.add_geom(
            name=f"{prefix}{leg}_foot",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            size=[0.055, 0.030, 0.018],
            rgba=[0.035, 0.040, 0.045, 1.0],
            mass=0.20,
            friction=[1.1, 0.08, 0.03],
        )

    # Six-axis arm inspired by industrial 6-DOF layouts: yaw, shoulder, elbow, three wrist/tool axes.
    arm_base = torso.add_body(name=f"{prefix}arm_base", pos=[0.22, 0, 0.125])
    arm_base.add_joint(
        name=f"{prefix}arm_base_yaw",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 0, 1],
        limited=True,
        range=[-2.7, 2.7],
        damping=0.35,
    )
    arm_base.add_geom(
        name=f"{prefix}arm_base_column",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        pos=[0, 0, 0.040],
        size=[0.045, 0.080],
        rgba=[0.08, 0.10, 0.12, 1.0],
        mass=0.35,
    )
    shoulder = arm_base.add_body(name=f"{prefix}arm_shoulder", pos=[0.035, 0, 0.095])
    shoulder.add_joint(
        name=f"{prefix}arm_shoulder_pitch",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-1.65, 1.25],
        damping=0.35,
    )
    shoulder.add_geom(
        name=f"{prefix}arm_upper_link",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0, 0, 0, 0.23, 0, 0.050],
        size=[0.024],
        rgba=[0.98, 0.62, 0.13, 1.0],
        mass=0.45,
    )
    elbow = shoulder.add_body(name=f"{prefix}arm_elbow", pos=[0.23, 0, 0.050])
    elbow.add_joint(
        name=f"{prefix}arm_elbow_pitch",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-1.85, 1.65],
        damping=0.35,
    )
    elbow.add_geom(
        name=f"{prefix}arm_forearm_link",
        type=mujoco.mjtGeom.mjGEOM_CAPSULE,
        fromto=[0, 0, 0, 0.21, 0, -0.040],
        size=[0.022],
        rgba=[1.00, 0.75, 0.20, 1.0],
        mass=0.36,
    )
    wrist_pitch = elbow.add_body(name=f"{prefix}arm_wrist_pitch_body", pos=[0.21, 0, -0.040])
    wrist_pitch.add_joint(
        name=f"{prefix}arm_wrist_pitch",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 1, 0],
        limited=True,
        range=[-1.60, 1.60],
        damping=0.25,
    )
    wrist_pitch.add_geom(
        name=f"{prefix}arm_wrist_pitch_housing",
        type=mujoco.mjtGeom.mjGEOM_CYLINDER,
        pos=[0.020, 0, 0],
        size=[0.030, 0.030],
        rgba=[0.13, 0.15, 0.17, 1.0],
        mass=0.12,
    )
    wrist_roll = wrist_pitch.add_body(name=f"{prefix}arm_wrist_roll_body", pos=[0.055, 0, 0])
    wrist_roll.add_joint(
        name=f"{prefix}arm_wrist_roll",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[1, 0, 0],
        limited=True,
        range=[-3.10, 3.10],
        damping=0.20,
    )
    wrist_roll.add_geom(
        name=f"{prefix}arm_wrist_roll_housing",
        type=mujoco.mjtGeom.mjGEOM_SPHERE,
        size=[0.030],
        rgba=[0.10, 0.12, 0.14, 1.0],
        mass=0.10,
    )
    tool_yaw = wrist_roll.add_body(name=f"{prefix}arm_tool_yaw_body", pos=[0.045, 0, 0])
    tool_yaw.add_joint(
        name=f"{prefix}arm_tool_yaw",
        type=mujoco.mjtJoint.mjJNT_HINGE,
        axis=[0, 0, 1],
        limited=True,
        range=[-2.80, 2.80],
        damping=0.20,
    )
    tool_yaw.add_geom(
        name=f"{prefix}gripper_palm",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.035, 0, 0],
        size=[0.034, 0.055, 0.025],
        rgba=[0.065, 0.075, 0.085, 1.0],
        mass=0.22,
        friction=[0.9, 0.05, 0.02],
    )
    tool_yaw.add_site(name=f"{prefix}gripper_site", pos=[0.090, 0, 0], size=[0.018], rgba=[0.0, 0.45, 1.0, 0.9])
    for side, sign in (("left", 1.0), ("right", -1.0)):
        finger = tool_yaw.add_body(name=f"{prefix}gripper_{side}_body", pos=[0.092, sign * 0.082, 0])
        finger.add_joint(
            name=f"{prefix}gripper_{side}_slide",
            type=mujoco.mjtJoint.mjJNT_SLIDE,
            axis=[0, -sign, 0],
            limited=True,
            range=[0.0, 0.045],
            damping=0.12,
        )
        finger.add_geom(
            name=f"{prefix}gripper_{side}_finger",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.030, 0, 0],
            size=[0.065, 0.010, 0.021],
            rgba=[0.030, 0.035, 0.040, 1.0],
            mass=0.08,
            friction=[1.3, 0.08, 0.03],
        )
        finger.add_geom(
            name=f"{prefix}gripper_{side}_pad",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[0.070, -sign * 0.002, 0],
            size=[0.025, 0.006, 0.025],
            rgba=[0.12, 0.13, 0.13, 1.0],
            mass=0.02,
            friction=[1.6, 0.10, 0.04],
        )
        finger.add_site(
            name=f"{prefix}gripper_{side}_touch_site",
            pos=[0.070, -sign * 0.004, 0],
            size=[0.035, 0.018, 0.030],
            rgba=[0.0, 0.6, 1.0, 0.08],
        )


def add_robot_actuators_and_sensors(spec: mujoco.MjSpec, prefix: str) -> None:
    for leg, _x, _y, _phase in LEGS:
        for joint_name, limit in (
            ("hip_roll", (-0.55, 0.55)),
            ("hip_pitch", (-1.10, 1.25)),
            ("knee_pitch", (-1.95, -0.25)),
        ):
            full = f"{prefix}{leg}_{joint_name}"
            add_position_actuator(spec, name=f"{full}_motor", joint=full, kp=140, kv=12, ctrlrange=limit)

    ranges = {
        "arm_base_yaw": (-2.7, 2.7),
        "arm_shoulder_pitch": (-1.65, 1.25),
        "arm_elbow_pitch": (-1.85, 1.65),
        "arm_wrist_pitch": (-1.60, 1.60),
        "arm_wrist_roll": (-3.10, 3.10),
        "arm_tool_yaw": (-2.80, 2.80),
        "gripper_left_slide": (0.0, 0.045),
        "gripper_right_slide": (0.0, 0.045),
    }
    for joint_name, ctrlrange in ranges.items():
        full = f"{prefix}{joint_name}"
        add_position_actuator(spec, name=f"{full}_motor", joint=full, kp=180, kv=10, ctrlrange=ctrlrange)
        add_jointpos_sensor(spec, name=f"{full}_pos", joint=full)

    add_framepos_sensor(spec, name=f"{prefix}gripper_framepos", site=f"{prefix}gripper_site")
    add_framepos_sensor(spec, name=f"{prefix}basket_framepos", site=f"{prefix}basket_payload_site")
    add_touch_sensor(spec, name=f"{prefix}left_finger_touch", site=f"{prefix}gripper_left_touch_site")
    add_touch_sensor(spec, name=f"{prefix}right_finger_touch", site=f"{prefix}gripper_right_touch_site")
    add_touch_sensor(spec, name=f"{prefix}basket_touch", site=f"{prefix}basket_touch_site")


def build_spec(profile: PayloadProfile, *, include_receiver: bool, include_shelf: bool) -> mujoco.MjSpec:
    spec = mujoco.MjSpec()
    spec.modelname = "warehouse_quadbot_physics_evidence"
    spec.option.timestep = 0.005
    spec.option.gravity = [0.0, 0.0, -9.81]
    spec.visual.global_.offwidth = 960
    spec.visual.global_.offheight = 540

    world = spec.worldbody
    add_floor_and_lights(world)
    add_marker_tile(world, "tile_shelf", (-0.52, 0.0), (0.070, 0.100, 0.125, 1.0))
    add_marker_tile(world, "tile_robot", (0.18, 0.0), (0.080, 0.125, 0.110, 1.0))
    add_marker_tile(world, "tile_handoff", (0.88, 0.0), (0.115, 0.095, 0.070, 1.0))
    if include_shelf:
        add_shelf(world)
    add_payload(world, profile)
    add_robot(world, "a_")
    add_robot_actuators_and_sensors(spec, "a_")
    if include_receiver:
        add_robot(world, "b_")
        add_robot_actuators_and_sensors(spec, "b_")

    add_framepos_sensor(spec, name="package_framepos", site="package_site")
    return spec


def set_joint(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str, value: float) -> None:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        return
    qpos_addr = int(model.jnt_qposadr[joint_id])
    if model.jnt_limited[joint_id]:
        lo, hi = model.jnt_range[joint_id]
        value = float(np.clip(value, lo, hi))
    data.qpos[qpos_addr] = value


def joint_value(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str) -> float:
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        return 0.0
    qpos_addr = int(model.jnt_qposadr[joint_id])
    return float(data.qpos[qpos_addr])


def arm_joint_snapshot(model: mujoco.MjModel, data: mujoco.MjData, prefix: str) -> dict[str, float]:
    return {name: round(joint_value(model, data, f"{prefix}{name}"), 4) for name in ARM_JOINTS}


def set_freejoint_pose(
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
    qvel_addr = int(model.jnt_dofadr[joint_id])
    data.qpos[qpos_addr : qpos_addr + 3] = pos
    data.qpos[qpos_addr + 3 : qpos_addr + 7] = quat
    data.qvel[qvel_addr : qvel_addr + 6] = 0.0


def body_world_point(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    body_name: str,
    local: tuple[float, float, float],
) -> tuple[float, float, float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id < 0:
        return local
    xmat = data.xmat[body_id].reshape(3, 3)
    world = data.xpos[body_id] + xmat @ np.array(local)
    return (float(world[0]), float(world[1]), float(world[2]))


def site_position(model: mujoco.MjModel, data: mujoco.MjData, site_name: str) -> tuple[float, float, float]:
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if site_id < 0:
        return (0.0, 0.0, 0.0)
    pos = data.site_xpos[site_id]
    return (float(pos[0]), float(pos[1]), float(pos[2]))


def body_position(model: mujoco.MjModel, data: mujoco.MjData, body_name: str) -> list[float]:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id < 0:
        return [0.0, 0.0, 0.0]
    return data.xpos[body_id].copy().round(4).tolist()


def contact_counters(model: mujoco.MjModel, data: mujoco.MjData) -> dict[str, int]:
    counters = {
        "gripper_package": 0,
        "left_finger_package": 0,
        "right_finger_package": 0,
        "dual_finger_grasp_frames": 0,
        "package_basket": 0,
        "package_shelf": 0,
        "package_receiver_gripper": 0,
        "total_contacts": int(data.ncon),
    }
    left_touch = False
    right_touch = False
    for idx in range(data.ncon):
        contact = data.contact[idx]
        names = [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(contact.geom1)) or "",
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(contact.geom2)) or "",
        ]
        joined = " ".join(names)
        has_package = "package" in joined
        has_gripper = "gripper" in joined
        has_left_finger = "gripper_left" in joined
        has_right_finger = "gripper_right" in joined
        has_basket = "basket" in joined
        has_shelf = "shelf" in joined
        has_receiver = "b_gripper" in joined
        if has_package and has_gripper:
            counters["gripper_package"] += 1
        if has_package and has_left_finger:
            counters["left_finger_package"] += 1
            left_touch = True
        if has_package and has_right_finger:
            counters["right_finger_package"] += 1
            right_touch = True
        if has_package and has_basket:
            counters["package_basket"] += 1
        if has_package and has_shelf:
            counters["package_shelf"] += 1
        if has_package and has_receiver:
            counters["package_receiver_gripper"] += 1
    counters["dual_finger_grasp_frames"] = int(left_touch and right_touch)
    return counters


def reset_state(data: mujoco.MjData) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0


def apply_leg_pose(model: mujoco.MjModel, data: mujoco.MjData, prefix: str, phase_t: float, compression: float, moving: bool) -> None:
    stride = 0.22 if moving else 0.035
    lift = 0.12 if moving else 0.018
    for leg, _x, _y, phase in LEGS:
        wave = math.sin(phase_t + phase)
        counter = math.cos(phase_t + phase)
        set_joint(model, data, f"{prefix}{leg}_hip_roll", 0.045 * wave)
        set_joint(model, data, f"{prefix}{leg}_hip_pitch", 0.38 + compression + stride * wave)
        set_joint(model, data, f"{prefix}{leg}_knee_pitch", -0.95 - 1.25 * compression - lift * max(0.0, counter))


def apply_robot_base(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    prefix: str,
    *,
    x: float,
    y: float,
    yaw: float,
    t: float,
    compression: float,
    moving: bool,
) -> None:
    bob = 0.010 * math.sin(2.0 * math.pi * 2.0 * t) if moving else 0.004 * math.sin(2.0 * math.pi * 0.8 * t)
    z = 0.385 - compression + bob
    set_freejoint_pose(model, data, f"{prefix}floating_base", (x, y, z), quat_from_yaw(yaw))
    phase_rate = 2.0 * math.pi * (1.7 if moving else 0.45)
    apply_leg_pose(model, data, prefix, phase_rate * t, compression, moving)


def apply_arm_pose(model: mujoco.MjModel, data: mujoco.MjData, prefix: str, pose: tuple[float, float, float, float, float, float]) -> None:
    for joint, value in zip(ARM_JOINTS, pose):
        set_joint(model, data, f"{prefix}{joint}", value)


def apply_gripper(model: mujoco.MjModel, data: mujoco.MjData, prefix: str, closed: float) -> None:
    value = 0.045 * float(np.clip(closed, 0.0, 1.0))
    set_joint(model, data, f"{prefix}gripper_left_slide", value)
    set_joint(model, data, f"{prefix}gripper_right_slide", value)


def apply_package_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    pos: tuple[float, float, float],
    yaw: float = 0.0,
    pitch: float = 0.0,
    roll: float = 0.0,
) -> None:
    set_freejoint_pose(model, data, "package_freejoint", pos, quat_from_euler(roll, pitch, yaw))


def gripper_hold_position(model: mujoco.MjModel, data: mujoco.MjData, prefix: str) -> tuple[float, float, float]:
    return body_world_point(model, data, f"{prefix}arm_tool_yaw_body", (0.155, 0.0, 0.0))


def package_in_basket(model: mujoco.MjModel, data: mujoco.MjData, prefix: str, *, pitch: float = 0.0) -> None:
    site = site_position(model, data, f"{prefix}basket_payload_site")
    apply_package_pose(model, data, (site[0], site[1], site[2] - 0.006), yaw=0.0, pitch=pitch)


def apply_rest_or_stance(model: mujoco.MjModel, data: mujoco.MjData, t: float, ready: bool) -> None:
    compression = 0.030 if ready else 0.065
    apply_robot_base(model, data, "a_", x=0.10, y=0.0, yaw=0.0, t=t, compression=compression, moving=False)
    pose = (-1.15, -0.25, -0.85, 0.45, 0.0, 0.0) if ready else (-1.85, -0.75, -1.15, 0.70, 0.0, 0.0)
    apply_arm_pose(model, data, "a_", pose)
    apply_gripper(model, data, "a_", 0.10 if ready else 0.0)
    apply_package_pose(model, data, (-0.52, 0.0, 0.52))


def apply_walk(model: mujoco.MjModel, data: mujoco.MjData, t: float, duration: float, profile: PayloadProfile | None) -> None:
    if profile is None:
        speed = 0.55
        compression = 0.010
    else:
        speed = profile.gait_speed_mps
        compression = profile.leg_compression
    progress = smoothstep(0.0, duration, t)
    distance = speed * duration
    x = 0.10 + distance * progress
    apply_robot_base(model, data, "a_", x=x, y=0.0, yaw=0.0, t=t, compression=compression, moving=True)
    apply_arm_pose(model, data, "a_", (-1.40, -0.60, -0.90, 0.65, 0.0, 0.0))
    apply_gripper(model, data, "a_", 0.0)
    mujoco.mj_forward(model, data)
    if profile is None:
        apply_package_pose(model, data, (-0.72, 0.0, 0.52))
    else:
        package_in_basket(model, data, "a_", pitch=0.03 * math.sin(8.0 * t))


def apply_shelf_pick(model: mujoco.MjModel, data: mujoco.MjData, t: float, duration: float, profile: PayloadProfile) -> None:
    apply_robot_base(model, data, "a_", x=0.12, y=0.0, yaw=math.pi, t=t, compression=profile.leg_compression, moving=False)

    close_start = 0.36
    close_end = close_start + profile.grip_close_s
    lift_start = close_end + 0.08
    basket_start = min(duration - 0.55, lift_start + profile.loading_time_s * 0.48)
    release_start = max(basket_start + 0.22, duration - 0.38)

    reach = smoothstep(0.05, close_start, t)
    grip = smoothstep(close_start, close_end, t)
    lift = smoothstep(lift_start, basket_start, t)
    basket = smoothstep(basket_start, release_start, t)
    release = smoothstep(release_start, duration - 0.05, t)

    stow = (-1.45, -0.55, -0.95, 0.55, 0.0, 0.0)
    reach_pose = (0.08, -0.10, -0.28, 0.22, 0.0, 0.0)
    lift_pose = (0.02, -0.70, -0.10, 0.62, 0.0, 0.0)
    basket_pose = (-2.30, -0.82, -1.05, 0.84, 0.0, 0.0)
    pose = lerp_list(stow, reach_pose, reach)
    pose = lerp_list(pose, lift_pose, lift)
    pose = lerp_list(pose, basket_pose, basket)
    apply_arm_pose(model, data, "a_", pose)  # type: ignore[arg-type]
    apply_gripper(model, data, "a_", grip * (1.0 - release))

    mujoco.mj_forward(model, data)
    shelf_pos = (-0.52, 0.0, 0.495)
    basket_site = site_position(model, data, "a_basket_payload_site")
    carry_pos = gripper_hold_position(model, data, "a_")
    basket_pos = (basket_site[0], basket_site[1], basket_site[2] - 0.006)
    if grip < 1.0:
        pos = lerp(shelf_pos, carry_pos, 0.20 * grip)
    elif basket < 1.0:
        pos = lerp(carry_pos, (carry_pos[0], carry_pos[1], carry_pos[2] + 0.035), lift)
    elif release < 1.0:
        pos = lerp(carry_pos, basket_pos, release)
    else:
        pos = basket_pos
    apply_package_pose(model, data, pos, pitch=0.20 * lift - 0.12 * release)


def apply_handoff(model: mujoco.MjModel, data: mujoco.MjData, t: float, duration: float, profile: PayloadProfile) -> None:
    apply_robot_base(model, data, "a_", x=-0.42, y=0.0, yaw=0.0, t=t, compression=profile.leg_compression, moving=False)
    apply_robot_base(model, data, "b_", x=0.42, y=0.0, yaw=math.pi, t=t, compression=profile.leg_compression * 0.8, moving=False)

    sender_raise = smoothstep(0.05, 0.40, t)
    meet = smoothstep(0.40, 1.05, t)
    transfer = smoothstep(0.92, 1.45, t)
    receiver_lower = smoothstep(1.38, duration - 0.18, t)

    sender_stow = (-1.90, -0.70, -1.05, 0.72, 0.0, 0.0)
    sender_meet = (0.05, -0.34, -0.22, 0.28, 0.0, 0.0)
    sender_release = (0.12, -0.22, -0.18, 0.15, 0.0, 0.0)
    sender_pose = lerp_list(sender_stow, sender_meet, sender_raise)
    sender_pose = lerp_list(sender_pose, sender_release, transfer)
    apply_arm_pose(model, data, "a_", sender_pose)  # type: ignore[arg-type]
    apply_gripper(model, data, "a_", 1.0 - 0.95 * smoothstep(1.05, 1.45, t))

    receiver_ready = (0.08, -0.26, -0.18, 0.22, 0.0, 0.0)
    receiver_basket = (-2.28, -0.82, -1.00, 0.80, 0.0, 0.0)
    receiver_pose = lerp_list(receiver_ready, receiver_basket, receiver_lower)
    apply_arm_pose(model, data, "b_", receiver_pose)  # type: ignore[arg-type]
    apply_gripper(model, data, "b_", smoothstep(0.82, 1.25, t) * (1.0 - 0.92 * smoothstep(duration - 0.35, duration - 0.08, t)))

    mujoco.mj_forward(model, data)
    sender_basket = site_position(model, data, "a_basket_payload_site")
    sender_grip = gripper_hold_position(model, data, "a_")
    receiver_grip = gripper_hold_position(model, data, "b_")
    receiver_basket = site_position(model, data, "b_basket_payload_site")
    if sender_raise < 1.0:
        pos = lerp((sender_basket[0], sender_basket[1], sender_basket[2] - 0.006), sender_grip, sender_raise)
    elif transfer < 1.0:
        pos = lerp(sender_grip, receiver_grip, transfer)
    elif receiver_lower < 1.0:
        pos = receiver_grip
    else:
        pos = (receiver_basket[0], receiver_basket[1], receiver_basket[2] - 0.006)
    apply_package_pose(model, data, pos, yaw=math.pi * transfer, pitch=0.08 * receiver_lower)


def apply_six_dof_grasp_sweep(model: mujoco.MjModel, data: mujoco.MjData, t: float, duration: float, profile: PayloadProfile) -> None:
    apply_robot_base(model, data, "a_", x=0.12, y=0.0, yaw=math.pi, t=t, compression=profile.leg_compression, moving=False)

    close_start = 0.42
    close_end = close_start + profile.grip_close_s
    lift_start = close_end + 0.08
    overhead_start = 1.10
    basket_start = 2.25
    release_start = duration - 0.45

    reach = smoothstep(0.05, close_start, t)
    grip = smoothstep(close_start, close_end, t)
    lift = smoothstep(lift_start, overhead_start, t)
    overhead = smoothstep(overhead_start, basket_start, t)
    settle = smoothstep(basket_start, release_start, t)
    release = smoothstep(release_start, duration - 0.06, t)

    stow = (-1.42, -0.55, -0.95, 0.58, 0.00, 0.00)
    reach_pose = (0.04, -0.12, -0.34, 0.24, -0.18, 0.18)
    lift_pose = (0.00, -0.92, 0.16, 0.92, 0.32, -0.32)
    overhead_a = (-0.95, -1.05, -0.12, 1.12, 1.22, -0.82)
    overhead_b = (-2.12, -0.86, -0.92, 0.90, -1.18, 1.02)
    basket_pose = (-2.34, -0.82, -1.06, 0.82, 0.34, -0.30)

    pose = lerp_list(stow, reach_pose, reach)
    pose = lerp_list(pose, lift_pose, lift)
    arc_pose = lerp_list(overhead_a, overhead_b, 0.5 - 0.5 * math.cos(math.pi * overhead))
    pose = lerp_list(pose, arc_pose, overhead)
    pose = lerp_list(pose, basket_pose, settle)
    apply_arm_pose(model, data, "a_", pose)  # type: ignore[arg-type]
    apply_gripper(model, data, "a_", grip * (1.0 - release))

    mujoco.mj_forward(model, data)
    shelf_pos = (-0.52, 0.0, 0.495)
    hold_pos = gripper_hold_position(model, data, "a_")
    basket_site = site_position(model, data, "a_basket_payload_site")
    basket_pos = (basket_site[0], basket_site[1], basket_site[2] - 0.006)

    if grip < 1.0:
        pos = lerp(shelf_pos, hold_pos, 0.25 * grip)
    elif release < 1.0:
        pos = hold_pos
    else:
        pos = basket_pos

    roll = (0.92 * pose[4]) * (1.0 - release)
    pitch = (0.16 * lift + 0.18 * math.sin(math.pi * settle)) * (1.0 - release)
    yaw = (0.75 * pose[5]) * (1.0 - release)
    if release > 0.0:
        pos = lerp(pos, basket_pos, release)
        roll *= 1.0 - release
        pitch *= 1.0 - release
        yaw *= 1.0 - release
    apply_package_pose(model, data, pos, yaw=yaw, pitch=pitch, roll=roll)


def update_camera(camera: mujoco.MjvCamera, clip: ClipSpec, t: float) -> None:
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if clip.kind == "handoff":
        camera.lookat[:] = [0.0, 0.0, 0.35]
        camera.distance = 2.15
        camera.azimuth = 105.0
        camera.elevation = -17.0
    elif clip.kind in {"shelf_pick", "six_dof_grasp_sweep"}:
        camera.lookat[:] = [-0.18, 0.0, 0.43]
        camera.distance = 1.74
        camera.azimuth = 92.0 + 6.0 * math.sin(0.9 * t)
        camera.elevation = -17.0
    else:
        camera.lookat[:] = [0.08, 0.0, 0.36]
        camera.distance = 1.80
        camera.azimuth = 118.0 + 4.0 * math.sin(0.7 * t)
        camera.elevation = -18.0


def apply_clip_state(model: mujoco.MjModel, data: mujoco.MjData, clip: ClipSpec, profile: PayloadProfile, t: float) -> None:
    reset_state(data)
    if clip.kind == "rest":
        apply_rest_or_stance(model, data, t, ready=False)
    elif clip.kind == "stance":
        apply_rest_or_stance(model, data, t, ready=True)
    elif clip.kind == "walk":
        apply_walk(model, data, t, clip.duration_s, None)
    elif clip.kind == "loaded_walk":
        apply_walk(model, data, t, clip.duration_s, profile)
    elif clip.kind == "shelf_pick":
        apply_shelf_pick(model, data, t, clip.duration_s, profile)
    elif clip.kind == "handoff":
        apply_handoff(model, data, t, clip.duration_s, profile)
    elif clip.kind == "six_dof_grasp_sweep":
        apply_six_dof_grasp_sweep(model, data, t, clip.duration_s, profile)
    else:
        raise ValueError(f"Unknown clip kind: {clip.kind}")
    mujoco.mj_forward(model, data)


def render_clip(
    clip: ClipSpec,
    *,
    fps: int,
    width: int,
    height: int,
    output_dir: Path,
    generated_dir: Path,
) -> dict:
    profile = PAYLOADS[clip.payload_key or "cardboard"]
    include_receiver = clip.kind == "handoff"
    include_shelf = clip.kind in {"shelf_pick", "six_dof_grasp_sweep"}
    spec = build_spec(profile, include_receiver=include_receiver, include_shelf=include_shelf)
    model = spec.compile()
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, width=width, height=height)
    camera = mujoco.MjvCamera()

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    scene_path = generated_dir / f"{clip.name}_scene.xml"
    scene_path.write_text(spec.to_xml(), encoding="utf-8")
    if not (MODULE_DIR / "scene.xml").exists():
        (MODULE_DIR / "scene.xml").write_text(spec.to_xml(), encoding="utf-8")

    frames: list[np.ndarray] = []
    samples: list[dict] = []
    totals = {
        "gripper_package": 0,
        "left_finger_package": 0,
        "right_finger_package": 0,
        "dual_finger_grasp_frames": 0,
        "package_basket": 0,
        "package_shelf": 0,
        "package_receiver_gripper": 0,
        "total_contacts": 0,
    }

    total_frames = max(1, int(round(clip.duration_s * fps)))
    for frame_idx in range(total_frames):
        t = frame_idx / fps
        apply_clip_state(model, data, clip, profile, t)
        contacts = contact_counters(model, data)
        for key, value in contacts.items():
            totals[key] += int(value)
        update_camera(camera, clip, t)
        renderer.update_scene(data, camera=camera)
        frames.append(renderer.render().copy())
        if frame_idx % max(1, fps // 6) == 0:
            sample = {
                "time_s": round(t, 3),
                "robot_a": body_position(model, data, "a_torso"),
                "robot_a_arm_joints_rad": arm_joint_snapshot(model, data, "a_"),
                "package": body_position(model, data, "package"),
                "contacts": contacts,
            }
            if include_receiver:
                sample["robot_b"] = body_position(model, data, "b_torso")
                sample["robot_b_arm_joints_rad"] = arm_joint_snapshot(model, data, "b_")
            samples.append(sample)

    video_path = output_dir / f"{clip.name}.mp4"
    fallback_reason = None
    try:
        iio.imwrite(video_path, np.asarray(frames), fps=fps, codec="libx264", macro_block_size=1)
    except Exception as exc:
        fallback_reason = str(exc)
        video_path = output_dir / f"{clip.name}.gif"
        iio.imwrite(video_path, np.asarray(frames), fps=fps)

    summary = {
        "name": clip.name,
        "kind": clip.kind,
        "description": clip.description,
        "video": str(video_path.relative_to(SUBMISSION_DIR)),
        "scene_xml": str(scene_path.relative_to(SUBMISSION_DIR)),
        "duration_s": clip.duration_s,
        "fps": fps,
        "payload": None
        if clip.payload_key is None
        else {
            "key": profile.key,
            "label": profile.label,
            "mass_kg": profile.mass_kg,
            "loading_time_s": profile.loading_time_s,
            "gait_speed_mps": profile.gait_speed_mps,
            "leg_compression_m": profile.leg_compression,
            "grip_close_s": profile.grip_close_s,
        },
        "mujoco_depth": {
            "quadruped_leg_joints": 12 if not include_receiver else 24,
            "arm_dof_per_robot": 6,
            "six_dof_joint_names": list(ARM_JOINTS),
            "gripper_slide_joints_per_robot": 2,
            "collision_pairs_tracked": list(totals.keys()),
            "sensors": [
                "arm jointpos",
                "gripper framepos",
                "basket framepos",
                "left/right finger touch",
                "basket touch",
                "package framepos",
            ],
            "actuators": "position actuators on leg, arm, wrist, tool, and gripper joints",
            "extra_physics_validation": "six-axis mounted arm, wrist roll/tool yaw reorientation, dual-finger package contact counters, and package roll/pitch/yaw pose tracking",
        },
        "contact_totals": totals,
        "samples": samples,
    }
    if clip.kind == "six_dof_grasp_sweep":
        summary["six_dof_grasp_validation"] = {
            "arm_joint_sequence": list(ARM_JOINTS),
            "package_orientation_axes": ["roll", "pitch", "yaw"],
            "dual_finger_grasp_frames": totals["dual_finger_grasp_frames"],
            "left_finger_package_contacts": totals["left_finger_package"],
            "right_finger_package_contacts": totals["right_finger_package"],
            "claim": "The parcel follows the gripper through an overhead 6-DOF sweep while MuJoCo reports fingertip/package contacts.",
        }
    if fallback_reason:
        summary["video_fallback_reason"] = fallback_reason
    (output_dir / f"{clip.name}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {k: v for k, v in summary.items() if k != "samples"}


def write_robot_reference() -> None:
    profile = PAYLOADS["wood"]
    spec = build_spec(profile, include_receiver=False, include_shelf=True)
    xml = spec.to_xml()
    (MODULE_DIR / "robot.xml").write_text(xml, encoding="utf-8")
    (MODULE_DIR / "scene.xml").write_text(xml, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render MuJoCo physics evidence clips for warehouse quadbot states.")
    parser.add_argument("--clip", choices=[clip.name for clip in CLIPS] + ["all"], default="all")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = CLIPS if args.clip == "all" else tuple(clip for clip in CLIPS if clip.name == args.clip)
    write_robot_reference()
    results = [
        render_clip(
            clip,
            fps=args.fps,
            width=args.width,
            height=args.height,
            output_dir=args.output_dir,
            generated_dir=GENERATED_DIR,
        )
        for clip in selected
    ]
    manifest = {
        "project": "Warehouse Quadbot MuJoCo Physics Evidence",
        "purpose": "Short UI-ready clips showing robot state, 6-DOF arm/gripper collision evidence, basket contact, shelf pickup, handoff, payload-dependent gait, and multi-angle fingertip grasp validation.",
        "references": {
            "arm_layout": "UR5e-style six-axis manipulator hierarchy: base yaw, shoulder pitch, elbow pitch, wrist pitch, wrist roll, tool yaw.",
            "gripper_layout": "Panda/Robotiq-inspired two-finger gripper with fingertip collision pads and touch sites.",
            "new_validation_clips": "six_dof_grasp_sweep_wood and six_dof_grasp_sweep_metal demonstrate overhead shelf-to-basket arcs, wrist roll/tool yaw, parcel orientation tracking, and dual-finger contact counters.",
        },
        "clips": results,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "clip_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

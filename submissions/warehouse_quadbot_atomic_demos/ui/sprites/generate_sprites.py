#!/usr/bin/env python3
"""Generate warehouse isometric pixel sprite sheets.

The art is code-generated so we can iterate dimensions, anchors, and variants
without hand-editing PNGs. V23 keeps square transparent sprite cells and changes
the exit gate conveyor sprites to cardinal E/S/W/N isometric directions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont


VERSION = 28
SPRITE_SCALE = 2
TILE_W = 64
TILE_H = 32
Z = 32
SHEET_W = 2048
PAD = 8
LABEL_H = 16

OUTLINE = (3, 7, 11, 255)
PAL = {
    "void": (14, 13, 12, 255),
    "floor_edge": (65, 58, 50, 255),
    "floor_dark": (44, 40, 36, 255),
    "floor_hi": (127, 105, 78, 255),
    "cyan": (102, 214, 224, 255),
    "cyan_dim": (56, 126, 132, 255),
    "green": (128, 205, 89, 255),
    "violet": (142, 116, 190, 255),
    "orange": (184, 82, 32, 255),
    "orange_dark": (92, 37, 18, 255),
    "yellow": (217, 153, 45, 255),
    "safety_yellow": (196, 145, 39, 255),
    "amber_light": (239, 167, 62, 255),
    "steel_top": (154, 158, 153, 255),
    "steel_mid": (91, 93, 90, 255),
    "steel_side": (58, 62, 62, 255),
    "steel_dark": (25, 29, 31, 255),
    "rack_blue": (54, 64, 64, 255),
    "rack_blue_dark": (20, 25, 25, 255),
    "white": (224, 225, 218, 255),
    "white_side": (145, 147, 142, 255),
    "warm_wall": (112, 78, 45, 255),
    "cardboard": (133, 89, 48, 255),
    "cardboard_dark": (71, 45, 27, 255),
    "black": (4, 8, 12, 255),
    "shadow": (0, 0, 0, 112),
}

FLOOR_VARIANTS = [
    (61, 76, 82, 255),
    (55, 70, 77, 255),
    (68, 83, 88, 255),
    (50, 64, 70, 255),
    (64, 78, 80, 255),
    (58, 72, 76, 255),
    (73, 86, 88, 255),
    (53, 67, 72, 255),
]

RACK_MATERIALS = {
    "cardboard": {
        "label": "paper/cardboard boxes",
        "pallet": ((105, 82, 46, 255), (88, 65, 38, 255), (64, 47, 31, 255), (42, 31, 24, 255)),
        "boxes": [
            ((139, 103, 70, 255), (174, 127, 80, 255), (84, 57, 37, 255)),
            ((162, 119, 73, 255), (196, 144, 86, 255), (100, 67, 40, 255)),
            ((116, 82, 55, 255), (148, 103, 63, 255), (68, 47, 34, 255)),
        ],
        "label_color": (231, 222, 190, 130),
    },
    "wood": {
        "label": "wood crates",
        "pallet": ((104, 72, 39, 255), (84, 53, 30, 255), (60, 38, 24, 255), (39, 26, 19, 255)),
        "boxes": [
            ((117, 79, 42, 255), (150, 96, 47, 255), (71, 43, 24, 255)),
            ((92, 62, 37, 255), (130, 82, 43, 255), (54, 35, 23, 255)),
            ((142, 96, 49, 255), (172, 111, 55, 255), (85, 52, 27, 255)),
        ],
        "label_color": (228, 180, 95, 130),
    },
    "metal": {
        "label": "metal bins",
        "pallet": ((93, 101, 101, 255), (67, 76, 78, 255), (48, 56, 60, 255), (27, 33, 37, 255)),
        "boxes": [
            ((142, 148, 145, 255), (179, 185, 180, 255), (82, 91, 92, 255)),
            ((105, 118, 123, 255), (145, 158, 160, 255), (60, 71, 76, 255)),
            ((124, 130, 125, 255), (161, 167, 158, 255), (71, 80, 79, 255)),
        ],
        "label_color": (210, 236, 244, 130),
    },
}

RACK_FILL_STATES = {
    "full": "all rack bays stocked",
    "half": "roughly half the rack stocked",
    "almost_none": "only one or two remaining pallets",
    "empty": "empty rack frame and decks",
}

LED_EDGE_MEANINGS = {
    "led_edge_pick_orange": "Orange edge only; shown for rack picking tiles only when that rack is selected.",
    "led_edge_delivery_green": "Green edge only; persistent delivery/truck drop-off zone marker.",
    "led_edge_robot_route_cyan": "Cyan edge only; selected robot current tile and next navigation target.",
    "led_edge_congestion_red": "Red edge only; temporary active congestion zone marker until the blockage is resolved.",
}

DOG_CARGO_TYPES = {
    "cardboard": {
        "label": "light paper/cardboard box",
        "load": 0.28,
        "colors": ((154, 108, 64, 255), (192, 139, 80, 255), (88, 58, 36, 255)),
        "mark": (235, 221, 184, 150),
    },
    "wood": {
        "label": "medium wood crate",
        "load": 0.58,
        "colors": ((118, 78, 40, 255), (154, 98, 46, 255), (70, 42, 24, 255)),
        "mark": (226, 172, 86, 150),
    },
    "metal": {
        "label": "heavy metal box",
        "load": 0.92,
        "colors": ((125, 135, 136, 255), (166, 176, 174, 255), (67, 79, 84, 255)),
        "mark": (210, 236, 244, 160),
    },
}


@dataclass
class Sprite:
    name: str
    w: int
    h: int
    footprint: str
    anchor: tuple[int, int]
    draw: Callable[[ImageDraw.ImageDraw, int, int, int, int], None]
    note: str
    x: int = 0
    y: int = 0


def shade(color: tuple[int, int, int, int], delta: int) -> tuple[int, int, int, int]:
    return (
        max(0, min(255, color[0] + delta)),
        max(0, min(255, color[1] + delta)),
        max(0, min(255, color[2] + delta)),
        color[3],
    )


def mix_color(a: tuple[int, int, int, int], b: tuple[int, int, int, int], t: float) -> tuple[int, int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
        round(a[3] + (b[3] - a[3]) * t),
    )


def p(origin: tuple[int, int], x: float, y: float, z: float = 0) -> tuple[int, int]:
    ox, oy = origin
    return (
        round(ox + (x - y) * TILE_W * 0.5),
        round(oy + (x + y) * TILE_H * 0.5 - z * Z),
    )


def poly(draw: ImageDraw.ImageDraw, points, fill, outline=OUTLINE, width: int = 1) -> None:
    draw.polygon(points, fill=fill)
    if outline:
        draw.line([*points, points[0]], fill=outline, width=width)


def line_outline(draw: ImageDraw.ImageDraw, points, color, width: int = 2, outline=OUTLINE) -> None:
    draw.line(points, fill=outline, width=width + 2)
    draw.line(points, fill=color, width=width)


def iso_box(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    x: float,
    y: float,
    w: float,
    d: float,
    z: float,
    h: float,
    top,
    left,
    right,
    outline=OUTLINE,
) -> None:
    b1 = p(origin, x + w, y, z)
    b2 = p(origin, x + w, y + d, z)
    b3 = p(origin, x, y + d, z)
    t0 = p(origin, x, y, z + h)
    t1 = p(origin, x + w, y, z + h)
    t2 = p(origin, x + w, y + d, z + h)
    t3 = p(origin, x, y + d, z + h)
    poly(draw, [b1, b2, t2, t1], right, outline)
    poly(draw, [b2, b3, t3, t2], left, outline)
    poly(draw, [t0, t1, t2, t3], top, outline)
    draw.line([t0, t1], fill=(232, 244, 246, 96), width=1)
    draw.line([t0, t3], fill=(232, 244, 246, 72), width=1)


def rivet(draw: ImageDraw.ImageDraw, x: int, y: int, metal=False) -> None:
    dark = (25, 22, 19, 255)
    hi = (127, 105, 78, 255) if not metal else (160, 139, 103, 255)
    draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=dark)
    draw.point((x - 1, y - 1), fill=hi)


def inside_floor_diamond(cx: int, cy: int, x: int, y: int, inset: int = 0) -> bool:
    dx = abs(x - cx)
    dy = abs(y - (cy + 16))
    return dx * 16 + dy * 32 <= 512 - inset * 32


def draw_floor_texture(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    fill: tuple[int, int, int, int],
    seed: int,
    *,
    metal: bool,
) -> None:
    hi = shade(fill, 12 if not metal else 18)
    soft_hi = shade(fill, 7 if not metal else 12)
    low = shade(fill, -9 if not metal else -12)
    dark = shade(fill, -16 if not metal else -18)

    # Dense ordered pixel grain, clipped to the isometric diamond. This creates
    # the subtle "woven" tile surface from pixel games without random scratches.
    for yy in range(cy + 3, cy + 30):
        for xx in range(cx - 29, cx + 30):
            if not inside_floor_diamond(cx, cy, xx, yy, inset=2):
                continue
            n = (xx * 17 + yy * 29 + seed * 11 + (xx - cx) * (yy - cy + 5)) & 31
            if n in (0, 9):
                draw.point((xx, yy), fill=soft_hi)
            elif n in (4, 18):
                draw.point((xx, yy), fill=low)

    # Tiny repeating iso-aligned flecks. They are patterned, not arbitrary
    # scratch marks, and they disappear into a clean surface when zoomed out.
    for row in range(0, 7):
        y0 = cy + 6 + row * 3
        phase = (seed + row * 5) % 9
        for col in range(-5, 6):
            x0 = cx + col * 6 + phase - 4
            if not inside_floor_diamond(cx, cy, x0, y0, inset=4):
                continue
            tone = hi if (row + col + seed) % 3 == 0 else dark
            draw.point((x0, y0), fill=tone)
            if inside_floor_diamond(cx, cy, x0 + 1, y0 + 1, inset=4):
                draw.point((x0 + 1, y0 + 1), fill=shade(tone, -3))

    # Broad, barely visible mottling patches, like concrete/paint variation
    # under a pixel-art camera. Kept orthogonal to the tile so it reads as
    # material texture rather than damage.
    patches = [
        (-17 + seed % 5, 10 + seed % 3, 11, 5),
        (2 - seed % 4, 19, 15, 4),
        (-24 + seed % 6, 20 - seed % 2, 10, 3),
    ]
    for px, py, pw, ph in patches:
        for yy in range(cy + py, cy + py + ph):
            for xx in range(cx + px, cx + px + pw):
                if inside_floor_diamond(cx, cy, xx, yy, inset=5) and (xx + yy + seed) % 5 == 0:
                    draw.point((xx, yy), fill=shade(fill, 10 if (px + py) % 2 else -10))


def floor_panel(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    fill: tuple[int, int, int, int],
    seed: int = 0,
    accent=None,
    accent_style: str | None = None,
    metal: bool = False,
) -> None:
    top = (cx, cy)
    right = (cx + 32, cy + 16)
    bottom = (cx, cy + 32)
    left = (cx - 32, cy + 16)

    poly(draw, [(cx, cy + 5), (cx + 32, cy + 21), (cx, cy + 37), (cx - 32, cy + 21)], (8, 6, 4, 120), None)
    poly(draw, [top, right, bottom, left], fill, OUTLINE)
    draw_floor_texture(draw, cx, cy, fill, seed, metal=metal)
    draw.line([left, top, right], fill=shade(fill, 26), width=1)
    draw.line([left, bottom, right], fill=shade(fill, -28), width=1)

    inner = [(cx, cy + 5), (cx + 22, cy + 16), (cx, cy + 27), (cx - 22, cy + 16)]
    draw.line([*inner, inner[0]], fill=shade(fill, -13), width=1)

    # Corner bolts/rivets. The varied seeds keep repeated floor tiles from
    # looking like a single flat carpet.
    for rx, ry in [(cx, cy + 5), (cx + 25, cy + 16), (cx, cy + 28), (cx - 25, cy + 16)]:
        rivet(draw, rx, ry, metal=metal)

    if metal:
        draw.line([(cx - 20, cy + 16), (cx, cy + 6), (cx + 20, cy + 16)], fill=shade(fill, 24), width=1)
        draw.line([(cx - 20, cy + 16), (cx, cy + 26), (cx + 20, cy + 16)], fill=shade(fill, -18), width=1)

    if accent:
        if accent_style == "corner":
            for sx in [-1, 1]:
                draw.line([(cx + sx * 14, cy + 7), (cx + sx * 24, cy + 12)], fill=accent, width=2)
                draw.line([(cx + sx * 24, cy + 20), (cx + sx * 14, cy + 25)], fill=accent, width=2)
        elif accent_style == "dash":
            for offset in [-16, 0, 16]:
                draw.line([(cx + offset - 8, cy + 16), (cx + offset, cy + 12)], fill=accent, width=2)
        elif accent_style == "rack":
            draw.line([(cx - 22, cy + 14), (cx, cy + 4), (cx + 22, cy + 14)], fill=accent, width=2)
            draw.rectangle((cx - 4, cy + 14, cx + 4, cy + 18), fill=shade(fill, -32), outline=accent)
        else:
            draw.line([(cx - 24, cy + 16), (cx, cy + 4), (cx + 24, cy + 16), (cx, cy + 28), (cx - 24, cy + 16)], fill=accent, width=2)


def make_floor_variant(index: int, accent=None, accent_style=None, metal=False):
    fill = FLOOR_VARIANTS[index % len(FLOOR_VARIANTS)]

    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        floor_panel(draw, x + 32, y + 6, fill, seed=index * 7 + 3, accent=accent, accent_style=accent_style, metal=metal)

    return _draw


def with_alpha(color: tuple[int, int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], alpha)


def led_line(draw: ImageDraw.ImageDraw, points, color, width: int = 2) -> None:
    draw.line(points, fill=with_alpha(color, 72), width=width + 4)
    draw.line(points, fill=with_alpha(color, 150), width=width + 2)
    draw.line(points, fill=color, width=width)


def draw_led_edge_overlay(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    color: tuple[int, int, int, int],
) -> None:
    cx = x + 32
    cy = y + 6
    top = (cx, cy)
    right = (cx + 32, cy + 16)
    bottom = (cx, cy + 32)
    left = (cx - 32, cy + 16)

    led_line(draw, [top, right, bottom, left, top], color, width=2)


def make_led_edge_overlay(color: tuple[int, int, int, int]):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_led_edge_overlay(draw, x, y, w, h, color=color)

    return _draw


def draw_depot_zone(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    positions = [
        (x + 64, y + 8),
        (x + 96, y + 24),
        (x + 32, y + 24),
        (x + 64, y + 40),
    ]
    for idx, (cx, cy) in enumerate(positions):
        floor_panel(draw, cx, cy, (69, 63, 54, 255), seed=idx + 30, accent=PAL["safety_yellow"], metal=True)
    cx, cy = x + 64, y + 40
    draw.line([(cx - 54, cy), (cx, cy - 27), (cx + 54, cy), (cx, cy + 27), (cx - 54, cy)], fill=PAL["safety_yellow"], width=2)
    for sx, sy in [(-26, -5), (2, -18), (-2, 14), (27, 1)]:
        draw.rectangle((cx + sx - 6, cy + sy - 4, cx + sx + 6, cy + sy + 4), fill=PAL["floor_dark"], outline=PAL["safety_yellow"])
        draw.point((cx + sx, cy + sy), fill=PAL["amber_light"])


def draw_aegis_robot(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    flip: bool = False,
    carry: bool = False,
    walk: int = 0,
) -> None:
    cx = x + w // 2
    cy = y + h - 14
    direction = -1 if flip else 1
    draw.ellipse((cx - 26, cy - 5, cx + 28, cy + 9), fill=PAL["shadow"])

    # FF reference dog: low horizontal white/gray torso, exposed dark joints,
    # paired linkages, wheel-like feet, compact sensor head, and a front arm.
    leg_sets = [
        (-22, -1, -23 if walk == 1 else -18, 8),
        (-8, 0, -5 if walk == 2 else -9, 10),
        (8, -1, 4 if walk == 1 else 11, 9),
        (22, 0, 24 if walk == 2 else 18, 8),
    ]
    for hip_x, hip_y, foot_x, foot_y in leg_sets:
        hx = cx + direction * hip_x
        hip = (hx, cy - 22 + hip_y)
        knee = (hx - direction * 3, cy - 9 + hip_y)
        fx = cx + direction * foot_x
        foot = (fx, cy + foot_y - 2)
        line_outline(draw, [hip, knee], (178, 181, 176, 255), width=2)
        line_outline(draw, [knee, foot], (91, 96, 96, 255), width=2)
        draw.ellipse((hip[0] - 3, hip[1] - 3, hip[0] + 3, hip[1] + 3), fill=PAL["steel_dark"], outline=OUTLINE)
        draw.point((hip[0] - 1, hip[1] - 1), fill=(198, 202, 196, 255))
        draw.ellipse((knee[0] - 3, knee[1] - 3, knee[0] + 3, knee[1] + 3), fill=(54, 60, 62, 255), outline=OUTLINE)
        draw.ellipse((fx - 5, cy + foot_y - 6, fx + 5, cy + foot_y + 5), fill=OUTLINE)
        draw.ellipse((fx - 3, cy + foot_y - 4, fx + 3, cy + foot_y + 3), fill=(63, 70, 72, 255))
        draw.point((fx - 1, cy + foot_y - 4), fill=(190, 196, 191, 255))

    side = [
        (cx - direction * 28, cy - 27),
        (cx - direction * 8, cy - 23),
        (cx + direction * 22, cy - 25),
        (cx + direction * 23, cy - 16),
        (cx - direction * 24, cy - 17),
    ]
    top = [
        (cx - direction * 29, cy - 34),
        (cx - direction * 10, cy - 41),
        (cx + direction * 24, cy - 33),
        (cx + direction * 22, cy - 25),
        (cx - direction * 28, cy - 27),
    ]
    poly(draw, side, PAL["white_side"], OUTLINE)
    poly(draw, top, PAL["white"], OUTLINE)
    draw.line([top[0], top[1], top[2]], fill=(255, 255, 248, 160), width=1)
    draw.line([(cx - direction * 20, cy - 26), (cx + direction * 13, cy - 24)], fill=(76, 82, 82, 255), width=1)
    draw.line([(cx - direction * 17, cy - 31), (cx + direction * 16, cy - 30)], fill=(172, 177, 173, 255), width=1)
    for joint_x in [-20, -7, 9, 22]:
        draw.rectangle(
            (cx + direction * joint_x - 2, cy - 23, cx + direction * joint_x + 2, cy - 19),
            fill=(44, 51, 54, 255),
            outline=OUTLINE,
        )

    head = [
        (cx + direction * 20, cy - 37),
        (cx + direction * 32, cy - 33),
        (cx + direction * 32, cy - 24),
        (cx + direction * 22, cy - 25),
    ]
    poly(draw, head, (210, 214, 211, 255), OUTLINE)
    face_x = cx + direction * 31
    draw.rectangle((face_x - 3, cy - 32, face_x + 3, cy - 27), fill=(28, 35, 37, 255), outline=OUTLINE)
    draw.point((face_x - 1, cy - 30), fill=(210, 236, 244, 255))
    draw.point((face_x + 2, cy - 30), fill=(210, 236, 244, 255))

    basket_x = cx - direction * 16
    basket = [
        (basket_x - 12, cy - 39),
        (basket_x + 4, cy - 44),
        (basket_x + 17, cy - 39),
        (basket_x + 1, cy - 34),
    ]
    poly(draw, basket, (45, 56, 59, 255), OUTLINE)
    draw.line([basket[0], basket[1], basket[2], basket[3], basket[0]], fill=(136, 150, 148, 255), width=1)
    draw.line([(basket_x - 7, cy - 39), (basket_x + 9, cy - 35)], fill=(91, 105, 106, 255), width=1)

    shoulder = (cx + direction * 23, cy - 29)
    elbow = (cx + direction * 30, cy - 38)
    wrist = (cx + direction * 35, cy - 34)
    line_outline(draw, [shoulder, elbow, wrist], (185, 188, 181, 255), width=2)
    draw.ellipse((shoulder[0] - 3, shoulder[1] - 3, shoulder[0] + 3, shoulder[1] + 3), fill=PAL["steel_dark"], outline=OUTLINE)
    draw.rectangle((wrist[0] - 4, wrist[1] - 3, wrist[0] + 4, wrist[1] + 2), fill=PAL["black"], outline=OUTLINE)

    if carry:
        bx = wrist[0] + direction * 2
        by = wrist[1] - 8
        draw.polygon([(bx - 7, by), (bx + 4, by - 4), (bx + 11, by), (bx, by + 5)], fill=PAL["cardboard"], outline=OUTLINE)
        draw.polygon([(bx - 7, by), (bx, by + 5), (bx, by + 12), (bx - 7, by + 7)], fill=PAL["orange_dark"], outline=OUTLINE)
        draw.polygon([(bx, by + 5), (bx + 11, by), (bx + 11, by + 7), (bx, by + 12)], fill=shade(PAL["cardboard"], 18), outline=OUTLINE)


def robot_drawer(*, flip=False, carry=False, walk=0):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_aegis_robot(draw, x, y, w, h, flip=flip, carry=carry, walk=walk)

    return _draw


DIRECTION_VECTORS = {
    # World/tile directions, not screen-space rotations. The shared isometric
    # camera projects +x down-right and +y down-left.
    "n": (0.0, -1.0),
    "ne": (1.0, -1.0),
    "e": (1.0, 0.0),
    "se": (1.0, 1.0),
    "s": (0.0, 1.0),
    "sw": (-1.0, 1.0),
    "w": (-1.0, 0.0),
    "nw": (-1.0, -1.0),
}


def normalize(vec: tuple[float, float]) -> tuple[float, float]:
    x, y = vec
    length = max((x * x + y * y) ** 0.5, 0.001)
    return (x / length, y / length)


def add2(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] + b[0], a[1] + b[1])


def mul2(a: tuple[float, float], scale: float) -> tuple[float, float]:
    return (a[0] * scale, a[1] * scale)


def pt2(point: tuple[float, float]) -> tuple[int, int]:
    return (round(point[0]), round(point[1]))


def poly2(draw: ImageDraw.ImageDraw, points, fill, outline=OUTLINE, width: int = 1) -> None:
    poly(draw, [pt2(point) for point in points], fill, outline, width)


def iso_model_point(
    origin: tuple[int, int],
    point3: tuple[float, float, float],
    *,
    scale_xy: float = 0.88,
) -> tuple[int, int]:
    x3, y3, z3 = point3
    return p(origin, x3 * scale_xy, y3 * scale_xy, z3)


def oriented_box_3d(
    center: tuple[float, float, float],
    facing: tuple[float, float],
    length: float,
    width: float,
    height: float,
) -> dict[str, tuple[float, float, float]]:
    cx, cy, cz = center
    perp = (-facing[1], facing[0])
    rear = (cx - facing[0] * length * 0.5, cy - facing[1] * length * 0.5)
    front = (cx + facing[0] * length * 0.5, cy + facing[1] * length * 0.5)
    rl = (rear[0] - perp[0] * width * 0.5, rear[1] - perp[1] * width * 0.5, cz)
    fl = (front[0] - perp[0] * width * 0.5, front[1] - perp[1] * width * 0.5, cz)
    fr = (front[0] + perp[0] * width * 0.5, front[1] + perp[1] * width * 0.5, cz)
    rr = (rear[0] + perp[0] * width * 0.5, rear[1] + perp[1] * width * 0.5, cz)
    rlt = (rl[0], rl[1], cz + height)
    flt = (fl[0], fl[1], cz + height)
    frt = (fr[0], fr[1], cz + height)
    rrt = (rr[0], rr[1], cz + height)
    return {
        "rl": rl,
        "fl": fl,
        "fr": fr,
        "rr": rr,
        "rlt": rlt,
        "flt": flt,
        "frt": frt,
        "rrt": rrt,
        "front": (front[0], front[1], cz + height * 0.5),
        "rear": (rear[0], rear[1], cz + height * 0.5),
        "center_top": (cx, cy, cz + height),
    }


def draw_iso_face(draw: ImageDraw.ImageDraw, origin: tuple[int, int], points3, fill, outline=OUTLINE) -> None:
    points = [iso_model_point(origin, point3) for point3 in points3]
    poly(draw, points, fill, outline)


def face_depth(origin: tuple[int, int], points3) -> float:
    points = [iso_model_point(origin, point3) for point3 in points3]
    return sum(point[1] for point in points) / len(points)


def draw_oriented_box_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    center: tuple[float, float, float],
    facing: tuple[float, float],
    length: float,
    width: float,
    height: float,
    *,
    top,
    side_light,
    side_mid,
    side_dark,
) -> dict[str, tuple[float, float, float]]:
    box = oriented_box_3d(center, facing, length, width, height)
    faces = [
        ([box["rl"], box["fl"], box["flt"], box["rlt"]], side_mid),
        ([box["fl"], box["fr"], box["frt"], box["flt"]], side_light),
        ([box["fr"], box["rr"], box["rrt"], box["frt"]], side_dark),
        ([box["rr"], box["rl"], box["rlt"], box["rrt"]], side_mid),
    ]
    for points3, fill in sorted(faces, key=lambda item: face_depth(origin, item[0])):
        draw_iso_face(draw, origin, points3, fill)
    draw_iso_face(draw, origin, [box["rlt"], box["flt"], box["frt"], box["rrt"]], top)
    top_a = iso_model_point(origin, box["rlt"])
    top_b = iso_model_point(origin, box["flt"])
    top_c = iso_model_point(origin, box["frt"])
    draw.line([top_a, top_b, top_c], fill=(255, 255, 248, 150), width=1)
    return box


def draw_iso_joint(draw: ImageDraw.ImageDraw, origin: tuple[int, int], point3, radius: int, color) -> None:
    x2, y2 = iso_model_point(origin, point3)
    draw.ellipse((x2 - radius, y2 - radius, x2 + radius, y2 + radius), fill=OUTLINE)
    draw.ellipse((x2 - radius + 1, y2 - radius + 1, x2 + radius - 1, y2 + radius - 1), fill=color)


def draw_iso_link(draw: ImageDraw.ImageDraw, origin: tuple[int, int], a3, b3, color, width: int = 2) -> None:
    line_outline(draw, [iso_model_point(origin, a3), iso_model_point(origin, b3)], color, width=width)


def draw_robot_wheel(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    radius: int,
    *,
    near_t: float,
    side_view_t: float,
    rim,
) -> None:
    fx, fy = center
    # side_view_t: 1.0 means we see the wheel face from the side, so it is
    # close to circular. 0.0 means front/back view, so the wheel face is a
    # compressed vertical ellipse.
    rx = max(1, round(radius * (0.52 + 0.48 * side_view_t)))
    ry = max(2, radius)
    fill = mix_color((52, 60, 63, 255), (86, 95, 96, 255), near_t)
    inner = mix_color((72, 82, 84, 255), (118, 128, 127, 255), near_t)
    dark = mix_color((22, 29, 32, 255), (36, 44, 46, 255), near_t)

    draw.ellipse((fx - rx - 1, fy - ry - 1, fx + rx + 1, fy + ry + 1), fill=OUTLINE)
    draw.ellipse((fx - rx, fy - ry, fx + rx, fy + ry), fill=fill, outline=rim)
    if rx >= 2 and ry >= 3:
        draw.ellipse((fx - max(1, rx - 1), fy - max(1, ry - 2), fx + max(1, rx - 1), fy + max(1, ry - 2)), outline=inner)
    if side_view_t < 0.45:
        draw.line([(fx, fy - ry + 1), (fx, fy + ry - 1)], fill=dark, width=1)
    elif side_view_t < 0.85:
        draw.point((fx - rx + 1, fy), fill=dark)
        draw.point((fx + rx - 1, fy), fill=mix_color(dark, rim, 0.45))
    if radius >= 3:
        draw.point((fx - max(1, rx // 2), fy - max(1, ry // 2)), fill=(214, 219, 213, 255))


def draw_oriented_slab(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    facing: tuple[float, float],
    length: float,
    width: float,
    *,
    top,
    side,
    side_dark,
    lift: float = 5,
    thickness: float = 8,
) -> dict[str, tuple[float, float]]:
    perp = (-facing[1], facing[0])
    rear = add2(center, mul2(facing, -length * 0.5))
    front = add2(center, mul2(facing, length * 0.5))
    top_shift = (0.0, -lift)
    drop = (0.0, thickness)
    rear_left = add2(add2(rear, mul2(perp, -width * 0.5)), top_shift)
    front_left = add2(add2(front, mul2(perp, -width * 0.5)), top_shift)
    front_right = add2(add2(front, mul2(perp, width * 0.5)), top_shift)
    rear_right = add2(add2(rear, mul2(perp, width * 0.5)), top_shift)
    lower = [add2(point, drop) for point in [rear_left, front_left, front_right, rear_right]]

    poly2(draw, [front_left, front_right, lower[2], lower[1]], side_dark, OUTLINE)
    poly2(draw, [front_right, rear_right, lower[3], lower[2]], side, OUTLINE)
    poly2(draw, [rear_left, front_left, front_right, rear_right], top, OUTLINE)
    draw.line([pt2(rear_left), pt2(front_left), pt2(front_right)], fill=(255, 255, 248, 150), width=1)
    draw.line([pt2(add2(center, mul2(facing, -length * 0.34))), pt2(add2(center, mul2(facing, length * 0.34)))], fill=(76, 82, 82, 255), width=1)
    return {
        "rear": rear,
        "front": front,
        "front_left": front_left,
        "front_right": front_right,
        "rear_left": rear_left,
        "rear_right": rear_right,
    }


def draw_robot_cargo_box(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    cargo_type: str,
    load: float,
    body_center_z: float,
) -> None:
    top, light, dark = DOG_CARGO_TYPES[cargo_type]["colors"]
    cargo_height = 0.135 + 0.035 * (1.0 - load)
    cargo_length = 0.34 + 0.045 * load
    cargo_width = 0.205 + 0.020 * load
    cargo_z = body_center_z + 0.175 + 0.006 * (1.0 - load)
    cargo_along = -0.055 - 0.015 * load
    box = draw_oriented_box_3d(
        draw,
        origin,
        (facing[0] * cargo_along, facing[1] * cargo_along, cargo_z),
        facing,
        cargo_length,
        cargo_width,
        cargo_height,
        top=top,
        side_light=light,
        side_mid=shade(top, -22),
        side_dark=dark,
    )
    label_a = iso_model_point(origin, box["center_top"])
    mark = DOG_CARGO_TYPES[cargo_type]["mark"]
    if cargo_type == "cardboard":
        draw.line([(label_a[0] - 4, label_a[1]), (label_a[0] + 4, label_a[1])], fill=mark, width=1)
        draw.line([(label_a[0], label_a[1] - 3), (label_a[0], label_a[1] + 3)], fill=shade(mark, -24), width=1)
    elif cargo_type == "wood":
        for offset in [-3, 3]:
            draw.line([(label_a[0] - 6, label_a[1] + offset), (label_a[0] + 6, label_a[1] + offset - 2)], fill=mark, width=1)
    elif cargo_type == "metal":
        draw.point((label_a[0] - 3, label_a[1] - 2), fill=mark)
        draw.point((label_a[0] - 2, label_a[1] - 2), fill=mark)
        draw.line([(label_a[0] + 2, label_a[1] + 2), (label_a[0] + 6, label_a[1])], fill=shade(mark, -34), width=1)


def draw_base_robot_dog(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    direction_name: str,
    cargo_type: str | None = None,
) -> None:
    facing = normalize(DIRECTION_VECTORS[direction_name])
    perp = (-facing[1], facing[0])
    origin = (round(x + w * 0.5), round(y + h - 11))
    load = DOG_CARGO_TYPES[cargo_type]["load"] if cargo_type else 0.0
    body_drop = 0.055 * load
    body_length = 0.62 + 0.065 * load
    body_width = 0.25 + 0.025 * load
    body_center_z = 0.32 - body_drop
    hip_z = 0.36 - body_drop * 0.90
    knee_z = 0.17 - body_drop * 0.45
    leg_span = 0.24 + 0.030 * load
    leg_side_offset = 0.145 + 0.008 * load
    foot_side_offset = 0.075 + 0.008 * load
    front_stride = 0.070 + 0.018 * load
    rear_stride = -0.045 - 0.012 * load
    origin_screen = iso_model_point(origin, (0.0, 0.0, 0.0))
    facing_screen = iso_model_point(origin, (facing[0], facing[1], 0.0))
    facing_dx = abs(facing_screen[0] - origin_screen[0])
    facing_dy = abs(facing_screen[1] - origin_screen[1])
    side_view_t = facing_dx / max(1, facing_dx + facing_dy)

    shadow_box = oriented_box_3d((0.0, 0.0, 0.0), facing, 0.84 + 0.08 * load, 0.44 + 0.03 * load, 0.01)
    shadow = [
        iso_model_point(origin, shadow_box["rl"]),
        iso_model_point(origin, shadow_box["fl"]),
        iso_model_point(origin, shadow_box["fr"]),
        iso_model_point(origin, shadow_box["rr"]),
    ]
    draw.polygon(shadow, fill=(0, 0, 0, 88))

    leg_specs = []
    for along in [-leg_span, leg_span]:
        for side in [-1, 1]:
            hip_xy = (
                facing[0] * along + perp[0] * side * leg_side_offset,
                facing[1] * along + perp[1] * side * leg_side_offset,
            )
            knee_xy = (
                hip_xy[0] + facing[0] * (0.035 if along > 0 else -0.035) + perp[0] * side * 0.035,
                hip_xy[1] + facing[1] * (0.035 if along > 0 else -0.035) + perp[1] * side * 0.035,
            )
            foot_xy = (
                hip_xy[0] + facing[0] * (front_stride if along > 0 else rear_stride) + perp[0] * side * foot_side_offset,
                hip_xy[1] + facing[1] * (front_stride if along > 0 else rear_stride) + perp[1] * side * foot_side_offset,
            )
            hip = (hip_xy[0], hip_xy[1], hip_z)
            knee = (knee_xy[0], knee_xy[1], knee_z)
            foot = (foot_xy[0], foot_xy[1], 0.025)
            foot_screen = iso_model_point(origin, foot)
            hip_screen = iso_model_point(origin, hip)
            depth = foot_screen[1] + hip_screen[1] * 0.2
            leg_specs.append((depth, foot_screen[1], side, hip, knee, foot))

    min_foot_y = min(item[1] for item in leg_specs)
    max_foot_y = max(item[1] for item in leg_specs)
    depth_range = max(1, max_foot_y - min_foot_y)

    for _depth, foot_y, _side, hip, knee, foot in sorted(leg_specs, key=lambda item: item[0]):
        # Screen-space y is the actual isometric depth: lower on the screen is
        # closer to camera. Wheel size, joint size, and brightness all follow
        # this value so every direction has coherent near/far wheels.
        near_t = (foot_y - min_foot_y) / depth_range
        upper_leg = mix_color((88, 96, 98, 255), (184, 190, 186, 255), near_t)
        lower_leg = mix_color((47, 55, 58, 255), (116, 126, 128, 255), near_t)
        joint_color = mix_color((45, 53, 56, 255), (70, 78, 80, 255), near_t)
        draw_iso_link(draw, origin, hip, knee, upper_leg, width=1)
        draw_iso_link(draw, origin, knee, foot, lower_leg, width=1)
        knee_radius = 1 if near_t < 0.22 else 2
        draw_iso_joint(draw, origin, knee, knee_radius, joint_color)
        fx, fy = iso_model_point(origin, foot)
        wheel_r = 2 if near_t < 0.34 else (3 if near_t < 0.72 else 4)
        rim = mix_color((92, 102, 104, 255), (154, 163, 160, 255), near_t)
        draw_robot_wheel(draw, (fx, fy), wheel_r, near_t=near_t, side_view_t=side_view_t, rim=rim)

    body = draw_oriented_box_3d(
        draw,
        origin,
        (0.0, 0.0, body_center_z),
        facing,
        body_length,
        body_width,
        0.17,
        top=PAL["white"],
        side_light=(178, 181, 176, 255),
        side_mid=PAL["white_side"],
        side_dark=(91, 99, 101, 255),
    )

    seam_a = iso_model_point(origin, (-facing[0] * 0.21, -facing[1] * 0.21, body_center_z + 0.18))
    seam_b = iso_model_point(origin, (facing[0] * 0.21, facing[1] * 0.21, body_center_z + 0.18))
    draw.line([seam_a, seam_b], fill=(95, 101, 101, 255), width=1)
    for pin in [-0.20, 0.0, 0.20]:
        px, py = iso_model_point(origin, (facing[0] * pin, facing[1] * pin, body_center_z + 0.195))
        draw.point((px, py), fill=(86, 92, 91, 255))
        draw.point((px + 1, py), fill=(186, 190, 185, 255))

    if cargo_type:
        draw_robot_cargo_box(draw, origin, facing, cargo_type, load, body_center_z)

    head_center = (
        facing[0] * (0.43 + 0.025 * load),
        facing[1] * (0.43 + 0.025 * load),
        0.34 - body_drop * 0.55,
    )
    draw_oriented_box_3d(
        draw,
        origin,
        head_center,
        facing,
        0.19,
        0.17,
        0.16,
        top=(215, 218, 213, 255),
        side_light=(178, 184, 181, 255),
        side_mid=(126, 135, 136, 255),
        side_dark=(78, 88, 91, 255),
    )
    sensor = (
        facing[0] * (0.57 + 0.025 * load),
        facing[1] * (0.57 + 0.025 * load),
        0.44 - body_drop * 0.55,
    )
    sx, sy = iso_model_point(origin, sensor)
    draw.rectangle((sx - 3, sy - 3, sx + 3, sy + 2), fill=(25, 34, 37, 255), outline=OUTLINE)
    draw.point((sx - 1, sy - 1), fill=(210, 236, 244, 255))
    draw.point((sx + 2, sy - 1), fill=(210, 236, 244, 255))


def base_robot_drawer(direction_name: str, cargo_type: str | None = None):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_base_robot_dog(draw, x, y, w, h, direction_name=direction_name, cargo_type=cargo_type)

    return _draw


def draw_pallet_box(draw: ImageDraw.ImageDraw, origin: tuple[int, int], x: float, y: float, z: float, idx: int) -> None:
    palettes = [
        (PAL["cardboard"], PAL["cardboard_dark"], shade(PAL["cardboard"], 18)),
        ((117, 81, 45, 255), (60, 39, 25, 255), (147, 94, 50, 255)),
        ((92, 75, 55, 255), (48, 38, 30, 255), (120, 94, 62, 255)),
        ((158, 123, 72, 255), (82, 57, 33, 255), (185, 137, 77, 255)),
        ((104, 99, 84, 255), (53, 49, 42, 255), (128, 119, 95, 255)),
    ]
    top, left, right = palettes[idx % len(palettes)]
    iso_box(draw, origin, x, y, 0.24, 0.25, z, 0.18, top, left, right)
    a = p(origin, x + 0.05, y + 0.04, z + 0.18)
    b = p(origin, x + 0.19, y + 0.04, z + 0.18)
    draw.line([a, b], fill=(255, 255, 255, 110), width=1)


def draw_pallet(draw: ImageDraw.ImageDraw, origin: tuple[int, int], x: float, y: float, z: float, width: float = 0.75) -> None:
    iso_box(draw, origin, x, y, width, 0.42, z, 0.06, (110, 73, 38, 255), (55, 34, 20, 255), (84, 52, 27, 255))
    for stripe in [0.10, 0.32, 0.54]:
        a = p(origin, x + stripe, y + 0.02, z + 0.07)
        b = p(origin, x + stripe + 0.11, y + 0.38, z + 0.07)
        draw.line([a, b], fill=(150, 97, 42, 255), width=1)


def rack_origin(x: int, y: int, w: int, h: int, length: int) -> tuple[int, int]:
    return (x + w // 2 - (length - 1) * 16, y + h - 54)


def draw_rack_post(draw: ImageDraw.ImageDraw, origin: tuple[int, int], x: float, y: float, height: float) -> None:
    iso_box(draw, origin, x, y, 0.08, 0.08, 0.04, height, (72, 83, 82, 255), PAL["rack_blue_dark"], PAL["rack_blue"])
    foot = p(origin, x + 0.04, y + 0.04, 0.04)
    draw.rectangle((foot[0] - 3, foot[1] - 1, foot[0] + 3, foot[1] + 1), fill=PAL["safety_yellow"], outline=OUTLINE)


def draw_pallet_rack(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, tiers: int, length: int = 2) -> None:
    origin = rack_origin(x, y, w, h, length)
    height = 0.35 + tiers * 0.42

    footprint = [p(origin, 0, 0, 0), p(origin, length, 0, 0), p(origin, length, 1, 0), p(origin, 0, 1, 0)]
    poly(draw, footprint, (54, 47, 40, 220), OUTLINE)
    draw.line([footprint[0], footprint[1]], fill=(109, 82, 53, 255), width=1)
    draw.line([footprint[3], footprint[2]], fill=(8, 19, 26, 255), width=1)

    for bay in range(length + 1):
        draw_rack_post(draw, origin, bay - 0.04, -0.02, height)
        draw_rack_post(draw, origin, bay - 0.04, 0.94, height)

    for level in range(tiers):
        z = 0.25 + level * 0.42
        # Real pallet racks read through orange load beams on the front/back.
        iso_box(draw, origin, -0.02, -0.01, length + 0.04, 0.08, z, 0.08, (165, 73, 30, 255), (82, 32, 15, 255), (120, 47, 20, 255))
        iso_box(draw, origin, -0.02, 0.93, length + 0.04, 0.08, z, 0.08, (165, 73, 30, 255), (82, 32, 15, 255), (120, 47, 20, 255))
        iso_box(draw, origin, 0.03, 0.16, length - 0.06, 0.68, z - 0.04, 0.04, (63, 59, 53, 255), (24, 25, 25, 255), (42, 42, 39, 255))
        draw.line([p(origin, 0.08, 0.88, z + 0.07), p(origin, length - 0.08, 0.88, z + 0.07)], fill=(131, 83, 42, 255), width=1)

        for bay in range(length):
            draw_pallet(draw, origin, bay + 0.12, 0.28, z + 0.02, width=0.74)
            for stack in range(3):
                if (bay + level + stack) % 5 == 0:
                    continue
                draw_pallet_box(draw, origin, bay + 0.18 + stack * 0.20, 0.32 + (stack % 2) * 0.17, z + 0.09 + stack * 0.05, bay + level + stack)

    # Diagonal side bracing, visible like a real rack frame.
    for bay in range(length):
        a = p(origin, bay + 0.02, -0.02, 0.16)
        b = p(origin, bay + 0.98, -0.02, height - 0.06)
        line_outline(draw, [a, b], (104, 109, 102, 255), width=1)
        a2 = p(origin, bay + 0.98, 0.98, 0.16)
        b2 = p(origin, bay + 0.02, 0.98, height - 0.06)
        line_outline(draw, [a2, b2], (72, 78, 75, 255), width=1)


def make_rack(tiers: int, length: int = 2):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_pallet_rack(draw, x, y, w, h, tiers, length)

    return _draw


RACK_SCREEN_DIRECTIONS = {
    "ne": (0.0, -1.0),
    "se": (1.0, 0.0),
    "sw": (0.0, 1.0),
    "nw": (-1.0, 0.0),
}


def point3_from_basis(
    facing: tuple[float, float],
    along: float,
    side: float,
    z: float,
) -> tuple[float, float, float]:
    perp = (-facing[1], facing[0])
    return (
        facing[0] * along + perp[0] * side,
        facing[1] * along + perp[1] * side,
        z,
    )


def draw_rack_box_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    along: float,
    side: float,
    z: float,
    length: float,
    width: float,
    height: float,
    *,
    top,
    side_light,
    side_mid,
    side_dark,
) -> None:
    center = point3_from_basis(facing, along, side, z)
    draw_oriented_box_3d(
        draw,
        origin,
        center,
        facing,
        length,
        width,
        height,
        top=top,
        side_light=side_light,
        side_mid=side_mid,
        side_dark=side_dark,
    )


def draw_rack_line_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    color,
    width: int = 1,
) -> None:
    draw_iso_link(
        draw,
        origin,
        point3_from_basis(facing, a[0], a[1], a[2]),
        point3_from_basis(facing, b[0], b[1], b[2]),
        color,
        width=width,
    )


def draw_pallet_load_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    bay_center: float,
    z: float,
    idx: int,
) -> None:
    draw_rack_box_3d(
        draw,
        origin,
        facing,
        bay_center,
        0.0,
        z,
        0.72,
        0.38,
        0.05,
        top=(112, 73, 38, 255),
        side_light=(96, 59, 29, 255),
        side_mid=(74, 47, 27, 255),
        side_dark=(50, 32, 21, 255),
    )

    box_palettes = [
        (PAL["cardboard"], shade(PAL["cardboard"], 18), PAL["cardboard_dark"]),
        ((118, 86, 54, 255), (154, 108, 61, 255), (63, 43, 28, 255)),
        ((91, 82, 66, 255), (123, 112, 87, 255), (48, 42, 34, 255)),
    ]
    offsets = [(-0.20, -0.08), (0.02, 0.09), (0.21, -0.06)]
    for box_idx, (along_offset, side_offset) in enumerate(offsets):
        if (idx + box_idx) % 5 == 0:
            continue
        top, light, dark = box_palettes[(idx + box_idx) % len(box_palettes)]
        draw_rack_box_3d(
            draw,
            origin,
            facing,
            bay_center + along_offset,
            side_offset,
            z + 0.06 + box_idx * 0.025,
            0.22,
            0.20,
            0.16,
            top=top,
            side_light=light,
            side_mid=shade(top, -24),
            side_dark=dark,
        )


def draw_rack_upright_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    along: float,
    side: float,
    height: float,
    *,
    near: bool,
) -> None:
    draw_rack_box_3d(
        draw,
        origin,
        facing,
        along,
        side,
        0.03,
        0.068,
        0.068,
        height,
        top=(92, 139, 116, 255) if near else (57, 93, 79, 255),
        side_light=(70, 124, 100, 255) if near else (42, 75, 66, 255),
        side_mid=(42, 91, 74, 255) if near else (29, 58, 53, 255),
        side_dark=(17, 42, 39, 255),
    )
    for idx, z in enumerate([0.20, 0.32, 0.44, 0.56, 0.68, 0.80, 0.92, 1.04]):
        if z > height - 0.03:
            continue
        hx, hy = iso_model_point(origin, point3_from_basis(facing, along, side + (0.012 if near else -0.012), z))
        hole = (7, 24, 25, 255)
        draw.rectangle((hx - 1, hy - 1, hx + 1, hy), fill=hole)
        if idx % 2 == 0:
            draw.point((hx + 1, hy - 1), fill=(118, 159, 135, 255))


def draw_rack_beam_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    side: float,
    z: float,
    length: float,
    *,
    bright: bool,
) -> None:
    draw_rack_box_3d(
        draw,
        origin,
        facing,
        0.0,
        side,
        z,
        length + 0.12,
        0.060,
        0.072,
        top=(236, 113, 31, 255) if bright else (177, 80, 30, 255),
        side_light=(210, 90, 24, 255) if bright else (136, 57, 22, 255),
        side_mid=(144, 55, 18, 255) if bright else (96, 39, 18, 255),
        side_dark=(74, 27, 12, 255),
    )


def draw_deck_panel_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    z: float,
    length: float,
    width: float,
) -> None:
    draw_rack_box_3d(
        draw,
        origin,
        facing,
        0.0,
        0.0,
        z,
        length - 0.12,
        width - 0.16,
        0.028,
        top=(112, 115, 108, 255),
        side_light=(82, 86, 83, 255),
        side_mid=(58, 63, 62, 255),
        side_dark=(32, 37, 38, 255),
    )
    for step in range(1, int(length * 2)):
        along = -length * 0.5 + step * 0.5
        a = iso_model_point(origin, point3_from_basis(facing, along, -width * 0.33, z + 0.035))
        b = iso_model_point(origin, point3_from_basis(facing, along, width * 0.33, z + 0.035))
        draw.line([a, b], fill=(144, 147, 138, 115), width=1)


def rack_slot_has_load(
    *,
    fill_state: str,
    length_tiles: int,
    bay: int,
    level: int,
    slot_index: int,
) -> bool:
    if fill_state == "empty":
        return False
    if fill_state == "full":
        return True
    if fill_state == "half":
        return (bay + level + slot_index) % 2 == 0
    if fill_state == "almost_none":
        if length_tiles <= 2:
            return bay == 0 and level == 0 and slot_index == 0
        return (bay, level, slot_index) in {(0, 0, 0), (length_tiles - 1, 1, 1)}
    return True


def draw_rack_pallet_stack_3d(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    bay_center: float,
    z: float,
    idx: int,
    *,
    material: str,
    fullness: float,
) -> None:
    mat = RACK_MATERIALS[material]
    pallet_top, pallet_light, pallet_mid, pallet_dark = mat["pallet"]
    draw_rack_box_3d(
        draw,
        origin,
        facing,
        bay_center,
        -0.02,
        z,
        0.72,
        0.42,
        0.050,
        top=pallet_top,
        side_light=pallet_light,
        side_mid=pallet_mid,
        side_dark=pallet_dark,
    )
    box_palettes = mat["boxes"]
    positions = [(-0.22, -0.11, 0.00), (0.02, 0.05, 0.02), (0.23, -0.08, 0.04), (-0.04, -0.08, 0.17)]
    count = max(1, min(len(positions), round(len(positions) * fullness)))
    selected_positions = positions[:count]
    for box_idx, (along_offset, side_offset, z_offset) in enumerate(selected_positions):
        top, light, dark = box_palettes[(idx + box_idx) % len(box_palettes)]
        draw_rack_box_3d(
            draw,
            origin,
            facing,
            bay_center + along_offset,
            side_offset,
            z + 0.065 + z_offset,
            0.22,
            0.18,
            0.13,
            top=top,
            side_light=light,
            side_mid=shade(top, -20),
            side_dark=dark,
        )
        label = iso_model_point(origin, point3_from_basis(facing, bay_center + along_offset + 0.04, side_offset + 0.09, z + 0.12 + z_offset))
        draw.line([(label[0] - 2, label[1]), (label[0] + 2, label[1])], fill=mat["label_color"], width=1)
        if material == "wood":
            a = iso_model_point(origin, point3_from_basis(facing, bay_center + along_offset - 0.07, side_offset - 0.03, z + 0.15 + z_offset))
            b = iso_model_point(origin, point3_from_basis(facing, bay_center + along_offset + 0.07, side_offset - 0.03, z + 0.15 + z_offset))
            draw.line([a, b], fill=(67, 39, 21, 165), width=1)
        elif material == "metal":
            spec = iso_model_point(origin, point3_from_basis(facing, bay_center + along_offset - 0.04, side_offset - 0.03, z + 0.19 + z_offset))
            draw.point(spec, fill=(231, 245, 244, 180))
            draw.point((spec[0] + 1, spec[1]), fill=(190, 209, 211, 150))


def draw_pallet_rack_3d(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    length_tiles: int,
    tiers: int,
    direction_name: str,
    material: str,
    fill_state: str,
) -> None:
    facing = normalize(RACK_SCREEN_DIRECTIONS[direction_name])
    origin = (x + w // 2, y + h - 38)
    length = float(length_tiles)
    rack_width = 1.00
    level_gap = 0.52
    shelf_base_z = 0.22
    rack_height = 0.40 + tiers * level_gap
    half_len = length * 0.5
    half_width = rack_width * 0.5

    footprint_box = oriented_box_3d((0.0, 0.0, 0.0), facing, length + 0.10, rack_width + 0.10, 0.01)
    footprint = [
        iso_model_point(origin, footprint_box["rl"]),
        iso_model_point(origin, footprint_box["fl"]),
        iso_model_point(origin, footprint_box["fr"]),
        iso_model_point(origin, footprint_box["rr"]),
    ]
    draw.polygon(footprint, fill=(0, 0, 0, 78))
    draw.line([footprint[0], footprint[1], footprint[2], footprint[3], footprint[0]], fill=(18, 42, 38, 190), width=1)

    open_side = half_width
    back_side = -half_width

    # Back rails are quiet and drawn first. The open picking face is reserved
    # for orange load beams, so the rack reads like a Costco pallet rack.
    for level in range(tiers + 1):
        z = 0.16 + level * level_gap
        draw_rack_line_3d(draw, origin, facing, (-half_len, back_side, z), (half_len, back_side, z), (35, 78, 64, 255))
        draw_rack_line_3d(draw, origin, facing, (-half_len, back_side, z + 0.05), (half_len, back_side, z + 0.05), (21, 51, 46, 255))

    # Diagonal side-frame bracing belongs on the narrow ends, not across the
    # pick face. This matches the user's 1x1 rack sketch and real warehouse
    # pallet rack construction.
    for along in [-half_len, half_len]:
        draw_rack_line_3d(draw, origin, facing, (along, back_side, 0.16), (along, open_side, rack_height - 0.12), (70, 126, 100, 255))
        draw_rack_line_3d(draw, origin, facing, (along, open_side, 0.20), (along, back_side, rack_height - 0.06), (34, 83, 68, 255))

    bay_centers = [-half_len + 0.5 + bay for bay in range(length_tiles)]
    fill_amount = {
        "full": 1.0,
        "half": 0.72,
        "almost_none": 0.40,
        "empty": 0.0,
    }[fill_state]
    for level in range(tiers):
        z = shelf_base_z + level * level_gap
        draw_deck_panel_3d(draw, origin, facing, z - 0.035, length, rack_width)
        draw_rack_beam_3d(draw, origin, facing, back_side, z, length, bright=False)
        for bay, bay_center in enumerate(bay_centers):
            slot_index = level * length_tiles + bay
            if rack_slot_has_load(fill_state=fill_state, length_tiles=length_tiles, bay=bay, level=level, slot_index=slot_index):
                draw_rack_pallet_stack_3d(
                    draw,
                    origin,
                    facing,
                    bay_center,
                    z + 0.02,
                    bay + level * 3,
                    material=material,
                    fullness=fill_amount,
                )
        draw_rack_beam_3d(draw, origin, facing, open_side, z + 0.008, length, bright=True)

    for side in [back_side, open_side]:
        draw_rack_beam_3d(draw, origin, facing, side, rack_height - 0.05, length, bright=side == open_side)

    for along in [-half_len + bay for bay in range(length_tiles + 1)]:
        for side in [-half_width, half_width]:
            draw_rack_upright_3d(draw, origin, facing, along, side, rack_height, near=side == open_side)
            foot = iso_model_point(origin, point3_from_basis(facing, along, side, 0.04))
            draw.rectangle((foot[0] - 4, foot[1] - 1, foot[0] + 4, foot[1] + 2), fill=(195, 143, 39, 255), outline=OUTLINE)


def rack3d_drawer(length_tiles: int, tiers: int, direction_name: str, material: str, fill_state: str):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_pallet_rack_3d(
            draw,
            x,
            y,
            w,
            h,
            length_tiles=length_tiles,
            tiers=tiers,
            direction_name=direction_name,
            material=material,
            fill_state=fill_state,
        )

    return _draw


def source_side(sprite: Sprite) -> int:
    return max(sprite.w, sprite.h)


def source_offset(sprite: Sprite) -> tuple[int, int]:
    side = source_side(sprite)
    return ((side - sprite.w) // 2, (side - sprite.h) // 2)


def final_w(sprite: Sprite) -> int:
    return source_side(sprite) * SPRITE_SCALE


def final_h(sprite: Sprite) -> int:
    return source_side(sprite) * SPRITE_SCALE


def final_anchor(sprite: Sprite) -> tuple[int, int]:
    offset_x, offset_y = source_offset(sprite)
    return ((sprite.anchor[0] + offset_x) * SPRITE_SCALE, (sprite.anchor[1] + offset_y) * SPRITE_SCALE)


def render_sprite(sprite: Sprite) -> Image.Image:
    side = source_side(sprite)
    offset_x, offset_y = source_offset(sprite)
    sprite_img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sprite_draw = ImageDraw.Draw(sprite_img)
    sprite.draw(sprite_draw, offset_x, offset_y, sprite.w, sprite.h)
    if SPRITE_SCALE == 1:
        return sprite_img
    return sprite_img.resize((final_w(sprite), final_h(sprite)), Image.Resampling.NEAREST)


def draw_computer_terminal(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    frame: int = 0,
    direction_name: str = "e",
) -> None:
    origin = (x + w // 2, y + h - 20)
    beige = (53, 62, 66, 255)
    beige_hi = (88, 100, 101, 255)
    beige_mid = (38, 47, 52, 255)
    beige_dark = (20, 26, 31, 255)
    mauve_dark = (11, 17, 23, 255)
    screen_dark = (5, 15, 24, 255)
    screen_glow = shade((83, 220, 176, 255), 18 if frame == 1 else (-18 if frame == 3 else 0))

    facing = normalize(DIRECTION_VECTORS.get(direction_name, DIRECTION_VECTORS["e"]))
    perp = (-facing[1], facing[0])

    base_length = 0.92
    base_width = 0.86
    body_length = 0.72
    body_width = 0.66
    body_z = 0.16
    body_h = 1.18
    front_offset = body_length * 0.5 + 0.008
    side_offset = body_width * 0.5 + 0.008

    shadow_box = oriented_box_3d((0.0, 0.0, 0.0), facing, base_length + 0.16, base_width + 0.14, 0.01)
    draw.polygon(
        [iso_model_point(origin, shadow_box[key]) for key in ["rl", "fl", "fr", "rr"]],
        fill=(0, 0, 0, 86),
    )

    draw_oriented_box_3d(
        draw,
        origin,
        (0.0, 0.0, 0.0),
        facing,
        base_length,
        base_width,
        body_z,
        top=beige_hi,
        side_light=beige_mid,
        side_mid=beige_dark,
        side_dark=(10, 15, 19, 255),
    )
    body = draw_oriented_box_3d(
        draw,
        origin,
        (0.0, 0.0, body_z),
        facing,
        body_length,
        body_width,
        body_h,
        top=beige_hi,
        side_light=beige,
        side_mid=beige_mid,
        side_dark=(13, 18, 22, 255),
    )

    def model_point(along: float, side: float, z: float) -> tuple[float, float, float]:
        return (
            facing[0] * along + perp[0] * side,
            facing[1] * along + perp[1] * side,
            z,
        )

    def face_pt(side: float, z: float) -> tuple[int, int]:
        return iso_model_point(origin, model_point(front_offset, side, z))

    def face_poly(s0: float, s1: float, z0: float, z1: float, fill, outline=OUTLINE) -> None:
        poly(draw, [face_pt(s0, z0), face_pt(s1, z0), face_pt(s1, z1), face_pt(s0, z1)], fill, outline)

    def side_pt(along: float, z: float) -> tuple[int, int]:
        return iso_model_point(origin, model_point(along, side_offset, z))

    # Recessed CRT bezel and live order/scheduler display.
    face_poly(-0.21, 0.21, 0.72, 1.08, mauve_dark)
    face_poly(-0.16, 0.16, 0.78, 1.01, screen_dark, outline=(19, 24, 35, 255))
    screen_patterns = [
        [(-0.13, 0.08, 0.96, screen_glow), (-0.13, 0.01, 0.88, PAL["green"]), (-0.13, 0.05, 0.82, PAL["amber_light"])],
        [(-0.13, 0.10, 0.97, screen_glow), (-0.13, 0.07, 0.89, PAL["green"]), (-0.09, -0.01, 0.83, PAL["cyan_dim"])],
        [(-0.12, 0.02, 0.99, PAL["green"]), (-0.13, 0.10, 0.91, screen_glow), (-0.05, 0.08, 0.84, PAL["amber_light"])],
        [(-0.13, 0.07, 0.96, shade(screen_glow, -24)), (-0.09, 0.10, 0.88, PAL["cyan_dim"]), (-0.13, -0.02, 0.83, PAL["green"])],
    ]
    for s0, s1, z0, color in screen_patterns[frame % len(screen_patterns)]:
        draw.line([face_pt(s0, z0), face_pt(s1, z0)], fill=color, width=1)
    scan_z = 1.01 - (frame % 4) * 0.065
    draw.line([face_pt(-0.15, scan_z), face_pt(0.14, scan_z)], fill=(166, 248, 219, 72), width=1)
    if frame != 2:
        dot = face_pt(0.13, 0.80)
        draw.point(dot, fill=screen_glow)

    # RGB status LEDs and floppy/server bay details from the reference.
    badge_x, badge_y = face_pt(-0.26, 0.42)
    for index, color in enumerate([(232, 70, 58, 255), (86, 214, 102, 255), (72, 158, 238, 255)]):
        draw.line([(badge_x + index * 3, badge_y + index), (badge_x + index * 3 + 5, badge_y + index + 2)], fill=color, width=1)
    face_poly(0.02, 0.24, 0.43, 0.49, mauve_dark)
    draw.line([face_pt(0.06, 0.46), face_pt(0.20, 0.46)], fill=(31, 37, 49, 255), width=1)
    face_poly(0.20, 0.29, 0.51, 0.57, (68, 78, 92, 255))

    # Side panel details make the object read as an angled warehouse server.
    for z0 in [0.34, 0.42, 0.50]:
        draw.line([side_pt(-0.18, z0), side_pt(0.08, z0)], fill=(95, 111, 113, 155), width=1)
    draw.line([side_pt(-0.20, 1.12), side_pt(0.16, 1.12)], fill=beige_hi, width=1)
    draw.line(
        [iso_model_point(origin, body["rlt"]), iso_model_point(origin, body["flt"]), iso_model_point(origin, body["frt"])],
        fill=(143, 169, 170, 145),
        width=1,
    )

    # Warehouse-server status LEDs and tiny ventilation pixels.
    led_colors = [(232, 70, 58, 255), PAL["green"], (72, 158, 238, 255)]
    for index, led_color in enumerate(led_colors):
        color = led_color if (frame + index) % 4 != 0 else shade(led_color, -70)
        draw.point(face_pt(-0.25 + index * 0.05, 0.26), fill=color)
    for z0 in [0.21, 0.17]:
        for side in [-0.25, -0.16, -0.07, 0.02, 0.11]:
            draw.point(face_pt(side, z0), fill=beige_dark)


def computer_terminal_drawer(frame: int):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_computer_terminal(draw, x, y, w, h, frame=frame)

    return _draw


def computer_terminal_directional_drawer(direction_name: str, frame: int):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_computer_terminal(draw, x, y, w, h, frame=frame, direction_name=direction_name)

    return _draw


def draw_exit_gate(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    direction_name: str = "e",
    frame: int = 0,
) -> None:
    facing = normalize(DIRECTION_VECTORS[direction_name])
    perp = (-facing[1], facing[0])
    origin = (round(x + w * 0.5), round(y + h - 46))
    length = 2.72
    belt_width = 0.64

    shadow_box = oriented_box_3d((0.0, 0.0, 0.0), facing, 2.96, 1.24, 0.01)
    shadow = [
        iso_model_point(origin, shadow_box["rl"]),
        iso_model_point(origin, shadow_box["fl"]),
        iso_model_point(origin, shadow_box["fr"]),
        iso_model_point(origin, shadow_box["rr"]),
    ]
    draw.polygon(shadow, fill=(0, 0, 0, 86))

    gate_center = (facing[0] * 1.36, facing[1] * 1.36, 0.20)
    gate_over_belt = direction_name in {"s", "e"}

    def draw_gate_components() -> None:
        nonlocal gate_center
        draw_oriented_box_3d(
            draw,
            origin,
            gate_center,
            facing,
            0.24,
            1.22,
            1.22,
            top=(145, 140, 126, 255),
            side_light=(105, 101, 91, 255),
            side_mid=(82, 79, 73, 255),
            side_dark=(48, 50, 49, 255),
        )
        hood_center = (gate_center[0] - facing[0] * 0.02, gate_center[1] - facing[1] * 0.02, 1.48)
        draw_oriented_box_3d(
            draw,
            origin,
            hood_center,
            facing,
            0.34,
            1.36,
            0.12,
            top=(178, 160, 118, 255),
            side_light=(105, 92, 70, 255),
            side_mid=(78, 67, 54, 255),
            side_dark=(43, 42, 39, 255),
        )
        for side in [-1, 1]:
            post_center = (
                gate_center[0] + perp[0] * side * 0.67,
                gate_center[1] + perp[1] * side * 0.67,
                0.18,
            )
            draw_oriented_box_3d(
                draw,
                origin,
                post_center,
                facing,
                0.13,
                0.13,
                1.38,
                top=PAL["safety_yellow"],
                side_light=PAL["orange"],
                side_mid=PAL["orange_dark"],
                side_dark=(62, 28, 15, 255),
            )

        # Sectional roll-up door slats. A one-pixel highlight shifts slightly by
        # frame, giving the door a live industrial shimmer without changing state.
        for i in range(9):
            z = 0.34 + i * 0.12
            shift = 0.02 if (i + frame) % 3 == 0 else 0.0
            a3 = (
                gate_center[0] + facing[0] * -0.14 + perp[0] * (-0.54 + shift),
                gate_center[1] + facing[1] * -0.14 + perp[1] * (-0.54 + shift),
                z,
            )
            b3 = (
                gate_center[0] + facing[0] * -0.14 + perp[0] * (0.54 + shift),
                gate_center[1] + facing[1] * -0.14 + perp[1] * (0.54 + shift),
                z,
            )
            draw.line([iso_model_point(origin, a3), iso_model_point(origin, b3)], fill=(200, 182, 142, 185), width=1)

    def draw_gate_bed_and_moving_parts() -> None:
        nonlocal gate_center
        draw_oriented_box_3d(
            draw,
            origin,
            (-facing[0] * 0.08, -facing[1] * 0.08, 0.0),
            facing,
            length,
            0.82,
            0.20,
            top=(72, 72, 66, 255),
            side_light=(56, 59, 57, 255),
            side_mid=(38, 43, 43, 255),
            side_dark=(22, 26, 27, 255),
        )
        belt_box = oriented_box_3d((-facing[0] * 0.08, -facing[1] * 0.08, 0.205), facing, length - 0.24, belt_width, 0.01)
        draw_iso_face(
            draw,
            origin,
            [belt_box["rlt"], belt_box["flt"], belt_box["frt"], belt_box["rrt"]],
            (28, 31, 31, 255),
        )

        phase = (frame % 4) * 0.065
        for i in range(13):
            along = -1.22 + ((i * 0.22 + phase) % 2.44)
            center = (facing[0] * along - facing[0] * 0.08, facing[1] * along - facing[1] * 0.08)
            a3 = (center[0] + perp[0] * -0.28, center[1] + perp[1] * -0.28, 0.245)
            b3 = (center[0] + perp[0] * 0.28, center[1] + perp[1] * 0.28, 0.245)
            draw.line([iso_model_point(origin, a3), iso_model_point(origin, b3)], fill=(116, 111, 96, 255), width=1)

        edge_side = 0.43
        draw.line(
            [
                iso_model_point(
                    origin,
                    (
                        -facing[0] * 1.30 + perp[0] * edge_side,
                        -facing[1] * 1.30 + perp[1] * edge_side,
                        0.245,
                    ),
                ),
                iso_model_point(
                    origin,
                    (
                        facing[0] * 1.08 + perp[0] * edge_side,
                        facing[1] * 1.08 + perp[1] * edge_side,
                        0.245,
                    ),
                ),
            ],
            fill=PAL["amber_light"],
            width=2,
        )

        parcel_bases = [-0.86, -0.28, 0.38, 0.94]
        for i, base in enumerate(parcel_bases):
            along = -1.10 + ((base + frame * 0.18 + 1.10) % 2.18)
            side_offset = -0.11 if i % 2 == 0 else 0.12
            center = (
                facing[0] * along + perp[0] * side_offset - facing[0] * 0.08,
                facing[1] * along + perp[1] * side_offset - facing[1] * 0.08,
                0.265,
            )
            draw_oriented_box_3d(
                draw,
                origin,
                center,
                facing,
                0.30,
                0.24,
                0.12,
                top=shade(PAL["cardboard"], 18 if i % 2 else 0),
                side_light=(170, 117, 65, 255),
                side_mid=PAL["cardboard"],
                side_dark=PAL["cardboard_dark"],
            )

        control_side = 0.67
        control_base = (
            facing[0] * 0.96 + perp[0] * control_side,
            facing[1] * 0.96 + perp[1] * control_side,
            0.06,
        )
        draw_oriented_box_3d(
            draw,
            origin,
            control_base,
            facing,
            0.12,
            0.12,
            0.58,
            top=PAL["yellow"],
            side_light=PAL["orange"],
            side_mid=PAL["orange_dark"],
            side_dark=(62, 28, 15, 255),
        )
        panel = iso_model_point(origin, (control_base[0], control_base[1], 0.62))
        draw.rectangle((panel[0] - 4, panel[1] - 7, panel[0] + 4, panel[1] + 6), fill=PAL["steel_dark"], outline=PAL["amber_light"])
        if frame % 2 == 0:
            draw.point((panel[0], panel[1] - 3), fill=PAL["green"])

    if gate_over_belt:
        draw_gate_bed_and_moving_parts()
        draw_gate_components()
    else:
        draw_gate_components()
        draw_gate_bed_and_moving_parts()

def exit_gate_drawer(direction_name: str, frame: int):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_exit_gate(draw, x, y, w, h, direction_name=direction_name, frame=frame)

    return _draw


def draw_wall_segment_at_origin(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    facing: tuple[float, float],
    *,
    levels: int,
    center_xy: tuple[float, float] = (0.0, 0.0),
) -> None:
    run = normalize(facing)
    normal = normalize((-run[1], run[0]))
    height_z = 1.92 * levels
    length = 1.04
    thickness = 0.18
    center3 = (center_xy[0], center_xy[1], 0.04)

    shadow_box = oriented_box_3d(center3, normal, thickness + 0.10, length + 0.06, 0.01)
    shadow = [
        iso_model_point(origin, shadow_box["rl"]),
        iso_model_point(origin, shadow_box["fl"]),
        iso_model_point(origin, shadow_box["fr"]),
        iso_model_point(origin, shadow_box["rr"]),
    ]
    draw.polygon(shadow, fill=(0, 0, 0, 76))

    draw_oriented_box_3d(
        draw,
        origin,
        center3,
        normal,
        thickness,
        length,
        height_z,
        top=(109, 120, 118, 255),
        side_light=(88, 101, 103, 255),
        side_mid=(62, 75, 79, 255),
        side_dark=(35, 43, 47, 255),
    )

    face_side = 1

    def wall_pt(along: float, z: float, side_offset: float = face_side * thickness * 0.56) -> tuple[int, int]:
        point3 = (
            center_xy[0] + run[0] * along + normal[0] * side_offset,
            center_xy[1] + run[1] * along + normal[1] * side_offset,
            z,
        )
        return iso_model_point(origin, point3)

    for along in [-0.34, 0.0, 0.34]:
        draw.line([wall_pt(along, 0.18), wall_pt(along, height_z - 0.12)], fill=(118, 132, 133, 170), width=1)
    z = 0.42
    while z < height_z - 0.12:
        draw.line([wall_pt(-0.48, z), wall_pt(0.48, z)], fill=(37, 49, 55, 205), width=1)
        z += 0.42

    draw.line([wall_pt(-0.50, 0.25), wall_pt(0.50, 0.25)], fill=PAL["safety_yellow"], width=2)
    draw.line([wall_pt(-0.50, height_z - 0.10), wall_pt(0.50, height_z - 0.10)], fill=(152, 167, 164, 185), width=1)
    for along in [-0.42, 0.42]:
        base = wall_pt(along, 0.12)
        draw.rectangle((base[0] - 2, base[1] - 1, base[0] + 2, base[1] + 1), fill=(30, 34, 34, 255))
    if levels == 2:
        for along in [-0.22, 0.22]:
            lamp = wall_pt(along, 2.12)
            draw.rectangle((lamp[0] - 3, lamp[1] - 1, lamp[0] + 3, lamp[1] + 1), fill=PAL["cyan_dim"])


def draw_warehouse_wall_segment(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    *,
    direction_name: str,
    levels: int,
) -> None:
    origin = (round(x + w * 0.5), round(y + h - 26))
    facing = normalize(DIRECTION_VECTORS[direction_name])
    draw_wall_segment_at_origin(draw, origin, facing, levels=levels)


def warehouse_wall_segment_drawer(direction_name: str, levels: int):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_warehouse_wall_segment(draw, x, y, w, h, direction_name=direction_name, levels=levels)

    return _draw


def draw_warehouse_wall_corner(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, *, levels: int) -> None:
    origin = (round(x + w * 0.5), round(y + h - 28))
    for direction_name in ["nw", "ne"]:
        facing = normalize(DIRECTION_VECTORS[direction_name])
        center_xy = (facing[0] * 0.52, facing[1] * 0.52)
        draw_wall_segment_at_origin(draw, origin, facing, levels=levels, center_xy=center_xy)


def warehouse_wall_corner_drawer(levels: int):
    def _draw(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
        draw_warehouse_wall_corner(draw, x, y, w, h, levels=levels)

    return _draw


def build_sprites() -> list[Sprite]:
    sprites: list[Sprite] = []
    for index in range(8):
        sprites.append(
            Sprite(
                f"floor_concrete_{index + 1:02d}",
                64,
                48,
                "1x1 tile",
                (32, 38),
                make_floor_variant(index),
                "FINAL warm gray polished concrete floor variant with rivets, scratches, and tire marks.",
            )
        )
    sprites.extend(
        [
            Sprite("led_edge_pick_orange", 64, 48, "transparent 1x1 tile edge overlay", (32, 38), make_led_edge_overlay(PAL["amber_light"]), "Orange tile-edge highlight for selected rack picking zones only."),
            Sprite("led_edge_delivery_green", 64, 48, "transparent 1x1 tile edge overlay", (32, 38), make_led_edge_overlay(PAL["green"]), "Green permanent tile-edge highlight for delivery/truck drop-off zones."),
            Sprite("led_edge_robot_route_cyan", 64, 48, "transparent 1x1 tile edge overlay", (32, 38), make_led_edge_overlay(PAL["cyan"]), "Cyan tile-edge highlight for selected robot current tile and next navigation target."),
            Sprite("led_edge_congestion_red", 64, 48, "transparent 1x1 tile edge overlay", (32, 38), make_led_edge_overlay((230, 73, 38, 255)), "Red temporary tile-edge highlight for active congestion zones."),
            Sprite("depot_zone_2x2", 144, 112, "2x2 tiles", (72, 82), draw_depot_zone, "Idle robot parking zone with four parking pads."),
            Sprite("robot_dog_base_n", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("n"), "High-res base AEGIS dog, north/back facing, no basket, no arm."),
            Sprite("robot_dog_base_ne", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("ne"), "High-res base AEGIS dog, north-east facing, no basket, no arm."),
            Sprite("robot_dog_base_e", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("e"), "High-res base AEGIS dog, east/right facing, no basket, no arm."),
            Sprite("robot_dog_base_se", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("se"), "High-res base AEGIS dog, south-east facing, no basket, no arm."),
            Sprite("robot_dog_base_s", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("s"), "High-res base AEGIS dog, south/front facing, no basket, no arm."),
            Sprite("robot_dog_base_sw", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("sw"), "High-res base AEGIS dog, south-west facing, no basket, no arm."),
            Sprite("robot_dog_base_w", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("w"), "High-res base AEGIS dog, west/left facing, no basket, no arm."),
            Sprite("robot_dog_base_nw", 64, 64, "base dog 8-dir", (32, 52), base_robot_drawer("nw"), "High-res base AEGIS dog, north-west facing, no basket, no arm."),
            *[
                Sprite(
                    f"robot_dog_carry_{cargo_type}_{direction_name}",
                    64,
                    64,
                    "cargo dog 8-dir",
                    (32, 52),
                    base_robot_drawer(direction_name, cargo_type=cargo_type),
                    (
                        f"High-res AEGIS dog carrying {DOG_CARGO_TYPES[cargo_type]['label']}, "
                        f"{direction_name.upper()} direction, no basket, no arm; loaded stance adjusts by cargo weight."
                    ),
                )
                for cargo_type in ["cardboard", "wood", "metal"]
                for direction_name in ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
            ],
            *[
                Sprite(
                    f"pallet_rack_1x{length_tiles}_{direction_name}_{material}_{fill_state}",
                    source_w,
                    source_h,
                    f"1x{length_tiles} tiles",
                    anchor,
                    rack3d_drawer(length_tiles, 2, direction_name, material, fill_state),
                    (
                        f"High-res 2.5D pallet rack, 1x{length_tiles}, {direction_name.upper()} direction, "
                        f"{RACK_MATERIALS[material]['label']}, {RACK_FILL_STATES[fill_state]}."
                    ),
                )
                for length_tiles, source_w, source_h, anchor in [
                    (2, 192, 176, (96, 146)),
                    (3, 256, 192, (128, 160)),
                ]
                for direction_name in ["ne", "se", "sw", "nw"]
                for material in ["cardboard", "wood", "metal"]
                for fill_state in ["full", "half", "almost_none", "empty"]
            ],
            *[
                Sprite(
                    f"computer_terminal_1x1_{direction_name}_frame_{frame:02d}",
                    128,
                    128,
                    "1x1 tile",
                    (64, 100),
                    computer_terminal_directional_drawer(direction_name, frame),
                    (
                        f"Animated dark isometric Macintosh-inspired warehouse order server, "
                        f"{direction_name.upper()} orientation, RGB LED/status frame {frame:02d}, no keyboard or mouse."
                    ),
                )
                for direction_name in ["e", "s", "w", "n"]
                for frame in range(4)
            ],
            *[
                Sprite(
                    f"exit_gate_conveyor_3x1_{direction_name}_frame_{frame:02d}",
                    256,
                    192,
                    "3x1 tiles",
                    (128, 146),
                    exit_gate_drawer(direction_name, frame),
                    (
                        f"Animated {direction_name.upper()} roll-up exit gate with moving conveyor belt, "
                        f"parcel motion, and sectional door slats, frame {frame:02d}."
                    ),
                )
                for direction_name in ["e", "s", "w", "n"]
                for frame in range(4)
            ],
            *[
                Sprite(
                    f"warehouse_wall_segment_{direction_name}_h{height_m}m",
                    160 if levels == 1 else 192,
                    176 if levels == 1 else 264,
                    "1x1 rear wall edge",
                    ((160 if levels == 1 else 192) // 2, (176 if levels == 1 else 264) - 26),
                    warehouse_wall_segment_drawer(direction_name, levels),
                    (
                        f"Rear warehouse wall segment, {direction_name.upper()} back-side orientation, "
                        f"approx {height_m}m tall if one tile is 1.5m."
                    ),
                )
                for direction_name in ["ne", "nw"]
                for levels, height_m in [(1, 3), (2, 6)]
            ],
            *[
                Sprite(
                    f"warehouse_wall_corner_back_h{height_m}m",
                    192 if levels == 1 else 256,
                    192 if levels == 1 else 288,
                    "rear wall corner",
                    ((192 if levels == 1 else 256) // 2, (192 if levels == 1 else 288) - 28),
                    warehouse_wall_corner_drawer(levels),
                    f"Back warehouse wall corner joining NE and NW wall runs, approx {height_m}m tall.",
                )
                for levels, height_m in [(1, 3), (2, 6)]
            ],
        ]
    )
    return sprites


def layout_sprites(sprites: list[Sprite]) -> tuple[int, int]:
    x = PAD
    y = PAD
    row_h = 0
    for sprite in sprites:
        sw = final_w(sprite)
        sh = final_h(sprite)
        if x + sw + PAD > SHEET_W:
            x = PAD
            y += row_h + PAD
            row_h = 0
        sprite.x = x
        sprite.y = y
        x += sw + PAD
        row_h = max(row_h, sh)
    return SHEET_W, y + row_h + PAD


def make_contact_sheet(sheet: Image.Image, sprites: list[Sprite], out_dir: Path) -> Image.Image:
    font = ImageFont.load_default()
    card_w = 430
    card_h = 430
    card_gap = 14
    columns = 2
    rows = (len(sprites) + columns - 1) // columns
    contact = Image.new(
        "RGBA",
        (columns * card_w + (columns + 1) * card_gap, rows * card_h + (rows + 1) * card_gap),
        (8, 15, 22, 255),
    )
    draw = ImageDraw.Draw(contact)
    for index, sprite in enumerate(sprites):
        col = index % columns
        row = index // columns
        cx = card_gap + col * (card_w + card_gap)
        cy = card_gap + row * (card_h + card_gap)
        draw.rectangle((cx, cy, cx + card_w, cy + card_h), fill=(13, 25, 34, 255), outline=(24, 224, 230, 120), width=1)
        sw = final_w(sprite)
        sh = final_h(sprite)
        ax0, ay0 = final_anchor(sprite)
        full_crop = sheet.crop((sprite.x, sprite.y, sprite.x + sw, sprite.y + sh))
        bbox = full_crop.getbbox() or (0, 0, sw, sh)
        left = max(0, bbox[0] - 4)
        top = max(0, bbox[1] - 4)
        right = min(sw, bbox[2] + 4)
        bottom = min(sh, bbox[3] + 4)
        crop = full_crop.crop((left, top, right, bottom))
        crop_w, crop_h = crop.size
        max_scale_w = max(1, (card_w - 36) // crop_w)
        max_scale_h = max(1, (card_h - 78) // crop_h)
        scale = min(4, max_scale_w, max_scale_h)
        scaled = crop.resize((crop_w * scale, crop_h * scale), Image.Resampling.NEAREST)
        px = cx + (card_w - scaled.width) // 2
        py = cy + 16
        contact.alpha_composite(scaled, (px, py))
        if not sprite.name.startswith("led_edge_"):
            ax = px + (ax0 - left) * scale
            ay = py + (ay0 - top) * scale
            draw.line([(ax - 7, ay), (ax + 7, ay)], fill=PAL["yellow"], width=1)
            draw.line([(ax, ay - 7), (ax, ay + 7)], fill=PAL["yellow"], width=1)
        draw.text((cx + 10, cy + card_h - 46), sprite.name, fill=(234, 246, 248, 255), font=font)
        draw.text((cx + 10, cy + card_h - 28), sprite.footprint, fill=(128, 166, 178, 255), font=font)
    return contact


def sprite_crop_from_sheet(sheet: Image.Image, sprite: Sprite) -> Image.Image:
    sw = final_w(sprite)
    sh = final_h(sprite)
    full_crop = sheet.crop((sprite.x, sprite.y, sprite.x + sw, sprite.y + sh))
    bbox = full_crop.getbbox() or (0, 0, sw, sh)
    left = max(0, bbox[0] - 6)
    top = max(0, bbox[1] - 6)
    right = min(sw, bbox[2] + 6)
    bottom = min(sh, bbox[3] + 6)
    return full_crop.crop((left, top, right, bottom))


def make_rack_state_matrix(sheet: Image.Image, sprites: list[Sprite]) -> Image.Image:
    font = ImageFont.load_default()
    by_name = {sprite.name: sprite for sprite in sprites}
    materials = ["cardboard", "wood", "metal"]
    states = ["full", "half", "almost_none", "empty"]
    sizes = [2, 3]
    cell_w = 210
    cell_h = 184
    left_w = 96
    top_h = 40
    section_gap = 30
    width = left_w + len(states) * cell_w + 24
    height = top_h + len(sizes) * (len(materials) * cell_h + section_gap) + 20
    preview = Image.new("RGBA", (width, height), (8, 15, 22, 255))
    draw = ImageDraw.Draw(preview)

    for col, state in enumerate(states):
        x = left_w + col * cell_w
        draw.text((x + 8, 14), state, fill=(174, 222, 226, 255), font=font)

    y = top_h
    for size in sizes:
        draw.text((14, y + 6), f"1x{size} / NE", fill=(239, 167, 62, 255), font=font)
        y += 22
        for row, material in enumerate(materials):
            row_y = y + row * cell_h
            draw.text((14, row_y + 72), material, fill=(224, 232, 226, 255), font=font)
            for col, state in enumerate(states):
                cell_x = left_w + col * cell_w
                draw.rectangle(
                    (cell_x, row_y, cell_x + cell_w - 10, row_y + cell_h - 10),
                    fill=(13, 25, 34, 255),
                    outline=(24, 224, 230, 110),
                    width=1,
                )
                name = f"pallet_rack_1x{size}_ne_{material}_{state}"
                crop = sprite_crop_from_sheet(sheet, by_name[name])
                max_w = cell_w - 24
                max_h = cell_h - 42
                scale = min(max_w / crop.width, max_h / crop.height)
                scaled = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.NEAREST)
                px = cell_x + (cell_w - 10 - scaled.width) // 2
                py = row_y + 10
                preview.alpha_composite(scaled, (px, py))
                draw.text((cell_x + 8, row_y + cell_h - 30), name.replace("pallet_rack_", ""), fill=(128, 166, 178, 255), font=font)
        y += len(materials) * cell_h + section_gap
    return preview


def make_robot_cargo_matrix(sheet: Image.Image, sprites: list[Sprite]) -> Image.Image:
    font = ImageFont.load_default()
    by_name = {sprite.name: sprite for sprite in sprites}
    directions = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
    cargo_rows = [
        ("base", "base", "robot_dog_base_{direction}"),
        ("cardboard", "light", "robot_dog_carry_cardboard_{direction}"),
        ("wood", "medium", "robot_dog_carry_wood_{direction}"),
        ("metal", "heavy", "robot_dog_carry_metal_{direction}"),
    ]
    cell_w = 138
    cell_h = 148
    left_w = 92
    top_h = 38
    width = left_w + len(directions) * cell_w + 22
    height = top_h + len(cargo_rows) * cell_h + 24
    preview = Image.new("RGBA", (width, height), (8, 15, 22, 255))
    draw = ImageDraw.Draw(preview)

    for col, direction in enumerate(directions):
        draw.text((left_w + col * cell_w + 12, 14), direction.upper(), fill=(174, 222, 226, 255), font=font)

    for row, (cargo_key, weight_label, name_pattern) in enumerate(cargo_rows):
        row_y = top_h + row * cell_h
        draw.text((14, row_y + 54), cargo_key, fill=(224, 232, 226, 255), font=font)
        draw.text((14, row_y + 72), weight_label, fill=(128, 166, 178, 255), font=font)
        for col, direction in enumerate(directions):
            cell_x = left_w + col * cell_w
            draw.rectangle(
                (cell_x, row_y, cell_x + cell_w - 8, row_y + cell_h - 8),
                fill=(13, 25, 34, 255),
                outline=(24, 224, 230, 110),
                width=1,
            )
            name = name_pattern.format(direction=direction)
            crop = sprite_crop_from_sheet(sheet, by_name[name])
            max_w = cell_w - 22
            max_h = cell_h - 34
            scale = min(max_w / crop.width, max_h / crop.height)
            scaled = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.NEAREST)
            px = cell_x + (cell_w - 8 - scaled.width) // 2
            py = row_y + 8
            preview.alpha_composite(scaled, (px, py))
            draw.text((cell_x + 8, row_y + cell_h - 27), name.replace("robot_dog_", ""), fill=(128, 166, 178, 255), font=font)
    return preview


def make_visual_animation_matrix(sheet: Image.Image, sprites: list[Sprite]) -> Image.Image:
    font = ImageFont.load_default()
    by_name = {sprite.name: sprite for sprite in sprites}
    frames = range(4)
    rows = [
        *(
            (
                f"server {direction.upper()}",
                "isometric server",
                f"computer_terminal_1x1_{direction}_frame_{{frame:02d}}",
            )
            for direction in ["e", "s", "w", "n"]
        ),
        *(
            (
                f"exit {direction.upper()}",
                "belt/gate",
                f"exit_gate_conveyor_3x1_{direction}_frame_{{frame:02d}}",
            )
            for direction in ["e", "s", "w", "n"]
        ),
    ]
    cell_w = 238
    cell_h = 184
    left_w = 96
    top_h = 40
    width = left_w + len(frames) * cell_w + 24
    height = top_h + len(rows) * cell_h + 22
    preview = Image.new("RGBA", (width, height), (8, 15, 22, 255))
    draw = ImageDraw.Draw(preview)

    for frame in frames:
        draw.text((left_w + frame * cell_w + 10, 14), f"FRAME {frame:02d}", fill=(174, 222, 226, 255), font=font)

    for row_index, (label, sublabel, name_pattern) in enumerate(rows):
        row_y = top_h + row_index * cell_h
        draw.text((14, row_y + 68), label, fill=(224, 232, 226, 255), font=font)
        draw.text((14, row_y + 86), sublabel, fill=(128, 166, 178, 255), font=font)
        for frame in frames:
            cell_x = left_w + frame * cell_w
            draw.rectangle(
                (cell_x, row_y, cell_x + cell_w - 8, row_y + cell_h - 8),
                fill=(13, 25, 34, 255),
                outline=(24, 224, 230, 110),
                width=1,
            )
            name = name_pattern.format(frame=frame)
            crop = sprite_crop_from_sheet(sheet, by_name[name])
            max_w = cell_w - 22
            max_h = cell_h - 36
            scale = min(max_w / crop.width, max_h / crop.height)
            scaled = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.NEAREST)
            px = cell_x + (cell_w - 8 - scaled.width) // 2
            py = row_y + 8
            preview.alpha_composite(scaled, (px, py))
            draw.text((cell_x + 8, row_y + cell_h - 28), name.replace("exit_gate_conveyor_3x1_", "").replace("computer_terminal_1x1_", ""), fill=(128, 166, 178, 255), font=font)
    return preview


def make_preview_sheet(sheet: Image.Image, sprites: list[Sprite], sheet_w: int, sheet_h: int) -> Image.Image:
    font = ImageFont.load_default()
    preview = Image.new("RGBA", (sheet_w, sheet_h + LABEL_H * 2), (11, 19, 27, 255))
    draw = ImageDraw.Draw(preview)
    for gx in range(0, sheet_w, 16):
        draw.line([(gx, 0), (gx, preview.height)], fill=(18, 33, 43, 255), width=1)
    for gy in range(0, preview.height, 16):
        draw.line([(0, gy), (sheet_w, gy)], fill=(18, 33, 43, 255), width=1)
    preview.alpha_composite(sheet, (0, 0))
    for sprite in sprites:
        sw = final_w(sprite)
        sh = final_h(sprite)
        draw.rectangle((sprite.x, sprite.y, sprite.x + sw - 1, sprite.y + sh - 1), outline=(24, 224, 230, 160), width=1)
        ax, ay = final_anchor(sprite)
        draw.line([(sprite.x + ax - 3, sprite.y + ay), (sprite.x + ax + 3, sprite.y + ay)], fill=PAL["yellow"], width=1)
        draw.line([(sprite.x + ax, sprite.y + ay - 3), (sprite.x + ax, sprite.y + ay + 3)], fill=PAL["yellow"], width=1)
        draw.text((sprite.x, sprite.y + sh + 1), sprite.name, fill=(222, 242, 244, 255), font=font)
    return preview


def make_robot_on_tile_sheet(sheet: Image.Image, sprites: list[Sprite]) -> Image.Image:
    font = ImageFont.load_default()
    floor = next(s for s in sprites if s.name == "floor_concrete_03")
    robots = [s for s in sprites if s.name.startswith("robot_dog_base_") or s.name.startswith("robot_dog_carry_")]
    card_w = 560
    card_h = 470
    card_gap = 14
    columns = 2
    rows = (len(robots) + columns - 1) // columns
    contact = Image.new(
        "RGBA",
        (columns * card_w + (columns + 1) * card_gap, rows * card_h + (rows + 1) * card_gap),
        (8, 15, 22, 255),
    )
    draw = ImageDraw.Draw(contact)
    fw = final_w(floor)
    fh = final_h(floor)
    floor_ax, floor_ay = final_anchor(floor)
    floor_img = sheet.crop((floor.x, floor.y, floor.x + fw, floor.y + fh))

    for index, robot in enumerate(robots):
        col = index % columns
        row = index // columns
        cx = card_gap + col * (card_w + card_gap)
        cy = card_gap + row * (card_h + card_gap)
        draw.rectangle((cx, cy, cx + card_w, cy + card_h), fill=(13, 25, 34, 255), outline=(24, 224, 230, 120), width=1)

        rw = final_w(robot)
        rh = final_h(robot)
        robot_ax, robot_ay = final_anchor(robot)
        robot_img = sheet.crop((robot.x, robot.y, robot.x + rw, robot.y + rh))
        scene = Image.new("RGBA", (240, 192), (0, 0, 0, 0))
        floor_anchor = (120, 140)
        tile_center = (120, 108)
        scene.alpha_composite(floor_img, (floor_anchor[0] - floor_ax, floor_anchor[1] - floor_ay))
        scene.alpha_composite(robot_img, (tile_center[0] - robot_ax, tile_center[1] - robot_ay))
        max_scale_w = max(1, (card_w - 36) // scene.width)
        max_scale_h = max(1, (card_h - 78) // scene.height)
        scale = min(2, max_scale_w, max_scale_h)
        scaled = scene.resize((scene.width * scale, scene.height * scale), Image.Resampling.NEAREST)
        px = cx + (card_w - scaled.width) // 2
        py = cy + 18
        contact.alpha_composite(scaled, (px, py))
        ax = px + tile_center[0] * scale
        ay = py + tile_center[1] * scale
        draw.line([(ax - 7, ay), (ax + 7, ay)], fill=PAL["yellow"], width=1)
        draw.line([(ax, ay - 7), (ax, ay + 7)], fill=PAL["yellow"], width=1)
        draw.text((cx + 10, cy + card_h - 40), robot.name, fill=(234, 246, 248, 255), font=font)
        draw.text((cx + 10, cy + card_h - 22), "on final floor tile", fill=(128, 166, 178, 255), font=font)
    return contact


def render_sheet(sprites: list[Sprite]) -> tuple[Image.Image, int, int]:
    sheet_w, sheet_h = layout_sprites(sprites)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for sprite in sprites:
        sheet.alpha_composite(render_sprite(sprite), (sprite.x, sprite.y))
    return sheet, sheet_w, sheet_h


def manifest_for(category: str, sprites: list[Sprite]) -> dict:
    manifest = {
        "version": VERSION,
        "category": category,
        "sprite_scale": SPRITE_SCALE,
        "base_tile": {
            "source_sprite": "128x128 final PNG cell for floor tiles with transparent padding",
            "visible_diamond": "128x64",
            "logical_model_tile": "64x48 art inside a 64x64 square canvas before nearest-neighbor 2x export",
            "robot_png": "128x128 final PNG with transparent padding",
        },
        "sprites": [
            {
                "name": s.name,
                "rect": {"x": s.x, "y": s.y, "w": final_w(s), "h": final_h(s)},
                "art_size": {"w": s.w * SPRITE_SCALE, "h": s.h * SPRITE_SCALE},
                "anchor": {"x": final_anchor(s)[0], "y": final_anchor(s)[1]},
                "footprint": s.footprint,
                "note": s.note,
            }
            for s in sprites
        ],
    }
    if category == "rack":
        manifest["rack_materials"] = {key: value["label"] for key, value in RACK_MATERIALS.items()}
        manifest["rack_fill_states"] = RACK_FILL_STATES
    if category == "LED":
        manifest["led_edge_meanings"] = LED_EDGE_MEANINGS
    if category == "robot_dog":
        manifest["robot_directions"] = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
        manifest["robot_cargo_types"] = {
            key: {"label": value["label"], "load": value["load"]}
            for key, value in DOG_CARGO_TYPES.items()
        }
        manifest["robot_sprite_groups"] = {
            "base": "robot_dog_base_{direction}",
            "carry": "robot_dog_carry_{cardboard|wood|metal}_{direction}",
        }
    if category == "visual":
        manifest["visual_animation_groups"] = {
            "computer_terminal_1x1": {
                "directions": ["e", "s", "w", "n"],
                "frames": 4,
                "pattern": "computer_terminal_1x1_{e|s|w|n}_frame_{00..03}",
                "meaning": "Macintosh-inspired order server CRT/status blink.",
            },
            "exit_gate_conveyor_3x1": {
                "directions": ["e", "s", "w", "n"],
                "frames": 4,
                "pattern": "exit_gate_conveyor_3x1_{e|s|w|n}_frame_{00..03}",
                "meaning": "Cardinal east/south/west/north roll-up exit gate with moving conveyor belt and parcels.",
            },
        }
        manifest["visual_wall_modules"] = {
            "tile_scale": "1 tile is treated as roughly 1.5m x 1.5m in-world.",
            "heights": {"h3m": "one wall level, approx 3m", "h6m": "two wall levels, approx 6m"},
            "segments": "warehouse_wall_segment_{ne|nw}_h{3|6}m",
            "corners": "warehouse_wall_corner_back_h{3|6}m",
            "rendering_rule": "Use only on the rear two warehouse sides; omit or hide front walls like a Sims-style cutaway.",
        }
    return manifest


def write_category(
    category: str,
    directory: Path,
    sprites: list[Sprite],
    *,
    contact_name: str,
) -> tuple[Image.Image, list[Sprite]]:
    directory.mkdir(exist_ok=True)
    sheet, _sheet_w, _sheet_h = render_sheet(sprites)
    sheet.save(directory / f"{category}_sprite_sheet_v{VERSION}.png")
    make_contact_sheet(sheet, sprites, directory).save(directory / contact_name)
    (directory / f"{category}_manifest_v{VERSION}.json").write_text(
        json.dumps(manifest_for(category, sprites), indent=2),
        encoding="utf-8",
    )
    return sheet, sprites


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    floor_dir = out_dir / "floor"
    led_dir = out_dir / "LED"
    robot_dir = out_dir / "robot_dog"
    rack_dir = out_dir / "rack"
    visual_dir = out_dir / "visual"
    for directory in [floor_dir, led_dir, robot_dir, rack_dir, visual_dir]:
        directory.mkdir(exist_ok=True)

    sprites = build_sprites()
    floor_sprites = [s for s in sprites if s.name.startswith("floor_")]
    led_sprites = [s for s in sprites if s.name.startswith("led_edge_")]
    robot_sprites = [s for s in sprites if s.name.startswith("robot_dog_base_") or s.name.startswith("robot_dog_carry_")]
    rack_sprites = [s for s in sprites if s.name.startswith("pallet_rack_")]
    visual_sprites = [
        s
        for s in sprites
        if s not in floor_sprites + led_sprites + robot_sprites + rack_sprites
    ]

    floor_sheet, _ = write_category("floor", floor_dir, floor_sprites, contact_name=f"floor_contact_v{VERSION}.png")
    write_category("LED", led_dir, led_sprites, contact_name=f"LED_contact_v{VERSION}.png")
    robot_sheet, _ = write_category(
        "robot_dog",
        robot_dir,
        robot_sprites,
        contact_name=f"robot_dog_contact_v{VERSION}.png",
    )
    make_robot_cargo_matrix(robot_sheet, robot_sprites).save(robot_dir / f"robot_dog_cargo_matrix_v{VERSION}.png")
    rack_sheet, _ = write_category("rack", rack_dir, rack_sprites, contact_name=f"pallet_rack_contact_v{VERSION}.png")
    make_rack_state_matrix(rack_sheet, rack_sprites).save(rack_dir / f"pallet_rack_state_matrix_v{VERSION}.png")
    visual_sheet, _ = write_category("visual", visual_dir, visual_sprites, contact_name=f"visual_contact_v{VERSION}.png")
    make_visual_animation_matrix(visual_sheet, visual_sprites).save(visual_dir / f"visual_animation_matrix_v{VERSION}.png")

    preview_sprites = floor_sprites + robot_sprites
    preview_sheet, _sheet_w, _sheet_h = render_sheet(preview_sprites)
    make_robot_on_tile_sheet(preview_sheet, preview_sprites).save(
        robot_dir / f"robot_dog_on_tile_contact_v{VERSION}.png"
    )


if __name__ == "__main__":
    main()

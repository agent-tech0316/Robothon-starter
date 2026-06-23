#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submissions" / "warehouse_quadbot_atomic_demos"
OUTPUTS = SUBMISSION / "outputs"
PHYSICS = OUTPUTS / "physics_evidence"
BUILD_DIR = OUTPUTS / "program_only_video_build"
DEMO_PATH = SUBMISSION / "demo.mp4"
MANIFEST_PATH = OUTPUTS / "program_only_demo_manifest.json"

SIZE = (1280, 720)
FPS = 24
CRF = "18"


def ffmpeg() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if draw.textbbox((0, 0), candidate, font=face)[2] <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def make_card(path: Path, title: str, body: str, kicker: str = "PROGRAM-ONLY DEMO") -> None:
    img = Image.new("RGB", SIZE, "#07121a")
    draw = ImageDraw.Draw(img)
    for y in range(SIZE[1]):
        shade = int(18 + y * 0.035)
        draw.line([(0, y), (SIZE[0], y)], fill=(7, shade, 26 + shade // 3))
    draw.rectangle((46, 46, SIZE[0] - 46, SIZE[1] - 46), outline="#1fe0e6", width=3)
    draw.rectangle((54, 54, SIZE[0] - 54, SIZE[1] - 54), outline="#354b5a", width=1)
    draw.text((78, 82), kicker, fill="#ffbf3d", font=font(26, True))
    draw.text((78, 142), title, fill="#f4fbff", font=font(56, True))
    y = 250
    for line in wrap(draw, body, font(31), 1080):
        draw.text((82, y), line, fill="#c9d8df", font=font(31))
        y += 45
    draw.text((82, SIZE[1] - 92), "Moving footage sources: Web runtime recording + MuJoCo renderer clips only.", fill="#80f0ff", font=font(24, True))
    img.save(path)


def make_image_card(path: Path, source: Path, title: str, body: str) -> None:
    base = Image.open(source).convert("RGB")
    base.thumbnail(SIZE, Image.Resampling.LANCZOS)
    img = Image.new("RGB", SIZE, "#07121a")
    offset = ((SIZE[0] - base.width) // 2, (SIZE[1] - base.height) // 2)
    img.paste(base, offset)
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, SIZE[0], 148), fill=(4, 9, 13, 214))
    draw.rectangle((0, SIZE[1] - 120, SIZE[0], SIZE[1]), fill=(4, 9, 13, 220))
    draw.text((42, 34), title, fill="#f4fbff", font=font(42, True))
    draw.text((44, SIZE[1] - 86), body, fill="#c9d8df", font=font(26))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(path)


def encode_image(image_path: Path, duration: float, out_path: Path) -> None:
    run([
        ffmpeg(), "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-t", f"{duration:.2f}",
        "-r", str(FPS),
        "-vf", f"fps={FPS},format=yuv420p",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", CRF,
        "-pix_fmt", "yuv420p",
        str(out_path),
    ])


def encode_video(source: Path, duration: float, out_path: Path) -> None:
    run([
        ffmpeg(), "-y",
        "-stream_loop", "8",
        "-i", str(source),
        "-t", f"{duration:.2f}",
        "-vf", f"scale={SIZE[0]}:{SIZE[1]}:force_original_aspect_ratio=decrease,pad={SIZE[0]}:{SIZE[1]}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", CRF,
        "-pix_fmt", "yuv420p",
        str(out_path),
    ])


def concat(segments: list[Path]) -> None:
    concat_file = BUILD_DIR / "concat.txt"
    concat_file.write_text("".join(f"file '{segment.resolve()}'\n" for segment in segments), encoding="utf-8")
    run([
        ffmpeg(), "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", CRF,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        str(DEMO_PATH),
    ])


def main() -> int:
    required_sources = [
        OUTPUTS / "runtime_live_decision_replay.mp4",
        SUBMISSION / "docs" / "screenshots" / "mission_control_program_only.png",
        PHYSICS / "fleet_physics_corridor.mp4",
        PHYSICS / "six_dof_grasp_sweep_metal.mp4",
        PHYSICS / "handoff_metal.mp4",
        PHYSICS / "effector_mix_lab.mp4",
        PHYSICS / "physics_evidence_contact_sheet.png",
    ]
    missing = [path for path in required_sources if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing program-only video source(s): " + ", ".join(str(path) for path in missing))

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    card_intro = BUILD_DIR / "card_intro.png"
    card_human = BUILD_DIR / "card_human.png"
    card_benchmark = BUILD_DIR / "card_benchmark.png"
    card_close = BUILD_DIR / "card_close.png"
    ui_card = BUILD_DIR / "ui_capture_card.png"
    contact_card = BUILD_DIR / "contact_sheet_card.png"

    make_card(
        card_intro,
        "Agentic Warehouse Quadbot Benchmark",
        "This replacement demo removes all AI-generated moving clips. It uses only real Web runtime footage, MuJoCo renderer output, generated benchmark data, and text overlays.",
    )
    make_image_card(
        ui_card,
        SUBMISSION / "docs" / "screenshots" / "mission_control_program_only.png",
        "Web Runtime: live warehouse state",
        "Current UI run loads high_humans runtime JSON, event replay, human-risk tiles, order pressure, and KPI panels.",
    )
    make_card(
        card_human,
        "Human-Intrusion Stressor",
        "High-load runtime: 10 stochastic people, 7 active at snapshot, 17 human-risk tiles, 147 hold ticks, 17 reroutes, 0 collisions, 0 lock overlaps.",
    )
    make_card(
        card_benchmark,
        "Benchmark Evidence",
        "30-robot heterogeneous stress extension: 54 six-hour scenarios, 9,720 robot-hours, 100% safety pass, +60.27% average planner uplift.",
    )
    make_image_card(
        contact_card,
        PHYSICS / "physics_evidence_contact_sheet.png",
        "MuJoCo evidence contact sheet",
        "Generated renderer output: contact traces, grasp sweeps, handoff, corridor physics, and heterogeneous tools.",
    )
    make_card(
        card_close,
        "Layered Validation",
        "Web runtime proves fleet planning, congestion recovery, and throughput. MuJoCo proves low-level physical contacts, payload handling, and robot interaction.",
        kicker="RUNNABLE SUBMISSION",
    )

    spec = [
        ("image", card_intro, 5.0, "Program-only title card", "generated text card from build_program_only_demo_video.py"),
        ("image", ui_card, 7.0, "Chrome capture of current UI runtime", "submissions/warehouse_quadbot_atomic_demos/docs/screenshots/mission_control_program_only.png"),
        ("video", OUTPUTS / "runtime_live_decision_replay.mp4", 18.0, "Web runtime recording", "submissions/warehouse_quadbot_atomic_demos/outputs/runtime_live_decision_replay.mp4"),
        ("image", card_human, 6.0, "Generated text card from runtime metrics", "generated text card from benchmark_metrics_high_humans.json"),
        ("image", card_benchmark, 6.0, "Generated text card from benchmark metrics", "generated text card from fleet_stress_benchmark_30robots.json"),
        ("video", PHYSICS / "fleet_physics_corridor.mp4", 8.0, "MuJoCo fleet corridor renderer clip", "submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/fleet_physics_corridor.mp4"),
        ("video", PHYSICS / "six_dof_grasp_sweep_metal.mp4", 8.0, "MuJoCo 6-DOF grasp renderer clip", "submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/six_dof_grasp_sweep_metal.mp4"),
        ("video", PHYSICS / "handoff_metal.mp4", 7.0, "MuJoCo two-robot handoff renderer clip", "submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/handoff_metal.mp4"),
        ("video", PHYSICS / "effector_mix_lab.mp4", 8.0, "MuJoCo heterogeneous end-effector renderer clip", "submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/effector_mix_lab.mp4"),
        ("image", contact_card, 7.0, "Generated MuJoCo contact sheet", "submissions/warehouse_quadbot_atomic_demos/outputs/physics_evidence/physics_evidence_contact_sheet.png"),
        ("image", card_close, 5.0, "Closing text card", "generated text card from build_program_only_demo_video.py"),
    ]

    segments: list[Path] = []
    manifest_segments = []
    for index, (kind, source, duration, description, manifest_source) in enumerate(spec, start=1):
        out = BUILD_DIR / f"segment_{index:02d}.mp4"
        if kind == "image":
            encode_image(source, duration, out)
        else:
            encode_video(source, duration, out)
        segments.append(out)
        manifest_segments.append({
            "index": index,
            "kind": kind,
            "source": manifest_source,
            "duration_s": duration,
            "description": description,
            "ai_generated_moving_footage": False,
        })

    concat(segments)
    manifest = {
        "demo_video": str(DEMO_PATH.relative_to(ROOT)),
        "duration_target_s": sum(item[2] for item in spec),
        "encoding": {"resolution": "1280x720", "fps": FPS, "crf": CRF, "audio": "none"},
        "policy": "All moving footage is real program output from Web runtime recording or MuJoCo renderer clips. Cards/text overlays are generated, but no AI-generated moving video is used.",
        "segments": manifest_segments,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    shutil.rmtree(BUILD_DIR)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

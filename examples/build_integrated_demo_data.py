#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from warehouse_runtime.config import load_yaml
from warehouse_runtime.simulator import RuntimeOptions, WarehouseRuntime


OUTPUT_DIR = ROOT / "submissions" / "warehouse_quadbot_atomic_demos" / "outputs"
LOAD_TICKS = {
    "low": 900,
    "medium": 900,
    "high": 900,
}


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_profile(load: str, ticks: int) -> dict[str, Path]:
    runtime = WarehouseRuntime(
        load_yaml(ROOT / "configs" / "runtime.yaml"),
        load_yaml(ROOT / "configs" / "scheduler_policy.yaml"),
        load_yaml(ROOT / "configs" / "mission_layout.yaml"),
        RuntimeOptions(
            load=load,
            planner_mode="local",
            speed=1,
            max_ticks=ticks,
            output_dir=str(OUTPUT_DIR),
            run_id=f"runtime_{load}_ui_demo",
        ),
    )
    runtime.run(ticks)
    snapshot = runtime.snapshot()
    metrics = runtime.metrics_report()

    snapshot_path = OUTPUT_DIR / f"runtime_snapshot_{load}.json"
    metrics_path = OUTPUT_DIR / f"benchmark_metrics_{load}.json"
    events_path = OUTPUT_DIR / f"runtime_events_{load}.jsonl"
    write_json(snapshot_path, snapshot)
    write_json(metrics_path, metrics)
    with events_path.open("w", encoding="utf-8") as handle:
        for event in runtime.events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    if load == "medium":
        write_json(OUTPUT_DIR / "runtime_snapshot.json", snapshot)
        write_json(OUTPUT_DIR / "benchmark_metrics.json", metrics)
        (OUTPUT_DIR / "runtime_events.jsonl").write_text(events_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "snapshot": snapshot_path,
        "metrics": metrics_path,
        "events": events_path,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        load: {key: str(path.relative_to(ROOT)) for key, path in build_profile(load, ticks).items()}
        for load, ticks in LOAD_TICKS.items()
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

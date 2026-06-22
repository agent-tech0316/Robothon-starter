from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_yaml
from .simulator import RuntimeOptions, WarehouseRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the warehouse order fulfillment runtime simulator.")
    parser.add_argument("--runtime", default="configs/runtime.yaml", help="Runtime config YAML path.")
    parser.add_argument("--scheduler", default="configs/scheduler_policy.yaml", help="Scheduler policy YAML path.")
    parser.add_argument("--layout", default="configs/mission_layout.yaml", help="Mission layout YAML path.")
    parser.add_argument("--load", choices=["low", "medium", "high"], default="medium", help="Order load profile.")
    parser.add_argument("--planner", choices=["local", "openai", "off"], default=None, help="Planner mode. Default comes from runtime config.")
    parser.add_argument("--speed", type=int, choices=[1, 10, 60], default=1, help="UI playback speed label stored in snapshot.")
    parser.add_argument("--ticks", type=int, default=None, help="Number of simulation ticks to run.")
    parser.add_argument("--output-dir", default=None, help="Directory for snapshot, metrics, and event log.")
    parser.add_argument("--run-id", default="runtime_demo", help="Run identifier for events and metrics.")
    parser.add_argument("--print-summary", action="store_true", help="Print metrics summary JSON to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime_config = load_yaml(args.runtime)
    scheduler_config = load_yaml(args.scheduler)
    layout_config = load_yaml(args.layout)
    planner = args.planner or runtime_config.get("planner", {}).get("default_mode", "local")
    options = RuntimeOptions(
        load=args.load,
        planner_mode=planner,
        speed=args.speed,
        max_ticks=args.ticks,
        output_dir=args.output_dir,
        run_id=args.run_id,
    )
    runtime = WarehouseRuntime(runtime_config, scheduler_config, layout_config, options)
    runtime.run(args.ticks)
    paths = runtime.write_outputs(args.output_dir)
    if args.print_summary:
        summary = runtime.metrics_report()
        summary["outputs"] = {key: str(path) for key, path in paths.items()}
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path

from warehouse_runtime.config import load_yaml
from warehouse_runtime.simulator import RuntimeOptions, WarehouseRuntime


def test_runtime_smoke_runs_and_writes_outputs(tmp_path: Path) -> None:
    runtime = WarehouseRuntime(
        load_yaml("configs/runtime.yaml"),
        load_yaml("configs/scheduler_policy.yaml"),
        load_yaml("configs/mission_layout.yaml"),
        RuntimeOptions(load="low", planner_mode="local", max_ticks=300, output_dir=str(tmp_path)),
    )
    runtime.run(300)
    paths = runtime.write_outputs(tmp_path)
    assert paths["snapshot"].exists()
    assert paths["metrics"].exists()
    assert paths["events"].exists()
    snapshot = runtime.snapshot()
    assert snapshot["robots"]
    assert snapshot["runtime"]["planner_mode"] == "local"
    assert "orders" in snapshot



def test_routes_never_enter_rack_or_blocked_tiles() -> None:
    runtime = WarehouseRuntime(
        load_yaml("configs/runtime.yaml"),
        load_yaml("configs/scheduler_policy.yaml"),
        load_yaml("configs/mission_layout.yaml"),
        RuntimeOptions(load="medium", planner_mode="local", max_ticks=900),
    )
    runtime.run(900)
    snapshot = runtime.snapshot()
    rack_tiles = set(snapshot["warehouse"]["rack_tiles"])
    blocked_tiles = set(snapshot["warehouse"]["blocked_tiles"])
    assert rack_tiles
    assert not runtime.route_violations()
    for robot in snapshot["robots"]:
        assert robot["tile_id"] not in rack_tiles
        assert robot["tile_id"] not in blocked_tiles
        for x, y in robot["route"]:
            tile_id = f"T_{int(x):02d}_{int(y):02d}"
            assert tile_id not in rack_tiles
            assert tile_id not in blocked_tiles


def test_routes_are_cardinal_and_robot_collisions_are_prevented() -> None:
    runtime = WarehouseRuntime(
        load_yaml("configs/runtime.yaml"),
        load_yaml("configs/scheduler_policy.yaml"),
        load_yaml("configs/mission_layout.yaml"),
        RuntimeOptions(load="medium", planner_mode="local", max_ticks=900),
    )
    runtime.run(900)
    snapshot = runtime.snapshot()

    assert not runtime.route_cardinality_violations()
    assert not runtime.collision_violations()
    assert not runtime.lock_overlap_violations()
    assert snapshot["runtime"]["route_cardinality_violations"] == 0
    assert snapshot["runtime"]["collision_violations"] == 0
    assert snapshot["runtime"]["lock_overlap_violations"] == 0

    occupied_tiles = snapshot["movement_locks"]["occupied_tiles"]
    assert len(occupied_tiles) == len(snapshot["robots"])
    assert len({entry["tile_id"] for entry in occupied_tiles}) == len(occupied_tiles)
    for robot in snapshot["robots"]:
        assert robot["movement_model"] == "four_direction_grid"
        assert robot["route_closed"] is False
        assert robot["route_cardinal"] is True
        points = robot["route"]
        for a, b in zip(points, points[1:]):
            assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

def test_local_planner_route_window_improves_medium_throughput() -> None:
    off_runtime = WarehouseRuntime(
        load_yaml("configs/runtime.yaml"),
        load_yaml("configs/scheduler_policy.yaml"),
        load_yaml("configs/mission_layout.yaml"),
        RuntimeOptions(load="medium", planner_mode="off", max_ticks=900),
    )
    local_runtime = WarehouseRuntime(
        load_yaml("configs/runtime.yaml"),
        load_yaml("configs/scheduler_policy.yaml"),
        load_yaml("configs/mission_layout.yaml"),
        RuntimeOptions(load="medium", planner_mode="local", max_ticks=900),
    )

    off_runtime.run(900)
    local_runtime.run(900)
    off_metrics = off_runtime.metrics_report()
    local_metrics = local_runtime.metrics_report()

    assert local_metrics["completed_orders"] > off_metrics["completed_orders"]
    assert local_metrics["throughput_orders_per_simulated_hour"] > off_metrics["throughput_orders_per_simulated_hour"]
    assert local_metrics["average_completion_ticks"] < off_metrics["average_completion_ticks"]
    assert local_metrics["route_blocked_tile_violations"] == 0
    assert local_metrics["route_cardinality_violations"] == 0
    assert local_metrics["collision_violations"] == 0
    assert local_metrics["lock_overlap_violations"] == 0


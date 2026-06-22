from __future__ import annotations

import json
import math
import random
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .ai_planner import PlannerDecision, local_planner_decision, openai_planner_decision


DIRECTIONS: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}

PRIORITY_VALUES = {
    "low": 25,
    "normal": 50,
    "high": 75,
    "urgent": 95,
}

DEADLINE_SECONDS = {
    "low": 3600,
    "normal": 2400,
    "high": 1500,
    "urgent": 900,
}


@dataclass
class RuntimeOptions:
    load: str = "medium"
    planner_mode: str = "local"
    speed: int = 1
    max_ticks: int | None = None
    output_dir: str | None = None
    run_id: str = "runtime_demo"


@dataclass
class Tile:
    tile_id: str
    x: int
    y: int
    traversable: bool = True
    zone_id: str | None = None


@dataclass
class Rack:
    rack_id: str
    sku_id: str
    pick_tile_id: str
    storage_tile_id: str
    quantity: int = 1_000_000
    footprint_tiles: list[str] = field(default_factory=list)


@dataclass
class RackModule:
    module_id: str
    footprint_tiles: list[str]
    pick_tiles: list[str] = field(default_factory=list)
    x: int = 0
    y: int = 0
    w: int = 1
    d: int = 1
    length: int = 1
    direction: str = "ne"
    material: str = "cardboard"
    fill: str = "full"


@dataclass
class Conveyor:
    conveyor_id: str
    unload_tile_id: str
    direction: str = "E"
    capacity_packages: int = 4


@dataclass
class Order:
    order_id: str
    order_sequence: int
    sku_id: str
    weight: float
    difficulty: int
    priority_label: str
    priority: int
    creation_tick: int
    deadline_tick: int
    status: str = "pending_inventory"
    assigned_robot_id: str | None = None
    rack_id: str | None = None
    pick_tile_id: str | None = None
    conveyor_id: str | None = None
    unload_tile_id: str | None = None
    inventory_reserved_tick: int | None = None
    assignment_tick: int | None = None
    picked_tick: int | None = None
    unloaded_tick: int | None = None
    completion_tick: int | None = None
    failure_reason: str | None = None


@dataclass
class Robot:
    robot_id: str
    robot_type_id: str
    current_tile_id: str
    max_payload_weight: float
    handling_skill_level: int
    base_move_ticks_per_tile: int = 2
    load_speed_penalty: float = 0.08
    status: str = "ready"
    assigned_order_id: str | None = None
    carried_order_id: str | None = None
    carried_sku_id: str | None = None
    carried_weight: float = 0.0
    target_tile_id: str | None = None
    next_tile_id: str | None = None
    route: list[str] = field(default_factory=list)
    heading: str | None = None
    busy_until_tick: int = 0
    available_at_tick: int = 0
    wait_ticks: int = 0
    lock_denials: int = 0
    busy_ticks: int = 0
    role: str = "runner"
    battery_pct: float = 96.0
    recovery_goal_tile_id: str | None = None
    last_replan_tick: int = -999999


@dataclass
class RuntimeMetrics:
    created_orders: int = 0
    completed_orders: int = 0
    failed_orders: int = 0
    replan_count: int = 0
    deadlock_count: int = 0
    deadlock_recovery_ticks: int = 0
    lock_wait_ticks: int = 0
    planner_checks: int = 0
    ai_planner_calls: int = 0
    local_planner_fallbacks: int = 0


class WarehouseRuntime:
    def __init__(
        self,
        runtime_config: dict[str, Any],
        scheduler_config: dict[str, Any],
        layout_config: dict[str, Any],
        options: RuntimeOptions | None = None,
    ) -> None:
        self.runtime_config = runtime_config
        self.scheduler_config = scheduler_config
        self.layout_config = layout_config
        self.options = options or RuntimeOptions()
        self.random = random.Random(int(runtime_config.get("runtime", {}).get("random_seed", 20260620)))
        self.tick_seconds = float(
            runtime_config.get("simulation", {}).get(
                "tick_duration_s",
                runtime_config.get("runtime", {}).get("tick", {}).get("duration_ms", 1000) / 1000,
            )
        )
        if self.tick_seconds <= 0:
            raise ValueError("tick duration must be positive")
        self.max_ticks = int(
            self.options.max_ticks
            or runtime_config.get("runtime", {}).get("tick", {}).get("max_ticks", 7200)
        )
        self.ai_interval_s = int(runtime_config.get("planner", {}).get("ai_planning_interval_s", 600))
        self.planner_interval_ticks = max(1, int(round(self.ai_interval_s / self.tick_seconds)))
        self.lock_replan_threshold = int(
            scheduler_config.get("routing", {}).get("replan", {}).get("after_lock_denials", 3)
        )
        self.wait_replan_threshold = int(
            scheduler_config.get("routing", {}).get("replan", {}).get("after_wait_ticks", 8)
        )
        self.deadlock_confirm_ticks = int(
            scheduler_config.get("deadlock_recovery", {}).get("confirm_after_wait_ticks", 20)
        )

        self.tick = 0
        self.metrics = RuntimeMetrics()
        self.events: list[dict[str, Any]] = []
        self.recent_messages: deque[str] = deque(maxlen=24)
        self.orders: dict[str, Order] = {}
        self.order_sequence = 0
        self.robots: dict[str, Robot] = {}
        self.tiles: dict[str, Tile] = {}
        self.width_tiles = 0
        self.height_tiles = 0
        self.racks: list[Rack] = []
        self.rack_modules: list[RackModule] = []
        self.racks_by_sku: dict[str, list[Rack]] = {}
        self.conveyors: list[Conveyor] = []
        self.occupancy: dict[str, str] = {}
        self.blocked_tiles: set[str] = set()
        self.rack_tiles: set[str] = set()
        self.buffer_tiles: list[str] = []
        self.depot_tiles: list[str] = []
        self.service_tiles: set[str] = set()
        self.wait_for: dict[str, str] = {}
        self.deadlock_cooldowns: dict[str, int] = {}
        self.last_planner_decision: PlannerDecision = local_planner_decision({"load": self.options.load})
        self.active_handoff_mode = False
        self.last_lock_requests: list[dict[str, Any]] = []
        self.last_granted_moves: list[dict[str, Any]] = []
        self.last_denied_moves: list[dict[str, Any]] = []

        self._build_world()
        self._emit("runtime.started", f"Runtime initialized with {self.options.load} load and {len(self.robots)} robots.")

    @property
    def sim_time_s(self) -> int:
        return int(round(self.tick * self.tick_seconds))

    def run(self, ticks: int | None = None) -> dict[str, Any]:
        total_ticks = int(ticks or self.max_ticks)
        for _ in range(total_ticks):
            self.step()
        return self.snapshot()

    def step(self) -> None:
        self.tick += 1
        self.wait_for = {}
        self._generate_orders()
        self._complete_busy_skills()
        if self.tick == 1 or self.tick % self.planner_interval_ticks == 0:
            self._planner_check()
        self._reserve_inventory()
        self._assign_orders()
        self._advance_robot_routes()
        self._detect_and_recover_deadlocks()
        self._update_robot_utilization()

    def write_outputs(self, output_dir: str | Path | None = None) -> dict[str, Path]:
        configured_outputs = self.runtime_config.get("outputs", {})
        base_dir = Path(output_dir or self.options.output_dir or configured_outputs.get("dir", "submissions/warehouse_quadbot_atomic_demos/outputs"))
        base_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = base_dir / configured_outputs.get("snapshot_file", "runtime_snapshot.json")
        metrics_path = base_dir / configured_outputs.get("metrics_file", "benchmark_metrics.json")
        events_path = base_dir / configured_outputs.get("events_file", "runtime_events.jsonl")

        snapshot_path.write_text(json.dumps(self.snapshot(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        metrics_path.write_text(json.dumps(self.metrics_report(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with events_path.open("w", encoding="utf-8") as handle:
            for event in self.events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return {"snapshot": snapshot_path, "metrics": metrics_path, "events": events_path}

    def snapshot(self) -> dict[str, Any]:
        active_orders = [order for order in self.orders.values() if order.status not in {"completed", "failed", "cancelled"}]
        completed = [order for order in self.orders.values() if order.status == "completed"]
        pending = [order for order in active_orders if order.status in {"pending_inventory", "inventory_reserved", "robot_assigned"}]
        sla_risk = [order for order in active_orders if order.deadline_tick - self.tick <= int(300 / self.tick_seconds)]
        created_per_hr = self._per_hour(self.metrics.created_orders)
        completed_per_hr = self._per_hour(self.metrics.completed_orders)
        avg_fulfillment = self._average_completion_seconds(completed) / 60 if completed else 0.0

        return {
            "tick": self.tick,
            "sim_time_s": self.sim_time_s,
            "load": self.options.load,
            "speed": self.options.speed,
            "planner_enabled": self.options.planner_mode != "off",
            "orders": {
                "created_per_hr": round(created_per_hr),
                "completed_per_hr": round(completed_per_hr),
                "active": len(active_orders),
                "pending": len(pending),
                "sla_risk": len(sla_risk),
                "open": len(active_orders),
                "avg_fulfillment_min": round(avg_fulfillment, 1),
            },
            "order_rows": [self._order_row(order) for order in self._display_orders(active_orders)],
            "robots": [self._robot_snapshot(robot) for robot in sorted(self.robots.values(), key=lambda item: item.robot_id)],
            "warehouse": self._warehouse_snapshot(),
            "movement_locks": self._movement_locks_snapshot(),
            "shelves": [self._rack_module_snapshot(module) for module in self.rack_modules],
            "events": list(self.recent_messages)[-10:],
            "runtime": {
                "workflow": "Outbound Batch Fulfillment",
                "active_skills": self._active_skills(),
                "deadlocks": self.metrics.deadlock_count,
                "replans": self.metrics.replan_count,
                "latest_decision": self.last_planner_decision.latest_decision,
                "planner_mode": self.last_planner_decision.planner_mode,
                "planner_source": self.last_planner_decision.source,
                "handoff_mode": self.active_handoff_mode,
                "ai_interval_s": self.ai_interval_s,
                "next_planner_check_s": max(0, self.ai_interval_s - (self.sim_time_s % self.ai_interval_s)),
                "route_blocked_tile_violations": len(self.route_violations()),
                "route_cardinality_violations": len(self.route_cardinality_violations()),
                "collision_violations": len(self.collision_violations()),
                "lock_overlap_violations": len(self.lock_overlap_violations()),
            },
            "skill_evidence": {
                "shelf_pick": {
                    "video": "../outputs/shelf_pick.mp4",
                    "trajectory": "../outputs/shelf_pick_trajectory.json",
                    "success": True,
                },
                "handoff": {
                    "video": "../outputs/handoff.mp4",
                    "trajectory": "../outputs/handoff_trajectory.json",
                    "success": True,
                },
            },
        }

    def metrics_report(self) -> dict[str, Any]:
        completed = [order for order in self.orders.values() if order.status == "completed"]
        completion_ticks = [order.completion_tick - order.creation_tick for order in completed if order.completion_tick is not None]
        completion_ticks.sort()
        active_orders = [order for order in self.orders.values() if order.status not in {"completed", "failed", "cancelled"}]
        total_robot_ticks = max(1, self.tick * max(1, len(self.robots)))
        busy_ticks = sum(robot.busy_ticks for robot in self.robots.values())
        return {
            "run_id": self.options.run_id,
            "tick": self.tick,
            "sim_time_s": self.sim_time_s,
            "load": self.options.load,
            "planner_mode": self.options.planner_mode,
            "completed_orders": self.metrics.completed_orders,
            "created_orders": self.metrics.created_orders,
            "active_orders": len(active_orders),
            "throughput_orders_per_simulated_hour": round(self._per_hour(self.metrics.completed_orders), 2),
            "average_completion_ticks": round(sum(completion_ticks) / len(completion_ticks), 2) if completion_ticks else 0,
            "p50_completion_ticks": self._percentile(completion_ticks, 50),
            "p95_completion_ticks": self._percentile(completion_ticks, 95),
            "average_lock_wait_ticks": round(self.metrics.lock_wait_ticks / max(1, len(self.robots)), 2),
            "deadlock_count": self.metrics.deadlock_count,
            "deadlock_recovery_ticks": self.metrics.deadlock_recovery_ticks,
            "replan_count": self.metrics.replan_count,
            "robot_utilization_pct": round(100 * busy_ticks / total_robot_ticks, 1),
            "sla_miss_count": sum(1 for order in completed if order.completion_tick and order.completion_tick > order.deadline_tick),
            "planner_checks": self.metrics.planner_checks,
            "ai_planner_calls": self.metrics.ai_planner_calls,
            "local_planner_fallbacks": self.metrics.local_planner_fallbacks,
            "route_blocked_tile_violations": len(self.route_violations()),
            "route_cardinality_violations": len(self.route_cardinality_violations()),
            "collision_violations": len(self.collision_violations()),
            "lock_overlap_violations": len(self.lock_overlap_violations()),
        }

    def _build_world(self) -> None:
        warehouse = self.layout_config.get("warehouse", {})
        self.width_tiles = int(warehouse.get("width_tiles", 20))
        self.height_tiles = int(warehouse.get("height_tiles", 14))
        self.blocked_tiles = set(self.layout_config.get("tiles", {}).get("blocked_tiles", []))
        zone_by_tile: dict[str, str] = {}
        for zone in self.layout_config.get("zones", []):
            for tile_id in zone.get("tiles", []):
                zone_by_tile[tile_id] = zone.get("zone_id", zone.get("type", "zone"))
            if zone.get("type") == "deadlock_buffer":
                self.buffer_tiles.extend(zone.get("tiles", []))
            if zone.get("type") == "robot_depot":
                self.depot_tiles.extend(zone.get("tiles", []))

        for module_data in self.layout_config.get("rack_modules", []):
            module = self._rack_module_from_data(module_data)
            self.rack_modules.append(module)
            self.rack_tiles.update(module.footprint_tiles)

        for rack_data in self.layout_config.get("racks", []):
            footprint_tiles = self._rack_footprint_tiles(rack_data)
            self.rack_tiles.update(footprint_tiles)
            rack = Rack(
                rack_id=rack_data["rack_id"],
                sku_id=rack_data["sku_id"],
                pick_tile_id=rack_data["pick_tile_id"],
                storage_tile_id=rack_data["storage_tile_id"],
                quantity=int(rack_data.get("quantity", 1_000_000)),
                footprint_tiles=footprint_tiles,
            )
            self.racks.append(rack)
            self.racks_by_sku.setdefault(rack.sku_id, []).append(rack)
            self.service_tiles.add(rack.pick_tile_id)

        if not self.rack_modules:
            self.rack_modules = [self._single_tile_module_from_rack(rack) for rack in self.racks]

        self.blocked_tiles.update(self.rack_tiles)
        for y in range(self.height_tiles):
            for x in range(self.width_tiles):
                tile_id = tile_id_from_xy(x, y)
                self.tiles[tile_id] = Tile(tile_id, x, y, tile_id not in self.blocked_tiles, zone_by_tile.get(tile_id))

        for rack in self.racks:
            if rack.pick_tile_id not in self.tiles:
                raise ValueError(f"Rack {rack.rack_id} pick tile {rack.pick_tile_id} is outside the warehouse")
            if not self.tiles[rack.pick_tile_id].traversable:
                raise ValueError(f"Rack {rack.rack_id} pick tile {rack.pick_tile_id} overlaps a blocked rack footprint")
        for conveyor_data in self.layout_config.get("outbound", {}).get("conveyors", []):
            conveyor = Conveyor(**conveyor_data)
            self.conveyors.append(conveyor)
            self.service_tiles.add(conveyor.unload_tile_id)
        for robot_data in self.layout_config.get("robots", []):
            robot = Robot(
                robot_id=robot_data["robot_id"],
                robot_type_id=robot_data.get("robot_type_id", "quadbot_standard"),
                current_tile_id=robot_data["start_tile_id"],
                max_payload_weight=float(robot_data.get("max_payload_weight", 6.0)),
                handling_skill_level=int(robot_data.get("handling_skill_level", 3)),
                base_move_ticks_per_tile=int(robot_data.get("base_move_ticks_per_tile", 2)),
                load_speed_penalty=float(robot_data.get("load_speed_penalty", 0.08)),
                role=robot_data.get("role", "runner"),
            )
            if robot.current_tile_id not in self.tiles:
                raise ValueError(f"Robot {robot.robot_id} starts on unknown tile {robot.current_tile_id}")
            if not self.tiles[robot.current_tile_id].traversable:
                raise ValueError(f"Robot {robot.robot_id} starts on non-traversable tile {robot.current_tile_id}")
            if self.occupancy.get(robot.current_tile_id):
                raise ValueError(f"Duplicate robot start tile {robot.current_tile_id}")
            self.robots[robot.robot_id] = robot
            self.occupancy[robot.current_tile_id] = robot.robot_id

    def _generate_orders(self) -> None:
        profile = self._selected_order_profile()
        rate = float(profile.get("orders_per_hour", profile.get("average_orders_per_hour", 300)))
        lam = rate * self.tick_seconds / 3600
        count = int(lam)
        if self.random.random() < lam - count:
            count += 1
        for _ in range(count):
            sku = self._choose_weighted(profile.get("skus", []), "probability")
            priority_label = self._choose_priority(profile.get("priority_distribution", {}))
            self.order_sequence += 1
            deadline_s = DEADLINE_SECONDS[priority_label] + int(sku.get("difficulty", 1) * 60 + sku.get("weight", 1.0) * 20)
            order = Order(
                order_id=f"ORD-RUNTIME-{self.order_sequence:09d}",
                order_sequence=self.order_sequence,
                sku_id=sku["sku_id"],
                weight=float(sku.get("weight", 1.0)),
                difficulty=int(sku.get("difficulty", 1)),
                priority_label=priority_label,
                priority=PRIORITY_VALUES[priority_label],
                creation_tick=self.tick,
                deadline_tick=self.tick + max(1, int(round(deadline_s / self.tick_seconds))),
            )
            self.orders[order.order_id] = order
            self.metrics.created_orders += 1
            self._emit("order.created", f"Created {order.order_id} {order.sku_id} {priority_label}.", order_id=order.order_id)

    def _planner_check(self) -> None:
        if self.options.planner_mode == "off":
            return
        summary = {
            "tick": self.tick,
            "sim_time_s": self.sim_time_s,
            "load": self.options.load,
            "active_orders": sum(1 for order in self.orders.values() if order.status not in {"completed", "failed", "cancelled"}),
            "pending_orders": sum(1 for order in self.orders.values() if order.status in {"pending_inventory", "inventory_reserved"}),
            "waiting_robots": sum(1 for robot in self.robots.values() if robot.wait_ticks > 0),
            "deadlocks": self.metrics.deadlock_count,
            "replans": self.metrics.replan_count,
            "completed_per_hour": self._per_hour(self.metrics.completed_orders),
        }
        fallback = local_planner_decision(summary)
        if self.options.planner_mode == "openai":
            self.metrics.ai_planner_calls += 1
            decision = openai_planner_decision(summary, fallback)
            if decision.source.startswith("local_fallback"):
                self.metrics.local_planner_fallbacks += 1
        else:
            decision = fallback
        self.metrics.planner_checks += 1
        self.last_planner_decision = decision
        self.active_handoff_mode = decision.handoff_enabled
        self._emit("planner.checked", decision.latest_decision, decision=decision.to_dict())

    def _reserve_inventory(self) -> None:
        for order in self.orders.values():
            if order.status != "pending_inventory":
                continue
            rack = self._nearest_rack_for_order(order, None)
            if not rack:
                order.status = "failed"
                order.failure_reason = "stockout"
                self.metrics.failed_orders += 1
                self._emit("order.failed", f"{order.order_id} failed: no rack for {order.sku_id}.", order_id=order.order_id)
                continue
            order.rack_id = rack.rack_id
            order.pick_tile_id = rack.pick_tile_id
            conveyor = self._choose_conveyor(order)
            order.conveyor_id = conveyor.conveyor_id
            order.unload_tile_id = conveyor.unload_tile_id
            order.status = "inventory_reserved"
            order.inventory_reserved_tick = self.tick

    def _assign_orders(self) -> None:
        for robot in self.robots.values():
            if robot.status in {"ready", "idle"} and not robot.assigned_order_id and robot.current_tile_id in self.service_tiles:
                self._send_robot_to_staging(robot)
        available = [
            robot for robot in self.robots.values()
            if robot.status in {"ready", "idle"} and not robot.assigned_order_id and robot.current_tile_id not in self.service_tiles
        ]
        if not available:
            return
        open_orders = [
            order for order in self.orders.values()
            if order.status == "inventory_reserved" and not order.assigned_robot_id
        ]
        if not open_orders:
            return
        assigned_orders: set[str] = set()
        for robot in sorted(available, key=lambda item: item.robot_id):
            candidates = [order for order in open_orders if order.order_id not in assigned_orders and self._robot_can_carry(robot, order)]
            if not candidates:
                continue
            order = max(candidates, key=lambda item: self._assignment_score(robot, item))
            if not order.pick_tile_id:
                continue
            if not self._set_route(robot, order.pick_tile_id, "navigating_to_rack"):
                continue
            assigned_orders.add(order.order_id)
            order.assigned_robot_id = robot.robot_id
            order.assignment_tick = self.tick
            order.status = "navigating_to_rack"
            robot.assigned_order_id = order.order_id
            self._emit("order.assigned", f"Assigned {order.order_id} to {robot.robot_id} for {order.pick_tile_id}.", order_id=order.order_id, robot_id=robot.robot_id)

    def _complete_busy_skills(self) -> None:
        for robot in self.robots.values():
            if robot.busy_until_tick <= self.tick:
                if robot.status == "picking":
                    self._complete_pick(robot)
                elif robot.status == "unloading":
                    self._complete_unload(robot)

    def _advance_robot_routes(self) -> None:
        self.last_lock_requests = []
        self.last_granted_moves = []
        self.last_denied_moves = []
        requests: list[tuple[float, Robot, str]] = []
        blocked_by: dict[str, tuple[str, str]] = {}

        for robot in self.robots.values():
            if robot.status not in {"navigating_to_rack", "navigating_to_conveyor", "relocating_to_buffer", "blocked", "waiting_for_tile_lock"}:
                continue
            if not robot.route:
                robot.next_tile_id = None
                self._handle_arrival(robot)
                continue
            if self.tick < robot.available_at_tick:
                continue

            source_tile = robot.current_tile_id
            next_tile = robot.route[0]
            priority = self._robot_move_priority(robot)
            robot.next_tile_id = next_tile
            self._record_lock_request(robot, source_tile, next_tile, priority)

            if not self._is_cardinal_step(source_tile, next_tile):
                self._record_denied_move(robot, source_tile, next_tile, "non_cardinal_step")
                self._emit("route.invalid_step", f"{robot.robot_id} route step {source_tile}->{next_tile} is not N/S/E/W; replanning.", robot_id=robot.robot_id, source=source_tile, destination=next_tile)
                self._replan_robot(robot, "route_step_not_cardinal_neighbor")
                continue
            if next_tile not in self.tiles or not self.tiles[next_tile].traversable:
                self._record_denied_move(robot, source_tile, next_tile, "blocked_tile")
                self._emit("route.blocked_tile", f"{robot.robot_id} route step {next_tile} is blocked; replanning.", robot_id=robot.robot_id, tile_id=next_tile)
                self._replan_robot(robot, "blocked_tile_on_route")
                continue

            owner = self.occupancy.get(next_tile)
            if owner and owner != robot.robot_id:
                reason = "destination_occupied"
                owner_robot = self.robots.get(owner)
                if owner_robot and owner_robot.route and owner_robot.route[0] == source_tile:
                    reason = "head_on_swap_locked"
                blocked_by[robot.robot_id] = (owner, reason)
                self._record_denied_move(robot, source_tile, next_tile, reason, blocker=owner)
                continue
            requests.append((priority, robot, next_tile))

        requests.sort(key=lambda item: (-item[0], item[1].robot_id))
        claimed_destinations: set[str] = set()
        moved_robot_ids: set[str] = set()
        for _, robot, next_tile in requests:
            source_tile = robot.current_tile_id
            if next_tile in claimed_destinations:
                blocked_by[robot.robot_id] = ("destination_claimed", "destination_claimed")
                self._record_denied_move(robot, source_tile, next_tile, "destination_claimed")
                continue
            if not self._is_cardinal_step(source_tile, next_tile):
                self._record_denied_move(robot, source_tile, next_tile, "non_cardinal_step_during_arbitration")
                self._replan_robot(robot, "route_step_not_cardinal_during_arbitration")
                continue
            if next_tile not in self.tiles or not self.tiles[next_tile].traversable:
                self._record_denied_move(robot, source_tile, next_tile, "blocked_tile_during_arbitration")
                self._emit("route.blocked_tile", f"{robot.robot_id} destination {next_tile} is blocked during lock arbitration.", robot_id=robot.robot_id, tile_id=next_tile)
                self._replan_robot(robot, "blocked_tile_during_arbitration")
                continue
            occupant = self.occupancy.get(next_tile)
            if occupant and occupant != robot.robot_id:
                reason = "destination_occupied"
                occupant_robot = self.robots.get(occupant)
                if occupant_robot and occupant_robot.route and occupant_robot.route[0] == source_tile:
                    reason = "head_on_swap_locked"
                blocked_by[robot.robot_id] = (occupant, reason)
                self._record_denied_move(robot, source_tile, next_tile, reason, blocker=occupant)
                continue
            if self.occupancy.get(source_tile) != robot.robot_id:
                robot.status = "error"
                self._record_denied_move(robot, source_tile, next_tile, "source_occupancy_mismatch")
                self._emit("robot.error", f"{robot.robot_id} occupancy mismatch at {source_tile}.", robot_id=robot.robot_id)
                continue
            claimed_destinations.add(next_tile)
            self._commit_move(robot, next_tile)
            moved_robot_ids.add(robot.robot_id)

        for robot_id, (blocker, reason) in blocked_by.items():
            robot = self.robots[robot_id]
            if robot_id in moved_robot_ids:
                continue
            robot.status = "waiting_for_tile_lock"
            robot.wait_ticks += 1
            robot.lock_denials += 1
            self.metrics.lock_wait_ticks += 1
            if blocker in self.robots:
                self.wait_for[robot_id] = blocker
            self._emit("robot.lock_wait", f"{robot.robot_id} waits for tile {robot.next_tile_id} blocked by {blocker} ({reason}).", robot_id=robot.robot_id, blocker=blocker, reason=reason)
            if robot.lock_denials >= self.lock_replan_threshold or robot.wait_ticks >= self.wait_replan_threshold:
                self._replan_robot(robot, "repeated_lock_denial")

    def _commit_move(self, robot: Robot, next_tile: str) -> None:
        if next_tile not in self.tiles or not self.tiles[next_tile].traversable:
            robot.status = "blocked"
            self._emit("robot.blocked", f"{robot.robot_id} refused blocked tile {next_tile}.", robot_id=robot.robot_id, tile_id=next_tile)
            self._replan_robot(robot, "blocked_destination_refused")
            return
        source = robot.current_tile_id
        del self.occupancy[source]
        self.occupancy[next_tile] = robot.robot_id
        robot.current_tile_id = next_tile
        robot.route.pop(0)
        robot.next_tile_id = robot.route[0] if robot.route else None
        robot.heading = self._heading_from_to(source, next_tile)
        robot.wait_ticks = 0
        robot.lock_denials = 0
        if robot.assigned_order_id or robot.carried_order_id:
            robot.status = "navigating_to_conveyor" if robot.carried_order_id else "navigating_to_rack"
        robot.available_at_tick = self.tick + self._move_duration_ticks(robot)
        robot.battery_pct = max(8.0, robot.battery_pct - 0.006 * self._move_duration_ticks(robot))
        self._record_granted_move(robot.robot_id, source, next_tile)
        self._emit("robot.moved", f"{robot.robot_id} moved {source}->{next_tile}.", robot_id=robot.robot_id, source=source, destination=next_tile)
        if not robot.route:
            self._handle_arrival(robot)

    def _record_lock_request(self, robot: Robot, source_tile: str, destination_tile: str, priority: float) -> None:
        self.last_lock_requests.append({
            "tick": self.tick,
            "robot_id": robot.robot_id,
            "source_tile": source_tile,
            "destination_tile": destination_tile,
            "lock_tiles": [source_tile, destination_tile],
            "priority": round(priority, 2),
        })

    def _record_granted_move(self, robot_id: str, source_tile: str, destination_tile: str) -> None:
        self.last_granted_moves.append({
            "tick": self.tick,
            "robot_id": robot_id,
            "source_tile": source_tile,
            "destination_tile": destination_tile,
            "lock_tiles": [source_tile, destination_tile],
        })

    def _record_denied_move(self, robot: Robot, source_tile: str, destination_tile: str, reason: str, blocker: str | None = None) -> None:
        self.last_denied_moves.append({
            "tick": self.tick,
            "robot_id": robot.robot_id,
            "source_tile": source_tile,
            "destination_tile": destination_tile,
            "lock_tiles": [source_tile, destination_tile],
            "reason": reason,
            "blocker": blocker,
        })

    def _handle_arrival(self, robot: Robot) -> None:
        if robot.recovery_goal_tile_id and robot.current_tile_id == robot.recovery_goal_tile_id:
            robot.recovery_goal_tile_id = None
            self._replan_robot(robot, "resume_after_buffer")
            return
        order = self._robot_order(robot)
        if not order:
            robot.status = "ready"
            robot.target_tile_id = None
            return
        if not robot.carried_order_id and order.pick_tile_id == robot.current_tile_id:
            self._start_pick(robot, order)
        elif robot.carried_order_id and order.unload_tile_id == robot.current_tile_id:
            self._start_unload(robot, order)

    def _start_pick(self, robot: Robot, order: Order) -> None:
        duration = max(1, int(round((4 + order.difficulty * 2) / self.tick_seconds)))
        order.status = "picking"
        robot.status = "picking"
        robot.busy_until_tick = self.tick + duration
        self._emit("skill.started", f"{robot.robot_id} started shelf_pick for {order.order_id} ({duration}s).", robot_id=robot.robot_id, order_id=order.order_id)

    def _complete_pick(self, robot: Robot) -> None:
        order = self._robot_order(robot)
        if not order:
            robot.status = "ready"
            return
        order.status = "in_transit"
        order.picked_tick = self.tick
        robot.carried_order_id = order.order_id
        robot.carried_sku_id = order.sku_id
        robot.carried_weight = order.weight
        self._emit("skill.completed", f"{robot.robot_id} picked {order.sku_id} for {order.order_id}.", robot_id=robot.robot_id, order_id=order.order_id)
        conveyor = self._choose_conveyor(order, robot)
        order.conveyor_id = conveyor.conveyor_id
        order.unload_tile_id = conveyor.unload_tile_id
        if order.unload_tile_id and self._set_route(robot, order.unload_tile_id, "navigating_to_conveyor"):
            order.status = "navigating_to_conveyor"
        else:
            self._fail_order(order, "conveyor_blocked")
            self._release_robot(robot)

    def _start_unload(self, robot: Robot, order: Order) -> None:
        duration = max(1, int(round((3 + order.difficulty + order.weight * 0.4) / self.tick_seconds)))
        order.status = "unloading_at_conveyor"
        robot.status = "unloading"
        robot.busy_until_tick = self.tick + duration
        self._emit("skill.started", f"{robot.robot_id} started unload for {order.order_id} ({duration}s).", robot_id=robot.robot_id, order_id=order.order_id)

    def _complete_unload(self, robot: Robot) -> None:
        order = self._robot_order(robot)
        if not order:
            self._release_robot(robot)
            return
        order.status = "completed"
        order.unloaded_tick = self.tick
        order.completion_tick = self.tick
        self.metrics.completed_orders += 1
        self._emit("order.completed", f"Completed {order.order_id} via {robot.robot_id} at {order.conveyor_id}.", robot_id=robot.robot_id, order_id=order.order_id)
        self._release_robot(robot)
        self._send_robot_to_staging(robot)

    def _detect_and_recover_deadlocks(self) -> None:
        if not self.wait_for:
            return
        cycle = self._find_wait_cycle()
        if not cycle:
            for robot_id in list(self.wait_for):
                robot = self.robots[robot_id]
                if robot.wait_ticks >= self.deadlock_confirm_ticks:
                    self._replan_robot(robot, "long_wait_recovery")
            return
        signature = "|".join(sorted(cycle))
        is_new_event = self.tick >= self.deadlock_cooldowns.get(signature, 0)
        victim = min((self.robots[rid] for rid in cycle), key=lambda item: self._robot_move_priority(item))
        buffer_tile = self._nearest_buffer_tile(victim.current_tile_id)
        if is_new_event:
            self.metrics.deadlock_count += 1
            self.deadlock_cooldowns[signature] = self.tick + max(20, self.deadlock_confirm_ticks)
            self._emit("deadlock.detected", f"Deadlock cycle {' -> '.join(cycle)}; {victim.robot_id} selected for recovery.", cycle=cycle)
        if buffer_tile and self._set_route(victim, buffer_tile, "blocked", avoid_occupied=True):
            victim.recovery_goal_tile_id = buffer_tile
            if is_new_event:
                self.metrics.deadlock_recovery_ticks += 1
                self._emit("deadlock.recovered", f"{victim.robot_id} backing off to buffer {buffer_tile}.", robot_id=victim.robot_id)
        else:
            self._replan_robot(victim, "deadlock_reroute")

    def _replan_robot(self, robot: Robot, reason: str) -> bool:
        order = self._robot_order(robot)
        if not order:
            robot.route = []
            robot.status = "ready"
            return False
        cooldown_ticks = max(4, self.wait_replan_threshold // 2)
        if self.tick - robot.last_replan_tick < cooldown_ticks:
            return False
        if robot.carried_order_id:
            conveyor = self._choose_conveyor(order, robot)
            order.conveyor_id = conveyor.conveyor_id
            order.unload_tile_id = conveyor.unload_tile_id
        target = order.unload_tile_id if robot.carried_order_id else order.pick_tile_id
        if not target:
            return False
        ok = self._set_route(robot, target, "navigating_to_conveyor" if robot.carried_order_id else "navigating_to_rack", avoid_occupied=True)
        if ok:
            robot.last_replan_tick = self.tick
            self.metrics.replan_count += 1
            self._emit("route.replanned", f"Replanned {robot.robot_id} because {reason}.", robot_id=robot.robot_id, reason=reason)
        return ok

    def _set_route(self, robot: Robot, target_tile_id: str, status: str, avoid_occupied: bool = True) -> bool:
        path = self._astar(robot.current_tile_id, target_tile_id, avoid_occupied=avoid_occupied, robot_id=robot.robot_id)
        if not path:
            path = self._astar(robot.current_tile_id, target_tile_id, avoid_occupied=False, robot_id=robot.robot_id)
        if not path:
            return False
        blocked = [tile_id for tile_id in path if tile_id != robot.current_tile_id and not self.tiles[tile_id].traversable]
        if blocked:
            self._emit("route.invalid", f"Rejected route for {robot.robot_id}; blocked tiles: {', '.join(blocked)}.", robot_id=robot.robot_id, blocked_tiles=blocked)
            return False
        robot.route = path[1:]
        robot.target_tile_id = target_tile_id
        robot.next_tile_id = robot.route[0] if robot.route else None
        robot.status = status
        if not robot.route:
            self._handle_arrival(robot)
        return True

    def _astar(self, start: str, goal: str, avoid_occupied: bool, robot_id: str | None = None) -> list[str] | None:
        if start not in self.tiles or goal not in self.tiles:
            return None
        if not self.tiles[goal].traversable:
            return None
        occupied = set(self.occupancy)
        if robot_id:
            occupied = {tile for tile in occupied if self.occupancy[tile] != robot_id}
        if goal in occupied:
            occupied.remove(goal)
        frontier: list[tuple[float, str]] = [(0.0, start)]
        came_from: dict[str, str | None] = {start: None}
        cost_so_far: dict[str, float] = {start: 0.0}
        while frontier:
            frontier.sort(key=lambda item: item[0])
            _, current = frontier.pop(0)
            if current == goal:
                break
            for neighbor in self._neighbors(current):
                if not self.tiles[neighbor].traversable:
                    continue
                if avoid_occupied and neighbor in occupied:
                    continue
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self._manhattan(neighbor, goal)
                    frontier.append((priority, neighbor))
                    came_from[neighbor] = current
        if goal not in came_from:
            return None
        path = [goal]
        current = goal
        while came_from[current] is not None:
            current = came_from[current]  # type: ignore[assignment]
            path.append(current)
        path.reverse()
        return path

    def _rack_module_from_data(self, data: dict[str, Any]) -> RackModule:
        footprint_tiles = list(data.get("footprint_tiles") or [])
        if not footprint_tiles:
            origin = data.get("origin_tile_id") or data.get("storage_tile_id")
            if not origin and "x" in data and "y" in data:
                origin = tile_id_from_xy(int(data["x"]), int(data["y"]))
            if not origin:
                raise ValueError(f"Rack module {data.get('module_id', '<unknown>')} needs footprint_tiles or origin coordinates")
            footprint_tiles = rect_tiles(origin, int(data.get("w", data.get("width_tiles", 1))), int(data.get("d", data.get("depth_tiles", data.get("length", 1)))))
        xs, ys = zip(*(xy_from_tile_id(tile_id) for tile_id in footprint_tiles))
        x = int(data.get("x", min(xs)))
        y = int(data.get("y", min(ys)))
        w = int(data.get("w", max(xs) - min(xs) + 1))
        d = int(data.get("d", max(ys) - min(ys) + 1))
        return RackModule(
            module_id=data.get("module_id") or data.get("rack_module_id") or data.get("rack_id") or f"rack_module_{len(self.rack_modules) + 1}",
            footprint_tiles=footprint_tiles,
            pick_tiles=list(data.get("pick_tiles", [])),
            x=x,
            y=y,
            w=w,
            d=d,
            length=int(data.get("length", max(w, d))),
            direction=str(data.get("direction", "ne")),
            material=str(data.get("material", "cardboard")),
            fill=str(data.get("fill", "full")),
        )

    def _single_tile_module_from_rack(self, rack: Rack) -> RackModule:
        x, y = xy_from_tile_id(rack.storage_tile_id)
        return RackModule(
            module_id=rack.rack_id,
            footprint_tiles=list(rack.footprint_tiles or [rack.storage_tile_id]),
            pick_tiles=[rack.pick_tile_id],
            x=x,
            y=y,
            w=1,
            d=1,
            length=1,
            material=material_from_sku(rack.sku_id),
        )

    def _rack_footprint_tiles(self, data: dict[str, Any]) -> list[str]:
        if data.get("footprint_tiles"):
            return list(data["footprint_tiles"])
        if data.get("storage_tile_ids"):
            return list(data["storage_tile_ids"])
        if data.get("footprint"):
            footprint = data["footprint"]
            origin = footprint.get("origin_tile_id") or footprint.get("storage_tile_id") or data.get("storage_tile_id")
            return rect_tiles(origin, int(footprint.get("w", footprint.get("width_tiles", 1))), int(footprint.get("d", footprint.get("depth_tiles", 1))))
        return [data["storage_tile_id"]]

    def _selected_order_profile(self) -> dict[str, Any]:
        profiles = {item.get("profile_id"): item for item in self.layout_config.get("order_profiles", [])}
        return profiles.get(f"{self.options.load}_load") or profiles.get("medium_load") or next(iter(profiles.values()))

    def _choose_weighted(self, items: list[dict[str, Any]], weight_key: str) -> dict[str, Any]:
        if not items:
            raise ValueError("Order profile must define skus")
        total = sum(float(item.get(weight_key, 1)) for item in items)
        mark = self.random.random() * total
        upto = 0.0
        for item in items:
            upto += float(item.get(weight_key, 1))
            if upto >= mark:
                return item
        return items[-1]

    def _choose_priority(self, distribution: dict[str, float]) -> str:
        if not distribution:
            distribution = {"low": 0.45, "normal": 0.35, "high": 0.15, "urgent": 0.05}
        total = sum(float(value) for value in distribution.values())
        mark = self.random.random() * total
        upto = 0.0
        for label, value in distribution.items():
            upto += float(value)
            if upto >= mark:
                return label
        return "normal"

    def _nearest_rack_for_order(self, order: Order, robot: Robot | None) -> Rack | None:
        racks = self.racks_by_sku.get(order.sku_id, [])
        if not racks:
            return None
        if not robot:
            return racks[order.order_sequence % len(racks)]
        return min(racks, key=lambda rack: self._manhattan(robot.current_tile_id, rack.pick_tile_id))

    def _choose_conveyor(self, order: Order, robot: Robot | None = None) -> Conveyor:
        if not self.conveyors:
            raise ValueError("Layout must define outbound conveyors")
        origin = robot.current_tile_id if robot else order.pick_tile_id

        def score(conveyor: Conveyor) -> float:
            distance = self._manhattan(origin, conveyor.unload_tile_id) if origin else 0
            active_queue = sum(
                1 for existing in self.orders.values()
                if existing.order_id != order.order_id
                and existing.conveyor_id == conveyor.conveyor_id
                and existing.status not in {"completed", "failed", "cancelled"}
            )
            route_pressure = sum(
                1 for bot in self.robots.values()
                if bot.robot_id != (robot.robot_id if robot else None)
                and (bot.target_tile_id == conveyor.unload_tile_id or bot.next_tile_id == conveyor.unload_tile_id)
            )
            occupied_penalty = 1 if conveyor.unload_tile_id in self.occupancy else 0
            return distance + active_queue * 16 + route_pressure * 8 + occupied_penalty * 12

        return min(self.conveyors, key=score)

    def _robot_can_carry(self, robot: Robot, order: Order) -> bool:
        return robot.max_payload_weight >= order.weight and robot.handling_skill_level >= max(1, order.difficulty - 1)

    def _assignment_score(self, robot: Robot, order: Order) -> float:
        rack = self._nearest_rack_for_order(order, robot)
        if rack:
            order.rack_id = rack.rack_id
            order.pick_tile_id = rack.pick_tile_id
        conveyor = self._choose_conveyor(order)
        order.conveyor_id = conveyor.conveyor_id
        order.unload_tile_id = conveyor.unload_tile_id
        travel = self._manhattan(robot.current_tile_id, order.pick_tile_id or robot.current_tile_id)
        if order.pick_tile_id and order.unload_tile_id:
            travel += self._manhattan(order.pick_tile_id, order.unload_tile_id)
        age = self.tick - order.creation_tick
        slack = max(1, order.deadline_tick - self.tick)
        priority_boost = self.last_planner_decision.priority_boost if order.priority >= 75 else 0.0
        return order.priority * 10 + age * 0.2 + priority_boost - travel * 3 - order.difficulty * 4 - order.weight * 1.5 - slack * 0.01

    def _move_duration_ticks(self, robot: Robot) -> int:
        multiplier = 1.0 + max(0.0, robot.carried_weight) * robot.load_speed_penalty
        return max(1, int(math.ceil(robot.base_move_ticks_per_tile * multiplier)))

    def _robot_move_priority(self, robot: Robot) -> float:
        order = self._robot_order(robot)
        priority = order.priority if order else 0
        loaded_bonus = 8 if robot.carried_order_id else 0
        return priority + loaded_bonus + robot.wait_ticks * 2

    def _robot_order(self, robot: Robot) -> Order | None:
        order_id = robot.assigned_order_id or robot.carried_order_id
        return self.orders.get(order_id) if order_id else None

    def _release_robot(self, robot: Robot) -> None:
        robot.status = "ready"
        robot.assigned_order_id = None
        robot.carried_order_id = None
        robot.carried_sku_id = None
        robot.carried_weight = 0.0
        robot.target_tile_id = None
        robot.next_tile_id = None
        robot.route = []
        robot.busy_until_tick = 0
        robot.available_at_tick = self.tick

    def _send_robot_to_staging(self, robot: Robot) -> bool:
        if robot.assigned_order_id or robot.carried_order_id or robot.route:
            return False
        for target_tile_id in self._staging_candidates(robot.current_tile_id):
            if self._set_route(robot, target_tile_id, "relocating_to_buffer", avoid_occupied=True):
                self._emit("robot.relocated", f"{robot.robot_id} clearing service tile {robot.current_tile_id} toward {target_tile_id}.", robot_id=robot.robot_id, target_tile_id=target_tile_id)
                return True
        return False

    def _staging_candidates(self, start: str) -> list[str]:
        candidates = []
        for tile_id in [*self.buffer_tiles, *self.depot_tiles]:
            if tile_id == start or tile_id in self.occupancy:
                continue
            tile = self.tiles.get(tile_id)
            if tile and tile.traversable:
                candidates.append(tile_id)
        return sorted(candidates, key=lambda tile_id: self._manhattan(start, tile_id))

    def _fail_order(self, order: Order, reason: str) -> None:
        order.status = "failed"
        order.failure_reason = reason
        self.metrics.failed_orders += 1
        self._emit("order.failed", f"{order.order_id} failed: {reason}.", order_id=order.order_id)

    def _find_wait_cycle(self) -> list[str] | None:
        for start in self.wait_for:
            seen: list[str] = []
            current = start
            while current in self.wait_for:
                if current in seen:
                    return seen[seen.index(current):]
                seen.append(current)
                current = self.wait_for[current]
        return None

    def _nearest_buffer_tile(self, start: str) -> str | None:
        candidates = [tile for tile in self.buffer_tiles if tile in self.tiles and self.tiles[tile].traversable and tile not in self.occupancy]
        if not candidates:
            return None
        return min(candidates, key=lambda tile: self._manhattan(start, tile))

    def _neighbors(self, tile_id: str) -> Iterable[str]:
        x, y = xy_from_tile_id(tile_id)
        for dx, dy in DIRECTIONS.values():
            next_id = tile_id_from_xy(x + dx, y + dy)
            if next_id in self.tiles:
                yield next_id

    def _are_neighbors(self, a: str, b: str) -> bool:
        return b in set(self._neighbors(a))

    def _is_cardinal_step(self, a: str, b: str) -> bool:
        return self._manhattan(a, b) == 1

    def _manhattan(self, a: str, b: str) -> int:
        ax, ay = xy_from_tile_id(a)
        bx, by = xy_from_tile_id(b)
        return abs(ax - bx) + abs(ay - by)

    def _heading_from_to(self, a: str, b: str) -> str | None:
        ax, ay = xy_from_tile_id(a)
        bx, by = xy_from_tile_id(b)
        dx, dy = bx - ax, by - ay
        for heading, delta in DIRECTIONS.items():
            if delta == (dx, dy):
                return heading
        return None

    def _update_robot_utilization(self) -> None:
        for robot in self.robots.values():
            if robot.status not in {"ready", "idle", "waiting_for_tile_lock"}:
                robot.busy_ticks += 1

    def _active_skills(self) -> list[str]:
        skills = {"route_plan"}
        if any(robot.status in {"navigating_to_rack", "navigating_to_conveyor", "relocating_to_buffer", "waiting_for_tile_lock"} for robot in self.robots.values()):
            skills.add("move_tile")
        if any(robot.status == "picking" for robot in self.robots.values()):
            skills.add("shelf_pick")
        if any(robot.status == "unloading" for robot in self.robots.values()):
            skills.add("unload")
        if self.active_handoff_mode:
            skills.add("handoff")
        if self.metrics.deadlock_count:
            skills.add("deadlock_recovery")
        return sorted(skills)

    def _display_orders(self, active_orders: list[Order]) -> list[Order]:
        active_orders.sort(key=lambda order: (-order.priority, order.deadline_tick, order.creation_tick))
        return active_orders[:12]

    def _order_row(self, order: Order) -> dict[str, Any]:
        return {
            "id": order.order_id.replace("ORD-RUNTIME-", "ORD-"),
            "priority": {"urgent": "P0", "high": "P1", "normal": "P2", "low": "P3"}.get(order.priority_label, "P2"),
            "difficulty": difficulty_label(order.difficulty),
            "weight_kg": order.weight,
            "assigned_robot": order.assigned_robot_id or "-",
            "age_s": max(0, self.tick - order.creation_tick) * self.tick_seconds,
            "status": order.status,
        }

    def _robot_snapshot(self, robot: Robot) -> dict[str, Any]:
        x, y = xy_from_tile_id(robot.current_tile_id)
        route_points = [[float(x), float(y)]]
        for tile_id in robot.route[:12]:
            rx, ry = xy_from_tile_id(tile_id)
            route_points.append([float(rx), float(ry)])
        order = self._robot_order(robot)
        route_tiles = [robot.current_tile_id, *robot.route]
        route_cardinal = all(self._is_cardinal_step(a, b) for a, b in zip(route_tiles, route_tiles[1:]))
        lock_tiles = [robot.current_tile_id] + ([robot.next_tile_id] if robot.next_tile_id else [])
        return {
            "id": robot.robot_id,
            "x": float(x),
            "y": float(y),
            "tile_id": robot.current_tile_id,
            "heading": robot.heading,
            "status": robot.status,
            "battery": round(robot.battery_pct),
            "carrying": bool(robot.carried_order_id),
            "current_order": order.order_id.replace("ORD-RUNTIME-", "ORD-") if order else None,
            "current_target": robot.target_tile_id,
            "next_target": robot.next_tile_id,
            "movement_model": "four_direction_grid",
            "route_closed": False,
            "route_cardinal": route_cardinal,
            "lock_tiles": lock_tiles,
            "carried_sku": robot.carried_sku_id,
            "carried_weight_kg": robot.carried_weight or None,
            "route": route_points,
            "wait_ticks": robot.wait_ticks,
            "role": robot.role,
        }

    def _movement_locks_snapshot(self) -> dict[str, Any]:
        return {
            "model": "source_and_destination_tile_atomic",
            "occupied_tiles": [
                {"tile_id": tile_id, "robot_id": robot_id}
                for tile_id, robot_id in sorted(self.occupancy.items())
            ],
            "requested_moves": list(self.last_lock_requests),
            "granted_moves": list(self.last_granted_moves),
            "denied_moves": list(self.last_denied_moves),
            "lock_overlap_violations": self.lock_overlap_violations(),
        }

    def _warehouse_snapshot(self) -> dict[str, Any]:
        return {
            "width_tiles": self.width_tiles,
            "height_tiles": self.height_tiles,
            "movement_model": "four_direction_grid",
            "lock_model": "current_and_next_tile",
            "blocked_tiles": sorted(self.blocked_tiles),
            "rack_tiles": sorted(self.rack_tiles),
            "buffer_tiles": sorted(self.buffer_tiles),
            "depot_tiles": sorted(self.depot_tiles),
            "service_tiles": sorted(self.service_tiles),
            "occupied_tiles": [
                {"tile_id": tile_id, "robot_id": robot_id}
                for tile_id, robot_id in sorted(self.occupancy.items())
            ],
        }

    def _rack_module_snapshot(self, module: RackModule) -> dict[str, Any]:
        return {
            "id": module.module_id,
            "x": float(module.x),
            "y": float(module.y),
            "w": float(module.w),
            "d": float(module.d),
            "h": 1.35,
            "length": module.length,
            "direction": module.direction,
            "material": module.material,
            "fill": module.fill,
            "anchorX": module.x + module.w,
            "anchorY": module.y + module.d,
            "footprint_tiles": list(module.footprint_tiles),
            "pick_tiles": list(module.pick_tiles),
            "blocks_robot": True,
        }

    def route_violations(self) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        for robot in self.robots.values():
            for tile_id in [robot.current_tile_id, *robot.route]:
                if tile_id in self.rack_tiles or (tile_id in self.tiles and not self.tiles[tile_id].traversable):
                    violations.append({"robot_id": robot.robot_id, "tile_id": tile_id})
        return violations

    def route_cardinality_violations(self) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        for robot in self.robots.values():
            route_tiles = [robot.current_tile_id, *robot.route]
            for source_tile, destination_tile in zip(route_tiles, route_tiles[1:]):
                if not self._is_cardinal_step(source_tile, destination_tile):
                    violations.append({
                        "robot_id": robot.robot_id,
                        "source_tile": source_tile,
                        "destination_tile": destination_tile,
                    })
        return violations

    def collision_violations(self) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        seen: dict[str, str] = {}
        for robot in self.robots.values():
            owner = seen.get(robot.current_tile_id)
            if owner and owner != robot.robot_id:
                violations.append({
                    "tile_id": robot.current_tile_id,
                    "robot_ids": [owner, robot.robot_id],
                    "reason": "duplicate_robot_tile",
                })
            seen[robot.current_tile_id] = robot.robot_id
            occupancy_owner = self.occupancy.get(robot.current_tile_id)
            if occupancy_owner != robot.robot_id:
                violations.append({
                    "tile_id": robot.current_tile_id,
                    "robot_id": robot.robot_id,
                    "occupancy_owner": occupancy_owner,
                    "reason": "occupancy_mismatch",
                })
        for tile_id, robot_id in self.occupancy.items():
            robot = self.robots.get(robot_id)
            if not robot or robot.current_tile_id != tile_id:
                violations.append({
                    "tile_id": tile_id,
                    "robot_id": robot_id,
                    "reason": "stale_occupancy_entry",
                })
        return violations

    def lock_overlap_violations(self) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        tile_owner: dict[str, str] = {}
        for move in self.last_granted_moves:
            robot_id = str(move.get("robot_id"))
            for tile_id in move.get("lock_tiles", []):
                owner = tile_owner.get(tile_id)
                if owner and owner != robot_id:
                    violations.append({
                        "tile_id": tile_id,
                        "robot_ids": [owner, robot_id],
                        "reason": "same_tick_lock_overlap",
                    })
                tile_owner[tile_id] = robot_id
        return violations

    def _average_completion_seconds(self, completed: list[Order]) -> float:
        if not completed:
            return 0.0
        return sum((order.completion_tick or self.tick) - order.creation_tick for order in completed) * self.tick_seconds / len(completed)

    def _per_hour(self, count: int) -> float:
        hours = max(self.sim_time_s / 3600, 1 / 3600)
        return count / hours

    def _percentile(self, values: list[int], percentile: int) -> float:
        if not values:
            return 0
        index = min(len(values) - 1, max(0, math.ceil(percentile / 100 * len(values)) - 1))
        return values[index]

    def _emit(self, event_type: str, message: str, **payload: Any) -> None:
        event = {
            "run_id": self.options.run_id,
            "tick": self.tick,
            "sim_time_s": self.sim_time_s,
            "event_type": event_type,
            "message": message,
            "payload": payload,
        }
        self.events.append(event)
        self.recent_messages.append(message)


def tile_id_from_xy(x: int, y: int) -> str:
    return f"T_{x:02d}_{y:02d}"


def rect_tiles(origin_tile_id: str, width: int, depth: int) -> list[str]:
    x0, y0 = xy_from_tile_id(origin_tile_id)
    return [tile_id_from_xy(x0 + dx, y0 + dy) for dy in range(depth) for dx in range(width)]


def xy_from_tile_id(tile_id: str) -> tuple[int, int]:
    parts = tile_id.split("_")
    if len(parts) != 3 or parts[0] != "T":
        raise ValueError(f"Invalid tile id {tile_id}")
    return int(parts[1]), int(parts[2])


def difficulty_label(value: int) -> str:
    if value <= 1:
        return "easy"
    if value == 2:
        return "normal"
    if value == 3:
        return "hard"
    return "expert"


def material_from_sku(sku_id: str) -> str:
    sku = sku_id.lower()
    if "metal" in sku or "tool" in sku:
        return "metal"
    if "wood" in sku or "bulk" in sku:
        return "wood"
    return "cardboard"

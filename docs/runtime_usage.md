# Runtime Usage

This runtime is the executable core for the Warehouse Order Fulfillment Simulator.
It is not a UI, MuJoCo controller, or low-level robot control stack.

## Run Local Planner

```bash
python3 examples/run_warehouse_runtime.py --load medium --planner local --ticks 1800 --print-summary
```

Outputs are written to:

```text
submissions/warehouse_quadbot_atomic_demos/outputs/runtime_snapshot.json
submissions/warehouse_quadbot_atomic_demos/outputs/runtime_events.jsonl
submissions/warehouse_quadbot_atomic_demos/outputs/benchmark_metrics.json
```

The snapshot shape follows `submissions/warehouse_quadbot_atomic_demos/ui/UI_DESIGN_HANDOFF.md`.

## Load Profiles

The first runtime layout uses 9 fixed robots and three load profiles:

- `low`: 120 orders/hour
- `medium`: 300 orders/hour
- `high`: 540 orders/hour

SKU weight affects loaded movement speed. SKU difficulty affects pick and unload duration.


## Rack Footprint Blocking

Rack tiles are hard obstacles. The runtime blocks every tile listed in
`rack_modules[].footprint_tiles` plus any per-SKU `racks[].storage_tile_id` or
`racks[].footprint_tiles` values. A robot may stand on a rack `pick_tile_id`, but
it may not enter the rack footprint itself.

Snapshots expose the obstacle contract for UI/runtime integration:

```text
warehouse.blocked_tiles
warehouse.rack_tiles
shelves[].footprint_tiles
shelves[].blocks_robot
```

The pathfinder and movement commit both validate this rule, so even if a layout
is regenerated or a route is stale, the robot refuses blocked rack tiles and
replans instead of moving through the rack.

## Movement Lock Contract

Runtime movement is limited to N/S/E/W tile neighbors. Diagonal route steps are
rejected, logged as `route.invalid_step`, and replanned before movement commit.

A robot may move only after the scheduler grants an atomic source+destination
lock for that tick. If the destination is occupied, already claimed, blocked, or
would create a head-on swap, the robot enters `waiting_for_tile_lock`; it does
not move into that tile. Snapshots expose the contract for UI and database
agents:

```text
movement_locks.model
movement_locks.occupied_tiles
movement_locks.requested_moves
movement_locks.granted_moves
movement_locks.denied_moves
runtime.route_cardinality_violations
runtime.collision_violations
runtime.lock_overlap_violations
robots[].route_closed = false
robots[].route_cardinal
robots[].lock_tiles
```

For a valid run, all movement violation counters must be `0`.

## Time Scale

The simulator tick is one simulated second. UI playback may show `1x`, `10x`, or
`60x`, but planner checks are based on simulated time. The planner interval is
600 simulated seconds, matching the 10-minute planning cadence.

## AI Planner Interface

Default mode is local heuristic planning and requires no key.

Optional OpenAI planning is enabled only when all are true:

1. Runtime is started with `--planner openai`.
2. `OPENAI_API_KEY` is set in the environment.
3. `OPENAI_MODEL` is set in the environment.

Do not commit API keys. For hackathon judging, leave planner mode as `local` or
let judges inject their own `OPENAI_API_KEY` and `OPENAI_MODEL` environment values.
If the API call fails, the runtime automatically falls back to the local planner.

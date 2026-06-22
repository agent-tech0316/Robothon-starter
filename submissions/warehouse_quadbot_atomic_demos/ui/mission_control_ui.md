# Mission Control UI Specification

## Product Intent

This UI is a warehouse-order-optimization simulator. It is not a robotics-control
dashboard and should not feel like a robotics debugging tool.

The core benchmark is throughput. Every screen should make it clear that the
agentic workflow and skill graph control warehouse operations, while robots are
execution resources assigned by the scheduler.

Target feeling:

- Mission Control
- Operations Center
- Warehouse Management System

Avoid:

- Joint-level robot telemetry
- Low-level controller panels
- Physics-debug readouts as the primary screen
- Robot-centric hierarchy where the warehouse is secondary

## Primary User Story

An operator or judge opens the demo and immediately understands:

1. Orders enter the warehouse.
2. The agentic workflow decomposes them into operational tasks.
3. The skill graph selects executable skills such as pick, route, load, unload,
   handoff, and pack.
4. The runtime scheduler assigns robots as executors.
5. Throughput, wait time, deadlocks, and replanning are measured live.

## Information Priority

1. Throughput and order completion health
2. Warehouse map and congestion state
3. Active workflow / skill graph decisions
4. Order queue urgency
5. Robot execution state
6. MuJoCo atomic evidence as supporting proof, not the central dashboard

## Recommended Layout

Use a fixed 3840x2160 mission-control layout for 4K 16:9 capture:

- Top: Agentech title bar plus load, time scale, pause, next tick, reset, record,
  and compact throughput / queue / SLA badges.
- Left: Throughput Benchmark, Runtime State, Agentic Planner, and Queue Pressure.
- Center: Warehouse Map, largest panel, with overlay toggles and a readable
  Timeline / Scheduler Events strip below it.
- Right: Order Panel, Robot Panel, and secondary MuJoCo skill evidence.
- Far right: narrow detail rail for capture state, TPS, pending orders, replans,
  deadlocks, active skills, and planner state.
- Bottom: Skill Graph, SKU Classes, Runtime Zones, and Runtime Contract.

The warehouse map remains the main visual anchor, but throughput is the main KPI
anchor and runtime decisions should stay visible near it.

## Required Panels

### 1. Warehouse Map

Purpose:

Show operational state of the warehouse, not robot internals.

Must display:

- Tile-based warehouse
- Shelves
- Delivery zone
- Robots
- Robot routes
- Occupancy state

Recommended visual layers:

- Base tile grid
- Occupancy overlay
- Shelf blocks
- Delivery / packing / outbound zones
- Planned routes as dashed lines
- Active routes as solid bright lines
- Blocked / occupied tiles as yellow or red overlays
- Robot markers with compact labels

Robot labels should show only:

- Robot id
- Task state
- Assigned order if relevant

Do not show:

- Joint angles
- Actuator values
- Contact solver details
- Raw MuJoCo debug information

### 2. Robot Panel

Purpose:

Show executor availability and assignment, not robot engineering detail.

For each robot show:

- Robot id
- Status: idle, moving, loading, unloading, blocked, waiting
- Current order
- Current target
- Next target
- Carried SKU
- Carried weight

Recommended row layout:

```text
R-03 | MOVING | ORD-028 | target A2-07 -> PACK-1 | SKU-MED | 2.0kg
```

Status colors:

- idle: muted gray
- moving: cyan
- loading: yellow
- unloading: green
- blocked: red
- waiting: orange

### 3. Order Panel

Purpose:

Make queue pressure and priority obvious.

For each order show:

- Order id
- Priority
- Difficulty
- Weight
- Assigned robot
- Age
- Status

Waiting-time color coding:

- Green: fresh / within SLA
- Yellow: aging / needs attention
- Red: late / threatens throughput

Recommended order row:

```text
ORD-028 | P1 | hard | 4.0kg | R-03 | 01:42 | assigned
```

### 4. Throughput Panel

Purpose:

This is the core benchmark panel.

Display:

- Orders completed
- Throughput
- Active orders
- Pending orders
- Average completion time

Recommended additional derived fields:

- Completion rate trend
- SLA risk count
- Bottleneck lane
- Projected orders per hour

This panel should have strong visual priority in the left rail or top-left.

### 5. Runtime Panel

Purpose:

Make agentic workflow and skill graph control visible.

Display:

- Current workflow
- Active skills
- Deadlock count
- Replanning count
- Scheduler decisions

Recommended structure:

```text
Workflow: Batch Fulfillment
Active Skills: route_plan, shelf_pick, load, unload
Deadlocks: 2
Replans: 7
Latest Decision: reroute R-02 around occupied tile 5,8
```

This panel should include a visible chain:

```text
Mission -> Workflow -> Skill Graph -> Scheduler -> Robot Executor
```

### 6. Timeline Panel

Purpose:

Show live operational events and scheduler decisions.

Display:

- Live event stream

Example events:

- Robot 3 assigned Order 28
- Robot 2 entered Tile 5,8
- Order 19 completed
- Deadlock resolved
- Replanning triggered

Recommended event tags:

- assignment
- movement
- completion
- deadlock
- replan
- skill
- throughput

## Agentic Workflow Visibility

The UI must repeatedly reinforce:

- The workflow drives task decomposition.
- The skill graph defines executable capabilities.
- The scheduler chooses assignments and routes.
- Robots execute assigned tasks.

Suggested language:

- "Scheduler Decision"
- "Active Workflow"
- "Skill Graph Edge"
- "Executor Assignment"
- "Throughput Impact"

Avoid language:

- "Robot controller"
- "Motor status"
- "Joint telemetry"
- "Physics debug"
- "Manual robot command"

## Color System

Core operational colors:

- Green: completed, healthy, fresh order, available capacity
- Yellow: warning, aging order, loading, congestion risk
- Red: blocked, late order, deadlock, critical bottleneck
- Cyan: active route, moving robot, selected operational layer
- Gray: idle, inactive, unassigned

Throughput color rules:

- Green: throughput at or above target
- Yellow: throughput below target but recovering
- Red: throughput below target and queue age rising

Order waiting-time rules:

- Green: age < 60 seconds
- Yellow: 60 seconds <= age < 180 seconds
- Red: age >= 180 seconds

These thresholds can be tuned once the runtime data distribution is known.

## Interaction Model

Primary interactions:

- Pause / resume simulation
- Next tick
- Speed control: 1x, 4x, 10x
- Select order
- Select robot
- Select skill graph edge
- Toggle occupancy overlay
- Toggle routes overlay
- Inspect scheduler decision

Secondary interactions:

- Drag shelf layout only if demonstrating optimization scenarios
- Open MuJoCo evidence for an active skill
- Export recording

## Data Model Summary

### Robot

```json
{
  "id": "R-03",
  "status": "moving",
  "current_order": "ORD-028",
  "current_target": "A2-07",
  "next_target": "PACK-1",
  "carried_sku": "SKU-MED",
  "carried_weight_kg": 2.0,
  "tile": [5, 8],
  "route": [[2, 6], [3, 6], [4, 7]]
}
```

### Order

```json
{
  "id": "ORD-028",
  "priority": "P1",
  "difficulty": "hard",
  "weight_kg": 4.0,
  "assigned_robot": "R-03",
  "age_s": 102,
  "status": "assigned"
}
```

### Runtime

```json
{
  "workflow": "Batch Fulfillment",
  "active_skills": ["route_plan", "shelf_pick", "load", "unload"],
  "deadlock_count": 2,
  "replanning_count": 7,
  "scheduler_decisions": [
    "Reroute R-02 around occupied tile 5,8"
  ]
}
```

### Throughput

```json
{
  "orders_completed": 289,
  "throughput_per_hour": 342,
  "active_orders": 53,
  "pending_orders": 96,
  "average_completion_time_min": 18.6
}
```

## Submission Narrative

The UI should support this judging narrative:

> This submission optimizes warehouse order fulfillment. The agentic workflow
> decomposes incoming orders, the skill graph maps each workflow step to
> executable warehouse skills, and the scheduler continuously assigns robot
> executors to maximize throughput while resolving occupancy conflicts,
> deadlocks, and replanning events. MuJoCo videos validate representative atomic
> skills, but the benchmark is warehouse throughput.

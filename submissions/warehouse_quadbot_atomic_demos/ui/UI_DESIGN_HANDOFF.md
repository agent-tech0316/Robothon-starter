# UI Design Handoff

## Product Position

This UI is the presentation and runtime surface for a warehouse order-fulfillment
optimizer. It is not a low-level robot teleoperation panel.

The story it should tell during judging:

1. A warehouse mission releases many orders.
2. The system decomposes the mission into workflow steps.
3. Workflow edges map to an atomic skill graph.
4. The runtime assigns robots, shelves, lanes, handoffs, and packing work.
5. MuJoCo videos prove selected low-level atomic skills are physically plausible.

## Chosen Stack

- Static HTML for submission-friendly packaging.
- CSS for the game-like dashboard/HUD shell.
- Canvas 2D for the pseudo-3D isometric warehouse stage.
- Relative video and JSON paths for existing MuJoCo outputs.
- No npm, no bundler, no network dependency.

This keeps the UI lightweight enough for a hackathon PR while still supporting
continuous animation, drag interactions, numeric fluctuation, recording, and
runtime state replacement later.

## Screen Architecture

- Top bar: Agentech identity, load profile, time scale, pause, next tick, reset,
  canvas recording, and compact throughput / queue / SLA benchmark badges.
- Left rail: throughput benchmark, runtime state, agentic planner counters, and
  queue pressure. This is the performance and decision-control side of the UI.
- Center stage: isometric warehouse map, overlay toggles, shelves, robots,
  routes, zones, and timeline / scheduler events.
- Right rail: order table, robot executor table, and MuJoCo atomic skill
  evidence. Orders and robots are operational tables, not robot-debug cards.
- Thin rail: 4K capture state plus compact pending/replan/deadlock/skill/planner
  counters for video readability.
- Bottom console: skill graph assets, SKU classes, zones, and runtime data
  contract.

## Runtime Data Contract

The browser currently simulates state in `app.js`. A runtime agent can replace
that state with snapshots shaped like this:

```json
{
  "tick": 775,
  "sim_time_s": 9306,
  "load": "medium",
  "speed": 1,
  "planner_enabled": true,
  "orders": {
    "created_per_hr": 342,
    "completed_per_hr": 289,
    "active": 53,
    "pending": 96,
    "sla_risk": 8,
    "open": 53,
    "avg_fulfillment_min": 18.6
  },
  "order_rows": [
    {
      "id": "ORD-028",
      "priority": "P1",
      "difficulty": "hard",
      "weight_kg": 4.0,
      "assigned_robot": "Q-03",
      "age_s": 188,
      "status": "assigned"
    }
  ],
  "robots": [
    {
      "id": "Q-01",
      "x": 0.9,
      "y": 7.3,
      "status": "moving",
      "battery": 86,
      "carrying": false,
      "current_order": "ORD-017",
      "current_target": "DEPOT",
      "next_target": "A1-04",
      "carried_sku": null,
      "carried_weight_kg": null,
      "route": [[0.9, 7.3], [2.6, 6.0], [7.6, 6.8]]
    }
  ],
  "shelves": [
    { "id": "A1", "x": 2.1, "y": 1.2, "w": 1.1, "d": 2.2, "h": 1.35 }
  ],
  "events": [
    "Assigned shelf_pick to Q-03 near A2."
  ],
  "runtime": {
    "workflow": "Batch Fulfillment",
    "active_skills": ["route_plan", "shelf_pick", "handoff", "load"],
    "deadlocks": 2,
    "replans": 7,
    "latest_decision": "Reroute Q-06 around B2 buffer zone."
  },
  "skill_evidence": {
    "shelf_pick": {
      "video": "../outputs/shelf_pick.mp4",
      "trajectory": "../outputs/shelf_pick_trajectory.json",
      "success": true
    }
  }
}
```

Recommended integration path:

- Start with polling a local JSON snapshot written by Python.
- Move to WebSocket or server-sent events only if live demos need lower latency.
- Keep MuJoCo evidence as fixed relative assets under `outputs/`.

## Files

- `index.html`: layout and semantic screen regions.
- `styles.css`: visual language, responsive layout, HUD panels, asset console.
- `app.js`: canvas renderer, simulated runtime state, controls, dragging, recording.
- `README.md`: run instructions for judges and future agents.

## Design Notes

- The isometric warehouse is intentionally a high-level runtime map, not a MuJoCo
  render. MuJoCo remains the evidence layer for atomic skills.
- The color system uses cyan for routes/evidence, amber for active work, green for
  verified/healthy state, red for congestion or recording.
- Shelves are draggable to support future layout optimization demos.
- The bottom `Runtime Contract` panel is a UI placeholder for the next agent that
  connects optimizer output to the dashboard.

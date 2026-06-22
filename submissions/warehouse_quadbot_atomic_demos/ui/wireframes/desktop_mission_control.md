# Desktop Mission Control Wireframe

## Layout

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ AGENTECH / Agentic Warehouse Runtime                                         │
│ Load: Low Med High   Time: 1x 4x 10x   Pause  Next Tick  Reset  Record       │
│ Compact benchmark badges: THR / QUEUE / SLA                                  │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┬───────────────────────────────────┬─────────────────┬─────┐
│ THROUGHPUT           │ WAREHOUSE MAP                     │ ORDER PANEL     │ SIM │
│ Orders Completed     │ overlay toggles                    │ ORD-028  P1 RED │ TPS │
│ Throughput / hr      │ tile grid + shelves                │ ORD-019  P2 YEL │ ORD │
│ Active Orders        │ delivery / outbound zones          │ ORD-031  P3 GRN │ RPL │
│ Pending Orders       │ occupancy overlay                  │                 │ DLK │
│ Avg Completion Time  │ robot executor markers             │ priority/age    │ SKL │
│                      │ active and planned routes          │ status          │ RUN │
├──────────────────────┤                                   ├─────────────────┤     │
│ RUNTIME STATE        │                                   │ ROBOT PANEL     │     │
│ Sim time / planner   │                                   │ R-01 idle       │     │
│ Fleet / selected     │                                   │ R-02 moving     │     │
│ Mission -> Workflow  │                                   │ R-03 loading    │     │
├──────────────────────┤                                   ├─────────────────┤     │
│ AGENTIC PLANNER      │                                   │ MUJOCO EVIDENCE │     │
│ Workflow / skills    │                                   │ Shelf / Handoff │     │
│ Deadlocks / replans  │                                   │ Arm + Basket    │     │
│ Latest decision      │                                   │                 │     │
├──────────────────────┤                                   │                 │     │
│ QUEUE PRESSURE       │                                   │                 │     │
└──────────────────────┴───────────────────────────────────┴─────────────────┴─────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ CENTER TIMELINE / SCHEDULER EVENTS                                           │
│ [00:12] Robot 3 assigned Order 28                                            │
│ [00:15] Robot 2 entered Tile 5,8                                             │
│ [00:21] Deadlock resolved                                                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ BOTTOM CONSOLE                                                               │
│ Skill Graph | SKU Classes | Runtime Zones | Runtime Contract                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Priority Notes

- Throughput panel should be top-left because throughput is the benchmark.
- Warehouse map should be the largest panel because it explains the operation.
- Runtime panel should sit near throughput to show why performance changes.
- Order and robot panels should be tables, not decorative cards.
- Timeline should be full width and always readable.
- MuJoCo evidence should be available but visually secondary.

## Visual Weight

```text
Warehouse Map      40%
Throughput/Runtime 22%
Order/Robot Tables 24%
Timeline           10%
Evidence            4%
```

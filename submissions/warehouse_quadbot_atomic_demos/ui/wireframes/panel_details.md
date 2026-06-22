# Panel Details

## Warehouse Map

```text
┌──────────────────────────────────────────────────────┐
│ WAREHOUSE MAP     overlays: occupancy routes orders  │
│                                                      │
│  [Shelf A1]     R-03 -> ORD-028      [Shelf A2]      │
│       ╲            occupied tile         ╱           │
│        ╲ route_plan active route        ╱            │
│         ╲                                ╱           │
│          [PACK] ---- delivery zone ---- [OUTBOUND]   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

Map fields:

- Tile occupancy: free, occupied, reserved, blocked
- Shelf ids
- Delivery / pack / outbound zones
- Robot id labels
- Active route
- Planned route
- Selected order route highlight

## Robot Panel

```text
┌───────────────────────────────────────────────────────────────┐
│ ROBOTS                                                        │
│ ID    STATUS      ORDER    TARGET       NEXT       SKU  WEIGHT │
│ R-01  idle        -        DEPOT        A1-04      -    -      │
│ R-02  moving      ORD-019  TILE 5,8     PACK-1     LGT  0.8kg  │
│ R-03  loading     ORD-028  A2-07        PACK-2     HVY  4.0kg  │
│ R-04  blocked     ORD-031  TILE 4,7     A3-02      MED  2.0kg  │
└───────────────────────────────────────────────────────────────┘
```

Statuses:

- idle
- moving
- loading
- unloading
- blocked
- waiting

## Order Panel

```text
┌───────────────────────────────────────────────────────────────┐
│ ORDERS                                                        │
│ ID       PRI  DIFF  WT     ROBOT  AGE    STATUS               │
│ ORD-028  P1   hard  4.0kg  R-03   03:12  assigned    RED       │
│ ORD-019  P2   med   2.0kg  R-02   01:22  moving      YELLOW    │
│ ORD-031  P3   easy  0.8kg  -      00:32  pending     GREEN     │
└───────────────────────────────────────────────────────────────┘
```

Age color:

- Green: fresh
- Yellow: aging
- Red: late

## Throughput Panel

```text
┌────────────────────────────┐
│ THROUGHPUT                 │
│ Orders Completed     289   │
│ Throughput           342/h │
│ Active Orders        53    │
│ Pending Orders       96    │
│ Avg Completion Time  18.6m │
└────────────────────────────┘
```

## Runtime Panel

```text
┌──────────────────────────────────────┐
│ RUNTIME                              │
│ Workflow       Batch Fulfillment     │
│ Active Skills  route_plan, pick      │
│ Deadlocks      2                     │
│ Replans        7                     │
│ Decisions      reroute R-02          │
└──────────────────────────────────────┘
```

## Timeline Panel

```text
┌──────────────────────────────────────────────────────────────┐
│ TIMELINE                                                     │
│ 00:12 assignment  Robot 3 assigned Order 28                  │
│ 00:15 movement    Robot 2 entered Tile 5,8                   │
│ 00:21 deadlock    Deadlock resolved                          │
│ 00:24 replan      Replanning triggered                       │
│ 00:29 complete    Order 19 completed                         │
└──────────────────────────────────────────────────────────────┘
```

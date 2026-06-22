# Component Tree

```text
MissionControlApp
├── TopCommandBar
│   ├── ProjectIdentity
│   ├── SimulationControls
│   │   ├── LoadSelector
│   │   ├── SpeedSelector
│   │   ├── PauseResumeButton
│   │   ├── NextTickButton
│   │   ├── ResetButton
│   │   └── RecordButton
│   └── BenchmarkSummary
│       ├── ThroughputBadge
│       ├── QueueHealthBadge
│       └── SlaRiskBadge
│
├── MainOperationsGrid
│   ├── LeftRail
│   │   ├── ThroughputPanel
│   │   │   ├── OrdersCompletedMetric
│   │   │   ├── ThroughputMetric
│   │   │   ├── ActiveOrdersMetric
│   │   │   ├── PendingOrdersMetric
│   │   │   └── AverageCompletionTimeMetric
│   │   ├── RuntimeStatePanel
│   │   │   ├── SimClock
│   │   │   ├── PlannerToggle
│   │   │   ├── FleetCount
│   │   │   ├── SelectedShelf
│   │   │   └── WorkflowChain
│   │   ├── AgenticPlannerPanel
│   │       ├── WorkflowStatus
│   │       ├── ActiveSkillsList
│   │       ├── DeadlockCounter
│   │       ├── ReplanningCounter
│   │       └── SchedulerDecisionList
│   │   └── QueuePressurePanel
│   │       ├── PriorityLaneMeter
│   │       ├── TransferLaneMeter
│   │       └── PackLaneMeter
│   │
│   ├── CenterStage
│   │   ├── WarehouseMapPanel
│   │   │   ├── TileGridLayer
│   │   │   ├── OccupancyLayer
│   │   │   ├── ShelfLayer
│   │   │   ├── DeliveryZoneLayer
│   │   │   ├── RouteLayer
│   │   │   └── RobotExecutorLayer
│   │   └── MapOverlayControls
│   │       ├── OccupancyToggle
│   │       ├── RoutesToggle
│   │       ├── OrdersToggle
│   │       └── CongestionToggle
│   │   └── TimelinePanel
│   │       ├── TimelineHeader
│   │       └── SchedulerEventStream
│   │
│   └── RightRail
│       ├── OrderPanel
│       │   ├── OrderFilterTabs
│       │   ├── OrderTable
│       │   │   └── OrderRow
│       │   │       ├── OrderId
│       │   │       ├── Priority
│       │   │       ├── Difficulty
│       │   │       ├── Weight
│       │   │       ├── AssignedRobot
│       │   │       ├── Age
│       │   │       └── Status
│       │   └── AgingLegend
│       │
│       └── RobotPanel
│           ├── RobotFilterTabs
│           ├── RobotTable
│           │   └── RobotRow
│           │       ├── RobotId
│           │       ├── Status
│           │       ├── CurrentOrder
│           │       ├── CurrentTarget
│           │       ├── NextTarget
│           │       ├── CarriedSku
│           │       └── CarriedWeight
│           └── StatusLegend
│       └── MujocoEvidencePanel
│           ├── ShelfPickVideo
│           ├── HandoffVideo
│           └── ArmBasketVideo
│
├── ThinRail
│   ├── CaptureResolution
│   ├── TargetTps
│   ├── PendingOrders
│   ├── ReplanCounter
│   ├── DeadlockCounter
│   ├── ActiveSkillCounter
│   └── PlannerState
│
└── BottomConsole
    ├── SkillGraphEvidence
    │   ├── SkillEdgeCard
    │   └── SkillStatusBadge
    ├── SkuClassPanel
    ├── RuntimeZonePanel
    └── RuntimeContractPanel
```

## State Ownership

```text
MissionControlApp
├── owns simulation clock, speed, pause state
├── owns selected order / selected robot / selected skill
├── receives throughput snapshots
├── receives robot snapshots
├── receives order snapshots
├── receives runtime decisions
└── receives event stream
```

## Design Rule

The map, order table, robot table, runtime panel, and timeline all point back to
the same idea: the agentic workflow and skill graph schedule warehouse work, and
robots are the executors.

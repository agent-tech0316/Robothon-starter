# Warehouse Database Diagrams

这份文档只放数据库关联图，方便快速看清表之间的关系。完整字段定义见 `docs/database_design.md`。

## 1. 总体关系图

```mermaid
erDiagram
    SIMULATION_RUNS ||--o{ ORDERS : generates
    SIMULATION_RUNS ||--o{ ROBOTS : operates
    SIMULATION_RUNS ||--o{ TASKS : schedules
    SIMULATION_RUNS ||--o{ ROUTES : plans
    SIMULATION_RUNS ||--o{ TILE_LOCKS : owns
    SIMULATION_RUNS ||--o{ EVENTS : logs

    WAREHOUSES ||--o{ TILES : contains
    WAREHOUSES ||--o{ RACKS : contains
    WAREHOUSES ||--o{ OUTBOUND_CONVEYORS : has
    WAREHOUSES ||--o{ OUTBOUND_DOCKS : has

    RACKS ||--o{ RACK_INVENTORY : stores
    SKUS ||--o{ RACK_INVENTORY : stocked_as
    SKUS ||--o{ ORDERS : requested_by

    ORDERS ||--o{ INVENTORY_RESERVATIONS : reserves
    ORDERS ||--o{ PACKAGES : creates
    ORDERS ||--o{ TASKS : decomposes_into
    ORDERS ||--o{ ORDER_OUTBOUND_ASSIGNMENTS : ships_via

    ROBOTS ||--o{ TASKS : executes
    ROBOTS ||--o{ ROUTES : follows
    ROBOTS ||--o{ TILE_LOCKS : holds
    ROBOTS ||--o{ HANDOFFS : participates

    ROUTES ||--o{ ROUTE_STEPS : includes
    ROUTE_STEPS ||--o{ TILE_LOCKS : requires

    PACKAGES ||--o{ HANDOFFS : transferred_by
    PACKAGES }o--|| OUTBOUND_CONVEYORS : unloaded_to
```

## 2. Warehouse 地图与障碍物

```mermaid
erDiagram
    WAREHOUSES ||--o{ TILES : contains
    WAREHOUSES ||--o{ TILE_NEIGHBORS : defines_grid_edges

    TILES ||--o{ TILE_NEIGHBORS : from_tile
    TILES ||--o{ TILE_NEIGHBORS : to_tile
    TILES ||--o{ TILE_LOCKS : locked_by
    TILES ||--o{ ROUTE_STEPS : used_by

    TILES {
        string tile_id PK
        int x
        int y
        enum tile_type
        bool is_available_floor
        bool blocks_robot
        enum collision_class
    }

    TILE_NEIGHBORS {
        string from_tile_id FK
        string to_tile_id FK
        enum direction "N/S/E/W only"
        bool is_enabled
    }
```

关键规则：

- visual 的 isometric 45 度移动来自 `N/S/E/W` 四向网格投影。
- robot 只能进入 `is_available_floor = true` 的 tile。
- rack、conveyor、dock、wall、blocked tile 都是 `blocks_robot = true`。
- `tile_neighbors` 不能连到不可走 tile。

## 3. Rack、Pick Point、SKU、库存

```mermaid
erDiagram
    WAREHOUSES ||--o{ RACKS : contains
    RACKS ||--o{ RACK_TILES : occupies
    RACKS ||--o{ RACK_PICK_POINTS : exposes
    RACKS ||--o{ RACK_INVENTORY : stores

    RACK_TILES ||--o{ RACK_PICK_POINTS : side_pick_tile
    TILES ||--o{ RACK_TILES : occupied_by_rack
    TILES ||--o{ RACK_PICK_POINTS : robot_stands_on

    SKUS ||--o{ RACK_INVENTORY : stocked_as
    RACK_INVENTORY ||--o{ INVENTORY_RESERVATIONS : reserved_by_orders

    RACKS {
        string rack_id PK
        string warehouse_id FK
        int footprint_width_tiles "1"
        int footprint_length_tiles "2 or 3"
        enum orientation
    }

    SKUS {
        string sku_id PK
        enum weight_class
        enum package_visual_type
        enum handling_difficulty
    }

    RACK_INVENTORY {
        string rack_inventory_id PK
        int initial_quantity
        int available_quantity
        int reserved_quantity
        int picked_quantity
        int shipped_quantity
    }
```

## 4. 订单、锁货、Package

```mermaid
erDiagram
    ORDER_GENERATION_PROFILES ||--o{ ORDERS : creates
    SKUS ||--o{ ORDERS : requested_sku
    ORDERS ||--o{ INVENTORY_RESERVATIONS : locks_inventory
    RACK_INVENTORY ||--o{ INVENTORY_RESERVATIONS : locked_from
    INVENTORY_RESERVATIONS ||--o{ PACKAGES : becomes_package
    ORDERS ||--o{ PACKAGES : owns

    ORDERS {
        string order_id PK
        bigint order_sequence
        string sku_id FK
        int quantity
        int priority
        int deadline_tick
        enum status
    }

    INVENTORY_RESERVATIONS {
        string reservation_id PK
        string order_id FK
        string rack_inventory_id FK
        int quantity
        enum status
    }

    PACKAGES {
        string package_id PK
        string order_id FK
        string sku_id FK
        enum current_holder_type
        string current_holder_id
        enum status
    }
```

## 5. Robot、Task、Route、Tile Lock

```mermaid
erDiagram
    ROBOT_TYPES ||--o{ ROBOTS : configures
    ORDERS ||--o{ TASKS : creates
    ROBOTS ||--o{ TASKS : executes
    TASKS ||--o{ ROUTES : planned_as
    ROUTES ||--o{ ROUTE_STEPS : contains
    ROUTE_STEPS ||--o{ TILE_LOCKS : requires
    ROBOTS ||--o{ TILE_LOCKS : holds
    ROBOTS ||--o{ WAIT_STATES : waits_in

    ROBOTS {
        string robot_id PK
        string current_tile_id FK
        enum status
        string current_lock_id FK
        string next_lock_id FK
        enum heading
        float move_progress
    }

    ROUTE_STEPS {
        string route_step_id PK
        string from_tile_id FK
        string to_tile_id FK
        enum direction "N/S/E/W"
        int enter_tick
        int exit_tick
    }

    TILE_LOCKS {
        string lock_id PK
        string tile_id FK
        string robot_id FK
        enum lock_type "current_tile/next_tile"
        int start_tick
        int end_tick
        enum status
    }
```

核心关系：

- robot 当前格对应 `current_tile` lock。
- robot 下一格对应 `next_tile` lock。
- 下一格锁不到，就写 `wait_states`。
- `route_steps.direction` 只允许 `N/S/E/W`。

## 6. Robot Handoff

```mermaid
erDiagram
    ORDERS ||--o{ HANDOFFS : may_require
    PACKAGES ||--o{ HANDOFFS : transferred_by
    ROBOTS ||--o{ HANDOFFS : sender
    ROBOTS ||--o{ HANDOFFS : receiver
    TILES ||--o{ HANDOFFS : sender_tile
    TILES ||--o{ HANDOFFS : receiver_tile

    HANDOFFS {
        string handoff_id PK
        string sender_robot_id FK
        string receiver_robot_id FK
        string sender_tile_id FK
        string receiver_tile_id FK
        enum handling_difficulty
        enum status
    }
```

约束：

- `sender_tile_id` 和 `receiver_tile_id` 必须是 `N/S/E/W` 相邻 tile。
- package 同一时间只能在 sender、receiver、conveyor、shipped 之一。

## 7. 出口履带、Dock、车辆

```mermaid
erDiagram
    WAREHOUSES ||--o{ OUTBOUND_CONVEYORS : has
    WAREHOUSES ||--o{ OUTBOUND_DOCKS : has
    OUTBOUND_DOCKS ||--o{ OUTBOUND_CONVEYORS : feeds
    OUTBOUND_DOCKS ||--o{ TRUCK_SCHEDULES : schedules
    TRUCK_SCHEDULES ||--o{ TRUCK_VISITS : produces
    ORDERS ||--o{ ORDER_OUTBOUND_ASSIGNMENTS : assigned_to_outbound
    OUTBOUND_CONVEYORS ||--o{ ORDER_OUTBOUND_ASSIGNMENTS : receives
    TRUCK_VISITS ||--o{ ORDER_OUTBOUND_ASSIGNMENTS : loads

    OUTBOUND_CONVEYORS {
        string conveyor_id PK
        string conveyor_tile_id FK
        string dropoff_tile_id FK
        enum status
    }

    TRUCK_SCHEDULES {
        string schedule_id PK
        int frequency_minutes
        int first_arrival_tick
        int loading_window_ticks
        int capacity_orders
    }

    TRUCK_VISITS {
        string truck_visit_id PK
        int planned_arrival_tick
        int planned_departure_tick
        int loaded_orders
        enum status
    }
```

关键规则：

- `conveyor_tile_id` 是履带本体，不可走。
- `dropoff_tile_id` 是机器人站立卸货的 available floor tile。
- order 在 dropoff tile 完成卸货后，warehouse 履约可记为 completed。

## 8. 最小实现关系

```mermaid
flowchart LR
    A["order_generation_profiles"] --> B["orders"]
    B --> C["inventory_reservations"]
    C --> D["rack_inventory"]
    D --> E["packages"]
    B --> F["tasks"]
    F --> G["routes"]
    G --> H["route_steps"]
    H --> I["tile_locks"]
    I --> J["robots"]
    E --> K["outbound_conveyors"]
    K --> L["orders.completed"]
```

第一版只要这条链路跑通，就能支持订单生成、锁货、取货、走路锁格、卸到出口、计算 throughput。

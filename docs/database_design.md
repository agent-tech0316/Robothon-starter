# Warehouse Outbound Fulfillment Simulator Database Design

## 1. 设计范围

这个数据库服务于一个只出库、不入库的仓储订单履约优化模拟器。系统持续生成订单，订单绑定仓库内已有 SKU；机器人从 rack 侧边取货，必要时在相邻 tile 上交接货物，最后把货送到出口履带或出货点。订单送达出口并完成卸载后，才算仓库履约完成。

数据库只记录仓库运行状态和事件，不把 throughput、congestion 这类可派生结果强行写死。核心 KPI 可以通过订单、机器人、tile lock、rack inventory 和事件日志计算出来。

核心边界：

```text
订单生成 -> 库存锁定 -> 机器人调度 -> 路径锁格 -> rack 取货 -> 可选机器人交接 -> 出口履带卸货 -> 订单完成
```

核心约束：

```text
1. 仓库是离散 tile map。
2. 机器人只能正东、正西、正南、正北移动，不能斜向移动。
3. 机器人所在 tile 必须锁定。
4. 机器人准备进入的下一格相邻 tile 也必须提前锁定。
5. 一个 tile 在同一 tick 区间内不能被多个机器人占用或作为下一步目标锁定。
6. 机器人取货必须站在 rack 的可用 pick point tile。
7. 两个机器人交接货物时，两个机器人必须位于相邻 tile。
8. 订单完成点是出口履带/出货点，不是 rack，也不是机器人取到货的时刻。
```

## 2. 逻辑分区

| 分区 | 作用 | 主要表 |
|---|---|---|
| `scenario` | 仓库静态地图、rack、出口、订单生成规则 | `warehouses`, `tiles`, `tile_neighbors`, `racks`, `rack_tiles`, `rack_pick_points`, `outbound_conveyors`, `order_generation_profiles` |
| `catalog` | SKU 与货物属性 | `skus`, `rack_inventory` |
| `fulfillment` | 订单、库存锁定、任务、包裹流转 | `orders`, `inventory_reservations`, `packages`, `tasks`, `handoffs` |
| `fleet` | 机器人配置与实时状态 | `robot_types`, `robots`, `robot_state_history` |
| `scheduler` | 路径、当前格锁、下一格锁、等待、避障 | `routes`, `route_steps`, `tile_locks`, `wait_states` |
| `outbound` | 出口履带、dock、车辆班次、车辆到访 | `outbound_docks`, `truck_schedules`, `truck_visits`, `order_outbound_assignments` |
| `runtime` | 仿真回合、事件日志、消息 | `simulation_runs`, `events`, `agent_messages` |
| `analytics` | 可选缓存指标 | `metric_snapshots` |

## 3. 仿真回合与订单生成

### `simulation_runs`

一轮仿真。所有订单、机器人状态、路线、事件都必须挂到某个 run。

| 字段 | 类型 | 说明 |
|---|---|---|
| `run_id` | string PK | 仿真回合 ID |
| `warehouse_id` | FK | 使用哪个仓库地图 |
| `seed` | integer | 随机种子，保证可复现 |
| `tick_duration_ms` | integer | 一个仿真 tick 对应多少毫秒 |
| `time_acceleration` | decimal | 加速倍率，例如仿真 1 分钟等于现实 1 小时 |
| `started_tick` | integer | 一般为 0 |
| `current_tick` | integer | 当前 tick |
| `planned_end_tick` | integer | 计划结束 tick |
| `status` | enum | `created`, `running`, `paused`, `completed`, `failed`, `aborted` |

写入方：Simulation Runtime  
更新频率：每 tick 更新 `current_tick`，其他字段低频更新

### `order_generation_profiles`

订单生成规则。订单不是手写输入，而是根据该 profile 自动生成。

| 字段 | 类型 | 说明 |
|---|---|---|
| `profile_id` | string PK | 生成规则 ID |
| `run_id` | FK | 所属仿真 |
| `orders_per_minute` | decimal | 每仿真分钟生成多少订单 |
| `burst_factor` | decimal | 是否允许高峰波动 |
| `sku_distribution` | JSON | SKU 抽样权重 |
| `quantity_distribution` | JSON | 数量分布 |
| `priority_distribution` | JSON | 优先级分布 |
| `deadline_distribution` | JSON | deadline 相对 creation_tick 的分布 |
| `random_seed` | integer | 订单生成随机种子 |
| `status` | enum | `active`, `paused`, `completed` |

写入方：Order Generator  
更新频率：仿真开始时创建，运行中低频调整

### 订单 ID 策略

订单 ID 必须用长字符串，不使用短整数主键。推荐：

```text
order_id = UUIDv7 或 ULID
```

同时保留 run 内递增号：

```text
order_sequence
```

原因：

- 加速仿真下订单量可能远高于现实时间。
- 需要支持连续模拟一天或多天。
- `order_id` 用于全局唯一，`order_sequence` 用于排序和 debug。

建议约束：

```sql
unique(order_id)
unique(run_id, order_sequence)
```

## 4. Warehouse 地图

### `warehouses`

仓库静态配置。

| 字段 | 类型 | 说明 |
|---|---|---|
| `warehouse_id` | string PK | 仓库 ID |
| `name` | string | 仓库名称 |
| `width_tiles` | integer | X 方向 tile 数 |
| `height_tiles` | integer | Y 方向 tile 数 |
| `tile_size_m` | decimal | 显示和距离换算用 |
| `expected_rack_count_min` | integer | 通常为 8 |
| `expected_rack_count_max` | integer | 通常为 16 |
| `movement_model` | enum | 固定为 `four_direction_grid` |
| `lock_model` | enum | 固定为 `current_and_next_tile` |
| `visual_projection` | enum | `isometric`，四向移动在画面上表现为 45 度方向 |
| `status` | enum | `draft`, `active`, `retired` |

写入方：Scenario Loader  
更新频率：静态

### `tiles`

离散地砖，是机器人移动、锁格、可视化地图的基础。

| 字段 | 类型 | 说明 |
|---|---|---|
| `tile_id` | string PK | tile ID |
| `warehouse_id` | FK | 所属仓库 |
| `x` | integer | X 坐标 |
| `y` | integer | Y 坐标 |
| `tile_type` | enum | `floor`, `rack_occupied`, `pick_point`, `conveyor`, `dock`, `wall`, `blocked`, `charger` |
| `is_available_floor` | boolean | 是否是机器人可站立、可行走的地面 tile；visual/pathfinding 以这个为准 |
| `is_traversable` | boolean | 兼容字段，应与 `is_available_floor` 保持一致 |
| `blocks_robot` | boolean | 是否是机器人碰撞阻挡物 |
| `collision_class` | enum | `available_floor`, `rack_collision`, `conveyor_collision`, `dock_collision`, `wall_collision`, `temporary_blocked`, `charger_floor` |
| `is_pick_point` | boolean | 是否是 rack 取货点 |
| `is_outbound_point` | boolean | 是否是出口履带卸货点 |
| `base_travel_cost` | decimal | 路径搜索基础成本 |
| `current_robot_id` | FK nullable | 当前占用机器人缓存 |
| `current_lock_id` | FK nullable | 当前 tile lock 缓存 |

约束：

```sql
unique(warehouse_id, x, y)
```

tile 类型规则：

| `tile_type` | `is_available_floor` | 说明 |
|---|---:|---|
| `floor` | true | 普通可行走地面 |
| `pick_point` | true | rack 侧边可站立取货点 |
| `charger` | true | 可站立充电点，如果启用电量逻辑 |
| `rack_occupied` | false | rack 本体占用，不可进入 |
| `conveyor` | false | 出口履带本体，不可进入 |
| `dock` | false | 车辆/dock 本体，不可进入 |
| `wall` | false | 墙体，不可进入 |
| `blocked` | false | 临时或静态阻挡，不可进入 |

visual 和路径规划都应该只把 `is_available_floor = true` 的 tile 当成机器人可移动地面。isometric 渲染时，机器人依然按 grid 的 `N/S/E/W` 运动；画面上看起来是 45 度斜向，但数据层不能生成斜向邻接边。

写入方：Scenario Loader 写静态字段；Robot Runtime 写占用缓存  
更新频率：静态字段不变；占用缓存每移动 step 更新

### `tile_neighbors`

明确四向连接关系，禁止斜向移动。`from_tile_id` 和 `to_tile_id` 都必须是 `is_available_floor = true`，不能连接到 rack、出口履带、dock、墙体或 blocked tile。

| 字段 | 类型 | 说明 |
|---|---|---|
| `neighbor_id` | string PK | 关系 ID |
| `warehouse_id` | FK | 仓库 |
| `from_tile_id` | FK | 起点 tile |
| `to_tile_id` | FK | 终点 tile |
| `direction` | enum | `N`, `S`, `E`, `W` |
| `is_enabled` | boolean | 是否可通行 |
| `travel_cost` | decimal | 连接成本 |

约束：

```sql
unique(warehouse_id, from_tile_id, to_tile_id)
direction in ('N', 'S', 'E', 'W')
from_tile_id.is_available_floor = true
to_tile_id.is_available_floor = true
```

写入方：Scenario Loader  
更新频率：静态，除非模拟临时封路

## 5. Rack 与 SKU 库存

### `racks`

rack 属于 warehouse。每个 rack 占地通常是 `1x2` 或 `1x3` tile。rack 本身不可被机器人站上去，机器人只能站在侧边 pick point 取货。

| 字段 | 类型 | 说明 |
|---|---|---|
| `rack_id` | string PK | rack ID |
| `warehouse_id` | FK | 所属仓库 |
| `name` | string | rack 名称 |
| `anchor_tile_id` | FK | rack footprint 的锚点 tile |
| `footprint_width_tiles` | integer | 固定为 1 |
| `footprint_length_tiles` | integer | 2 或 3 |
| `orientation` | enum | `N`, `S`, `E`, `W`，表示 rack 长轴方向 |
| `status` | enum | `active`, `blocked`, `empty`, `maintenance` |

约束：

```sql
footprint_width_tiles = 1
footprint_length_tiles in (2, 3)
```

写入方：Scenario Loader  
更新频率：静态，库存清空后可更新 `status`

### `rack_tiles`

rack 实际占用哪些 tile。

| 字段 | 类型 | 说明 |
|---|---|---|
| `rack_tile_id` | string PK | rack-tile 关系 ID |
| `rack_id` | FK | rack |
| `tile_id` | FK | 被 rack 占用的 tile |
| `segment_index` | integer | rack 长轴上的第几个 segment |

约束：

```sql
unique(rack_id, tile_id)
```

写入方：Scenario Loader  
更新频率：静态

### `rack_pick_points`

rack 侧边可取货点。`1x2` rack 理论上有 4 个侧边 pick point，`1x3` rack 理论上有 6 个侧边 pick point。靠墙或被阻挡的一侧可以标记为不可用。

| 字段 | 类型 | 说明 |
|---|---|---|
| `pick_point_id` | string PK | pick point ID |
| `rack_id` | FK | 所属 rack |
| `rack_tile_id` | FK | 对应 rack 的某个 segment |
| `tile_id` | FK | 机器人需要站立的 tile |
| `side` | enum | `left`, `right`，相对 rack 长轴 |
| `is_available` | boolean | 是否可用 |
| `blocked_reason` | enum nullable | `wall`, `blocked_tile`, `maintenance`, `none` |

约束：

```sql
unique(rack_id, rack_tile_id, side)
```

写入方：Scenario Loader；Traffic Controller 可临时关闭  
更新频率：静态或低频

### `skus`

SKU 是货物类型，不记录客户信息。

| 字段 | 类型 | 说明 |
|---|---|---|
| `sku_id` | string PK | SKU ID |
| `name` | string | SKU 名称 |
| `weight_class` | enum | `light`, `medium`, `heavy` |
| `package_visual_type` | enum | `cardboard_box`, `wooden_crate`, `metal_crate` |
| `unit_weight` | decimal | 单件重量 |
| `unit_volume` | decimal | 单件体积 |
| `handling_difficulty` | enum | `easy`, `medium`, `hard` |
| `pick_base_ticks` | integer | 基础取货耗时 |
| `transfer_base_ticks` | integer | 基础交接耗时 |
| `unload_base_ticks` | integer | 基础卸载耗时 |
| `status` | enum | `active`, `inactive` |

规则：

- `weight_class` 影响机器人移动速度和可视化外观。
- `handling_difficulty` 影响取货、交接、卸货耗时。
- 传递难度不必和重量正相关，应由 SKU 随机生成或配置。

写入方：SKU Catalog Loader  
更新频率：静态

### `rack_inventory`

只出库场景下，库存只会减少或从 available 变 reserved/picked/shipped，不会补货。

| 字段 | 类型 | 说明 |
|---|---|---|
| `rack_inventory_id` | string PK | 库存记录 ID |
| `warehouse_id` | FK | 仓库 |
| `rack_id` | FK | rack |
| `sku_id` | FK | SKU |
| `pick_point_id` | FK nullable | 推荐取货点 |
| `initial_quantity` | integer | 初始数量 |
| `available_quantity` | integer | 可分配数量 |
| `reserved_quantity` | integer | 已被订单锁定数量 |
| `picked_quantity` | integer | 已从 rack 取走数量 |
| `shipped_quantity` | integer | 已完成出库数量 |
| `last_updated_tick` | integer | 最后更新时间 |

约束：

```sql
available_quantity >= 0
reserved_quantity >= 0
picked_quantity >= 0
shipped_quantity >= 0
available + reserved + picked + shipped <= initial_quantity
```

写入方：Inventory Manager  
更新频率：订单锁货、取货、卸货时更新

## 6. Orders

### `orders`

订单只记录仓库履约需要的信息，不记录客户是谁。

| 字段 | 类型 | 说明 |
|---|---|---|
| `order_id` | string PK | 长 ID，推荐 ULID/UUIDv7 |
| `run_id` | FK | 所属 run |
| `order_sequence` | bigint | run 内递增号 |
| `generation_profile_id` | FK | 由哪个生成规则产生 |
| `sku_id` | FK | 订单目标 SKU |
| `quantity` | integer | 数量 |
| `priority` | integer | 优先级，越高越急 |
| `deadline_tick` | integer | 必须送达出口前的 tick |
| `target_conveyor_id` | FK nullable | 指定出口履带；为空则由调度器选择 |
| `assigned_robot_id` | FK nullable | 当前主机器人 |
| `assigned_task_id` | FK nullable | 当前任务 |
| `creation_tick` | integer | 创建 tick |
| `inventory_reserved_tick` | integer nullable | 库存锁定 tick |
| `assignment_tick` | integer nullable | 分配 tick |
| `picked_tick` | integer nullable | 从 rack 取下 tick |
| `unloaded_tick` | integer nullable | 在出口卸载 tick |
| `completion_tick` | integer nullable | 完成 tick |
| `status` | enum | 见下方生命周期 |
| `failure_reason` | string nullable | 失败原因 |

订单状态建议：

```text
generated
pending_inventory
inventory_reserved
robot_assigned
navigating_to_rack
picking
in_transit
waiting_handoff
handoff
navigating_to_conveyor
unloading_at_conveyor
completed
failed
cancelled
```

约束：

```sql
unique(order_id)
unique(run_id, order_sequence)
quantity > 0
deadline_tick > creation_tick
```

写入方：Order Generator, Inventory Manager, Scheduler, Robot Runtime  
更新频率：订单生命周期事件驱动

### `inventory_reservations`

订单锁货记录。只出库时，这张表很重要，因为一旦锁定，其他订单不能再拿同一份库存。

| 字段 | 类型 | 说明 |
|---|---|---|
| `reservation_id` | string PK | 库存锁定 ID |
| `run_id` | FK | run |
| `order_id` | FK | 订单 |
| `rack_inventory_id` | FK | 锁定哪份库存 |
| `sku_id` | FK | SKU |
| `quantity` | integer | 锁定数量 |
| `reserved_tick` | integer | 锁定 tick |
| `released_tick` | integer nullable | 释放 tick |
| `status` | enum | `reserved`, `picked`, `shipped`, `released`, `failed` |

写入方：Inventory Manager  
更新频率：订单锁货、失败释放、取货、出货

### `packages`

订单执行时产生的可搬运货物对象。一个订单可以直接用一个 package，也可以多个 package。

| 字段 | 类型 | 说明 |
|---|---|---|
| `package_id` | string PK | package ID |
| `run_id` | FK | run |
| `order_id` | FK | 所属订单 |
| `sku_id` | FK | SKU |
| `quantity` | integer | 数量 |
| `weight_class` | enum | 从 SKU 复制，方便可视化 |
| `handling_difficulty` | enum | 从 SKU 复制 |
| `current_holder_type` | enum | `rack`, `robot`, `conveyor`, `shipped`, `lost` |
| `current_holder_id` | string | rack_id / robot_id / conveyor_id 等 |
| `current_tile_id` | FK nullable | 当前所在 tile |
| `status` | enum | `reserved_at_rack`, `picked`, `carried`, `in_handoff`, `unloaded`, `shipped`, `lost` |

写入方：Inventory Manager, Robot Runtime  
更新频率：取货、交接、卸货时更新

## 7. Robots

### `robot_types`

机器人类型配置，定义速度和搬运参数。

| 字段 | 类型 | 说明 |
|---|---|---|
| `robot_type_id` | string PK | 类型 ID |
| `name` | string | 类型名称 |
| `base_move_ticks_per_tile` | integer | 空载每格耗时 |
| `max_payload_weight` | decimal | 最大载重 |
| `load_speed_penalty` | decimal | 负载对速度的惩罚系数 |
| `turn_penalty_ticks` | integer | 转向额外耗时，可选 |
| `pick_skill_level` | integer | 取货能力 |
| `handoff_skill_level` | integer | 交接能力 |
| `unload_skill_level` | integer | 卸货能力 |

写入方：Scenario Loader  
更新频率：静态

### `robots`

机器人实时状态。它不是底层控制对象，而是仓库执行资源。

| 字段 | 类型 | 说明 |
|---|---|---|
| `robot_id` | string PK | robot ID |
| `run_id` | FK | run |
| `robot_type_id` | FK | 类型 |
| `current_tile_id` | FK | 当前 tile |
| `status` | enum | 见下方状态 |
| `assigned_order_id` | FK nullable | 当前订单 |
| `assigned_task_id` | FK nullable | 当前任务 |
| `active_route_id` | FK nullable | 当前路线 |
| `target_tile_id` | FK nullable | 当前目标 |
| `next_tile_id` | FK nullable | 下一步目标 |
| `current_lock_id` | FK nullable | 当前 tile 锁 |
| `next_lock_id` | FK nullable | 下一格锁 |
| `heading` | enum nullable | `N`, `S`, `E`, `W`，用于 visual 朝向；不允许斜向 |
| `move_progress` | decimal | 当前 step 的进度，0 到 1，用于可视化插值 |
| `carried_package_id` | FK nullable | 正在携带的 package |
| `carried_sku_id` | FK nullable | 正在携带的 SKU |
| `carried_weight` | decimal | 当前载重 |
| `battery_pct` | decimal | 可选，先可保留 |
| `available_at_tick` | integer | 机器人下一次可执行新动作的 tick |
| `last_updated_tick` | integer | 更新时间 |

机器人状态建议：

```text
idle
ready
assigned
planning_route
navigating
moving
waiting_for_tile_lock
waiting_for_pick_point
picking
carrying
waiting_for_handoff
handoff_sending
handoff_receiving
navigating_to_conveyor
unloading
releasing_package
blocked
error
offline
```

写入方：Robot Runtime  
更新频率：每 step 或每 tick 更新

### `robot_state_history`

用于 replay、debug、可视化和利用率计算。

| 字段 | 类型 | 说明 |
|---|---|---|
| `history_id` | string PK | 历史记录 ID |
| `run_id` | FK | run |
| `robot_id` | FK | robot |
| `tick` | integer | tick |
| `tile_id` | FK | 所在 tile |
| `status` | enum | robot 状态 |
| `assigned_order_id` | FK nullable | 订单 |
| `carried_package_id` | FK nullable | package |
| `wait_reason` | string nullable | 等待原因 |

写入方：Robot Runtime  
更新频率：小规模仿真可每 tick；大规模可每 N ticks 采样

## 8. Tasks, Routes, Tile Locks

### `tasks`

任务是 order 的可执行步骤。

| 字段 | 类型 | 说明 |
|---|---|---|
| `task_id` | string PK | task ID |
| `run_id` | FK | run |
| `order_id` | FK nullable | 对应订单 |
| `robot_id` | FK nullable | 执行机器人 |
| `task_type` | enum | `reserve_inventory`, `navigate_to_pick_point`, `pick_from_rack`, `move_to_handoff`, `handoff_package`, `move_to_conveyor`, `unload_to_conveyor` |
| `source_tile_id` | FK nullable | 起点 |
| `target_tile_id` | FK nullable | 终点 |
| `rack_id` | FK nullable | rack |
| `pick_point_id` | FK nullable | pick point |
| `package_id` | FK nullable | package |
| `priority` | integer | 优先级 |
| `status` | enum | `created`, `ready`, `assigned`, `running`, `waiting`, `completed`, `failed`, `cancelled` |
| `created_tick` | integer | 创建 tick |
| `started_tick` | integer nullable | 开始 tick |
| `completed_tick` | integer nullable | 完成 tick |

写入方：Mission Planner, Scheduler, Robot Runtime  
更新频率：任务生命周期事件驱动

### `routes`

路线是机器人四向移动的计划。

| 字段 | 类型 | 说明 |
|---|---|---|
| `route_id` | string PK | route ID |
| `run_id` | FK | run |
| `robot_id` | FK | robot |
| `task_id` | FK | task |
| `order_id` | FK nullable | order |
| `plan_version` | integer | 重规划版本 |
| `start_tile_id` | FK | 起点 |
| `target_tile_id` | FK | 终点 |
| `planned_start_tick` | integer | 计划开始 |
| `planned_end_tick` | integer | 计划结束 |
| `status` | enum | `planned`, `active`, `completed`, `superseded`, `failed`, `cancelled` |
| `replan_reason` | string nullable | 重规划原因 |

写入方：Scheduler  
更新频率：路径生成和重规划

### `route_steps`

路线的每一步。相邻 step 必须是四向相邻 tile。

| 字段 | 类型 | 说明 |
|---|---|---|
| `route_step_id` | string PK | step ID |
| `route_id` | FK | route |
| `sequence_index` | integer | 顺序 |
| `from_tile_id` | FK | 起点 tile |
| `to_tile_id` | FK | 下一格 tile |
| `direction` | enum | `N`, `S`, `E`, `W`，用于 visual 里的 isometric 45 度方向 |
| `enter_tick` | integer | 进入 tick |
| `exit_tick` | integer | 离开 tick |
| `action` | enum | `move`, `wait`, `yield`, `pick`, `handoff`, `unload` |
| `status` | enum | `planned`, `locked`, `executed`, `skipped`, `failed` |

约束：

```sql
to_tile_id must be one of from_tile_id's N/S/E/W neighbors
from_tile_id and to_tile_id must both be available floor tiles
exit_tick > enter_tick
```

写入方：Scheduler  
更新频率：路径生成和执行状态更新

### `tile_locks`

这是避障和防碰撞的核心表。机器人移动时必须同时持有当前格锁和下一格锁。

| 字段 | 类型 | 说明 |
|---|---|---|
| `lock_id` | string PK | lock ID |
| `run_id` | FK | run |
| `tile_id` | FK | 被锁 tile |
| `robot_id` | FK | 锁定机器人 |
| `route_id` | FK nullable | route |
| `route_step_id` | FK nullable | step |
| `task_id` | FK nullable | task |
| `lock_type` | enum | `current_tile`, `next_tile`, `pick_point`, `handoff_pair`, `conveyor_unload` |
| `start_tick` | integer | 锁开始 tick |
| `end_tick` | integer | 锁结束 tick |
| `status` | enum | `requested`, `active`, `released`, `expired`, `cancelled`, `failed` |
| `priority` | integer | 抢锁优先级 |

核心约束：

```sql
同一 run_id + tile_id + tick 区间内，只能有一个 active lock。
```

业务规则：

- 机器人站在当前 tile 时持有 `current_tile` lock。
- 机器人准备移动时，先申请相邻 tile 的 `next_tile` lock。
- 如果下一格已被锁，机器人进入 `waiting_for_tile_lock`。
- 先拿到锁的机器人先走，其他机器人等待或重规划。

写入方：Scheduler, Robot Runtime  
更新频率：每一步移动前后高频更新

### `wait_states`

记录等待原因，方便计算拥堵和可视化。

| 字段 | 类型 | 说明 |
|---|---|---|
| `wait_state_id` | string PK | wait ID |
| `run_id` | FK | run |
| `robot_id` | FK | robot |
| `order_id` | FK nullable | order |
| `tile_id` | FK | 等待位置 |
| `blocked_tile_id` | FK nullable | 想去但被锁的 tile |
| `reason` | enum | `tile_locked`, `pick_point_busy`, `handoff_partner_not_adjacent`, `conveyor_busy`, `deadlock_risk` |
| `started_tick` | integer | 开始 tick |
| `ended_tick` | integer nullable | 结束 tick |
| `status` | enum | `active`, `resolved`, `abandoned` |

写入方：Scheduler, Robot Runtime  
更新频率：等待开始/结束时更新

## 9. Robot Handoff

### `handoffs`

两个机器人之间传递货物。必须相邻。

| 字段 | 类型 | 说明 |
|---|---|---|
| `handoff_id` | string PK | handoff ID |
| `run_id` | FK | run |
| `order_id` | FK | order |
| `package_id` | FK | package |
| `sender_robot_id` | FK | 发送机器人 |
| `receiver_robot_id` | FK | 接收机器人 |
| `sender_tile_id` | FK | 发送机器人 tile |
| `receiver_tile_id` | FK | 接收机器人 tile |
| `sku_id` | FK | SKU |
| `handling_difficulty` | enum | 从 SKU 复制 |
| `planned_start_tick` | integer | 计划开始 |
| `actual_start_tick` | integer nullable | 实际开始 |
| `completed_tick` | integer nullable | 完成 |
| `status` | enum | `planned`, `waiting_adjacent`, `in_progress`, `completed`, `failed`, `cancelled` |

约束：

```sql
sender_tile_id and receiver_tile_id must be N/S/E/W adjacent.
```

写入方：Scheduler, Robot Runtime  
更新频率：交接任务生命周期

## 10. 出口履带、dock 与车辆班次

### `outbound_conveyors`

订单卸货点。出口履带本体不是可行走 tile，机器人不能走到 conveyor tile 上。机器人必须站在履带旁边的 `dropoff_tile_id`，且该 tile 必须是 `is_available_floor = true` 的地面 tile。货物卸到这里以后，仓库履约可以算完成。

| 字段 | 类型 | 说明 |
|---|---|---|
| `conveyor_id` | string PK | 出口履带 ID |
| `warehouse_id` | FK | warehouse |
| `dock_id` | FK nullable | 对应 dock |
| `conveyor_tile_id` | FK | 出口履带本体 tile，不可行走 |
| `dropoff_tile_id` | FK | 机器人卸货时站立的 available floor tile |
| `queue_capacity_orders` | integer | 可暂存订单数 |
| `status` | enum | `active`, `congested`, `blocked`, `maintenance` |

写入方：Scenario Loader；Runtime 可更新拥堵状态  
更新频率：静态/低频

### `outbound_docks`

出货 dock，可配置 2 个或 4 个。

| 字段 | 类型 | 说明 |
|---|---|---|
| `dock_id` | string PK | dock ID |
| `warehouse_id` | FK | warehouse |
| `name` | string | 名称 |
| `dock_tile_id` | FK | dock tile |
| `status` | enum | `active`, `closed`, `congested`, `maintenance` |

写入方：Scenario Loader  
更新频率：静态/低频

### `truck_schedules`

车辆到达规则。车可以每 30 分钟来一次，也可以每 60 分钟来一次。

| 字段 | 类型 | 说明 |
|---|---|---|
| `schedule_id` | string PK | schedule ID |
| `warehouse_id` | FK | warehouse |
| `dock_id` | FK | dock |
| `frequency_minutes` | integer | 30 或 60 等 |
| `first_arrival_tick` | integer | 第一辆车到达 tick |
| `loading_window_ticks` | integer | 装车窗口 |
| `capacity_orders` | integer | 最大订单数 |
| `capacity_weight` | decimal | 最大重量 |
| `status` | enum | `active`, `paused`, `retired` |

写入方：Scenario Loader  
更新频率：静态

### `truck_visits`

具体某一辆车。根据 schedule 在仿真中生成。

| 字段 | 类型 | 说明 |
|---|---|---|
| `truck_visit_id` | string PK | 车辆到访 ID |
| `run_id` | FK | run |
| `dock_id` | FK | dock |
| `schedule_id` | FK | schedule |
| `planned_arrival_tick` | integer | 计划到达 |
| `actual_arrival_tick` | integer nullable | 实际到达 |
| `planned_departure_tick` | integer | 计划离开 |
| `actual_departure_tick` | integer nullable | 实际离开 |
| `capacity_orders` | integer | 容量 |
| `loaded_orders` | integer | 已装订单 |
| `status` | enum | `scheduled`, `arrived`, `loading`, `departed`, `missed`, `cancelled` |

写入方：Outbound Runtime  
更新频率：车辆到达/离开事件

### `order_outbound_assignments`

订单分配到哪个出口、哪辆车。

| 字段 | 类型 | 说明 |
|---|---|---|
| `assignment_id` | string PK | assignment ID |
| `run_id` | FK | run |
| `order_id` | FK | order |
| `conveyor_id` | FK | 出口履带 |
| `dock_id` | FK nullable | dock |
| `truck_visit_id` | FK nullable | 具体车辆 |
| `assigned_tick` | integer | 分配 tick |
| `dock_deadline_tick` | integer | 必须卸到出口的 tick |
| `unloaded_tick` | integer nullable | 卸货 tick |
| `loaded_tick` | integer nullable | 装车 tick |
| `status` | enum | `assigned`, `en_route`, `unloaded_at_conveyor`, `loaded_on_truck`, `shipped`, `missed_truck`, `failed` |

写入方：Outbound Planner, Robot Runtime  
更新频率：订单出货生命周期

## 11. Events 与可视化数据来源

### `events`

所有关键状态变化都写事件，便于 replay、debug、计算指标。

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_id` | string PK | event ID |
| `run_id` | FK | run |
| `tick` | integer | tick |
| `entity_type` | enum | `order`, `robot`, `rack`, `sku`, `tile`, `lock`, `route`, `handoff`, `conveyor`, `truck` |
| `entity_id` | string | 实体 ID |
| `event_type` | string | 事件类型 |
| `payload` | JSON | 事件详情 |
| `severity` | enum | `debug`, `info`, `warning`, `error` |

写入方：所有 runtime service 通过 Event Bus 写入  
更新频率：高频追加

### 可视化应从哪里取数据

| 可视化内容 | 数据来源 | 是否需要单独存指标 |
|---|---|---|
| 地图 tile | `tiles` | 不需要 |
| 哪些地面可走 | `tiles.is_available_floor`, `tile_neighbors` | 不需要 |
| 碰撞阻挡物 | `tiles.blocks_robot`, `tiles.collision_class` | 不需要 |
| rack 位置与朝向 | `racks`, `rack_tiles` | 不需要 |
| rack 剩余库存 | `rack_inventory` | 不需要 |
| SKU 外观 | `skus.weight_class`, `skus.package_visual_type` | 不需要 |
| 机器人位置和状态 | `robots` | 不需要 |
| 机器人历史轨迹 | `robot_state_history` 或 `route_steps` | 不需要 |
| 当前拥堵 | `tile_locks`, `wait_states` | 不需要 |
| 出口拥堵 | `outbound_conveyors`, `order_outbound_assignments` | 不需要 |
| throughput | `orders.completion_tick` 按时间窗口聚合 | 不需要 |
| missed deadline | `orders.deadline_tick` vs `orders.completion_tick` | 不需要 |

## 12. 派生指标

数据库可以不持久化这些值，运行时或报告层查询计算即可：

```text
throughput = completed orders / time window
order_generation_rate = generated orders / time window
average_fulfillment_time = avg(completion_tick - creation_tick)
deadline_miss_count = count(completion_tick > deadline_tick)
on_time_completion_rate = completed_on_time / completed_orders
rack_depletion_rate = shipped_quantity / initial_quantity
robot_utilization = non_idle_ticks / total_robot_ticks
waiting_time = sum(wait_states duration)
congestion_score = active tile locks + active waits per area/time window
handoff_count = completed handoffs
truck_fill_rate = loaded_orders / capacity_orders
missed_truck_count = count(order_outbound_assignments.status = missed_truck)
```

如果为了性能需要缓存，可以写入 `metric_snapshots`，但它不是状态源。

### `metric_snapshots`

| 字段 | 类型 | 说明 |
|---|---|---|
| `metric_snapshot_id` | string PK | snapshot ID |
| `run_id` | FK | run |
| `tick` | integer | tick |
| `completed_orders` | integer | 已完成订单数 |
| `generated_orders` | integer | 已生成订单数 |
| `active_orders` | integer | 活跃订单数 |
| `waiting_robot_count` | integer | 等待机器人数 |
| `active_lock_count` | integer | 当前锁数 |
| `deadline_miss_count` | integer | 超时数 |
| `metadata` | JSON | 可扩展指标 |

写入方：Metrics Collector  
更新频率：每 N ticks，可选

## 13. 最小可实现表清单

第一阶段建议只实现这些表：

1. `simulation_runs`
2. `warehouses`
3. `tiles`
4. `tile_neighbors`
5. `racks`
6. `rack_tiles`
7. `rack_pick_points`
8. `skus`
9. `rack_inventory`
10. `order_generation_profiles`
11. `orders`
12. `inventory_reservations`
13. `packages`
14. `robot_types`
15. `robots`
16. `tasks`
17. `routes`
18. `route_steps`
19. `tile_locks`
20. `wait_states`
21. `handoffs`
22. `outbound_conveyors`
23. `outbound_docks`
24. `truck_schedules`
25. `truck_visits`
26. `order_outbound_assignments`
27. `events`

第二阶段再加入：

1. `robot_state_history`
2. `agent_messages`
3. `metric_snapshots`

## 14. 关键数据库不变量

1. `orders.order_id` 全局唯一，长度足够支撑高频长时间模拟。
2. 同一个 run 内 `order_sequence` 唯一递增。
3. SKU 库存只减少，不入库补货。
4. rack 占用 tile 不可 traversable。
5. rack pick point 必须是 traversable tile。
6. 机器人只能移动到 N/S/E/W 相邻 tile。
7. `tile_neighbors` 只能连接 available floor tile，不能连接 rack、出口、dock、墙体或 blocked tile。
8. 同一 tick 区间内，同一个 tile 只能有一个 active lock。
9. 机器人移动时必须同时持有当前 tile lock 和下一 tile lock。
10. 机器人取货时必须站在对应 rack 的可用 pick point。
11. 两个机器人 handoff 时必须相邻。
12. package 不能同时属于 rack 和 robot。
13. order 只有在出口履带旁的 dropoff tile 卸货后才能进入 `completed`。
14. throughput、congestion、waiting time 优先作为查询派生结果，而不是手写状态。

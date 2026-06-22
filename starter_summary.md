# Robothon Starter Summary / Robothon Starter 摘要

Project direction: Warehouse Order Fulfillment Simulator  
项目方向：仓库订单履约优化仿真器

Local repository: `/Users/billyuanwang/Library/CloudStorage/Dropbox/Agentech智能体科技/020 Agentech Robotics/FF_hackathon_06.2026/Robothon-starter`  
本地仓库：`/Users/billyuanwang/Library/CloudStorage/Dropbox/Agentech智能体科技/020 Agentech Robotics/FF_hackathon_06.2026/Robothon-starter`

## Bottom Line / 核心结论

The starter repository is a MuJoCo robot asset and demo package. It is not a warehouse simulator and not a robotics-control framework.

starter 仓库是一个 MuJoCo 机器人资产和 demo 包。它不是仓库仿真器，也不是机器人控制框架。

Use the starter as a robot asset library, MuJoCo validation environment, rendering/video/export reference, and submission scaffold.

应把 starter 用作机器人资产库、MuJoCo 验证环境、渲染/视频/导出参考，以及提交脚手架。

Do not use it as the main architecture. The main architecture should remain: Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization.

不要把它当作主架构。主架构应保持为：Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization。

MuJoCo should validate low-level robot actions only.

MuJoCo 只应验证低层机器人动作。

## What Exists / 现有什么

| Area / 领域 | Existing starter support / starter 已有支持 |
|---|---|
| Scenes / 场景 | One minimal Master scene plus runtime-generated demo floors, pads, lights, and cameras / 一个极简 Master 场景，以及运行时生成的 demo 地面、标记垫、灯光和相机 |
| Robots / 机器人 | FF Master humanoid, Aegis quadruped, FF Futurist humanoid / FF Master 人形、Aegis 四足、FF Futurist 人形 |
| Assets / 资产 | STL meshes, MJCF/URDF files, preview images, RViz config / STL 网格、MJCF/URDF 文件、预览图、RViz 配置 |
| Controllers / 控制器 | No reusable controllers; demos directly animate `qpos` / 没有可复用控制器；demo 直接动画化 `qpos` |
| Sensors / 传感器 | Master has frame/IMU-style sensors; Aegis/Futurist do not / Master 有 frame/IMU 风格传感器；Aegis/Futurist 没有 |
| Actuators / 执行器 | Master has 31 motor actuators; Aegis/Futurist do not / Master 有 31 个 motor 执行器；Aegis/Futurist 没有 |
| Demos / 演示 | Three scripts generating videos and trajectory JSON / 三个脚本生成视频和轨迹 JSON |
| Visualization / 可视化 | MuJoCo viewer, Python renderer, imageio video export, RViz support for Master / MuJoCo viewer、Python renderer、imageio 视频导出、Master 的 RViz 支持 |
| Submission / 提交 | Template folder and PR checklist / 提交模板目录和 PR 清单 |

## Best Reuse / 最佳复用点

Reuse `requirements.txt`, `submissions/SUBMISSION_TEMPLATE/`, the example video/trajectory patterns, `assets/Master/scene.xml`, `ff_master_ultra.xml`, the Futurist `carry_walk` idea, and the JSON summary output pattern.

复用 `requirements.txt`、`submissions/SUBMISSION_TEMPLATE/`、示例视频/轨迹输出模式、`assets/Master/scene.xml`、`ff_master_ultra.xml`、Futurist 的 `carry_walk` 思路，以及 JSON summary 输出模式。

Do not rebuild MuJoCo setup, video generation, model loading, robot meshes, submission templates, or basic trajectory export.

不要重建 MuJoCo 设置、视频生成、模型加载、机器人网格、提交模板或基础轨迹导出。

Do not depend on scripted demo motion as real control, Futurist for collision-accurate manipulation, Aegis/Futurist as actuator-ready robots, or full humanoid control for the core project.

不要依赖脚本化 demo 动作作为真实控制，不要依赖 Futurist 做碰撞精确操作，不要把 Aegis/Futurist 当成执行器就绪的机器人，也不要把完整人形控制作为项目核心。

## Recommended Fast Path / 推荐最快路径

Create `submissions/warehouse-order-fulfillment/` and build a pure-Python warehouse simulator with orders, inventory, shelves, bins, stations, robots, and an aisle graph.

创建 `submissions/warehouse-order-fulfillment/`，并构建一个纯 Python 仓库仿真器，包含订单、库存、货架、料箱、工作站、机器人和巷道图。

Add Mission -> Workflow decomposition, then represent actions as a Skill Graph.

添加 Mission -> Workflow 拆解，然后把动作表示为 Skill Graph。

Recommended skills include `navigate_to_zone`, `align_to_shelf`, `pick_item`, `place_in_tote`, `carry_tote`, `handoff_to_station`, `pack_order`, and `recover_from_blockage`.

推荐技能包括 `navigate_to_zone`、`align_to_shelf`、`pick_item`、`place_in_tote`、`carry_tote`、`handoff_to_station`、`pack_order` 和 `recover_from_blockage`。

Implement a multi-agent runtime for task assignment, route planning, conflict avoidance, event logs, and metrics.

实现多智能体运行时，用于任务分配、路径规划、冲突规避、事件日志和指标统计。

Add a MuJoCo validation layer with simple warehouse boxes, shelves, stations, packages, one robot model, and representative low-level skill validation.

添加 MuJoCo 验证层，包含简单仓库盒子、货架、工位、包裹、一个机器人模型，以及代表性低层技能验证。

Generate a demo video, trajectory JSON, and order fulfillment metrics.

生成演示视频、轨迹 JSON 和订单履约指标。

## Effort Snapshot / 工程量快照

| Component / 组件 | Effort / 难度 |
|---|---:|
| Submission scaffold / 提交脚手架 | Easy |
| Warehouse objects and map / 仓库物体与地图 | Easy |
| Order and inventory model / 订单与库存模型 | Easy |
| Metrics and JSON logs / 指标与 JSON 日志 | Easy |
| Demo video generation / 演示视频生成 | Easy |
| Mission planner / Mission 规划器 | Medium |
| Workflow engine / 工作流引擎 | Medium |
| Skill graph / 技能图 | Medium |
| Multi-agent scheduler / 多智能体调度器 | Medium |
| Aisle route planning / 巷道路径规划 | Medium |
| MuJoCo warehouse scene / MuJoCo 仓库场景 | Medium |
| Carry-action validation / 搬运动作验证 | Medium |
| Advanced optimization / 高级优化 | Hard |
| Stable pick/place manipulation / 稳定拾取放置 | Hard |
| Actuator-based humanoid control / 基于执行器的人形控制 | Hard |

## Recommended Robot Choice / 推荐机器人选择

Use FF Master when you need MuJoCo depth: actuators, sensors, MJCF, and collisions.

当需要展示 MuJoCo 深度时使用 FF Master：执行器、传感器、MJCF 和碰撞。

Use Futurist when you need a visually clear humanoid carry demo.

当需要一个视觉上清晰的人形搬运 demo 时使用 Futurist。

Use Aegis only if the story is patrol or navigation, not package manipulation.

只有当叙事是巡逻或导航，而不是包裹操作时，才使用 Aegis。

For warehouse order optimization, the robot should be an actor in the workflow, not the center of the architecture.

对仓库订单优化来说，机器人应该是工作流中的执行者，而不是架构中心。

## Actionable Recommendation / 行动建议

Build the optimizer first, then plug MuJoCo into selected skill validations.

先构建优化器，再把 MuJoCo 接入到选定技能的验证中。

Minimum compelling demo: 3 to 5 warehouse agents, 10 to 20 orders, shelves and packing station, dynamic task assignment, route conflict avoidance, event replay, metrics showing improvement over a baseline, and one MuJoCo clip validating a carry/pick/place-style skill.

最低限度但有说服力的 demo：3 到 5 个仓库智能体、10 到 20 个订单、货架和打包站、动态任务分配、路径冲突规避、事件回放、相对 baseline 的指标提升，以及一个验证搬运/拾取/放置类技能的 MuJoCo 片段。

This gives the project a strong warehouse-optimization identity while still satisfying the Robothon expectation of a runnable MuJoCo robot simulation.

这能让项目拥有清晰的仓库优化身份，同时满足 Robothon 对可运行 MuJoCo 机器人仿真的期待。

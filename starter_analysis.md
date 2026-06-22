# Robothon Starter Repository Technical Analysis / Robothon Starter 仓库技术分析

Project: FFAI Robothon Summer 2026  
项目：FFAI Robothon Summer 2026

Target direction: Warehouse Order Fulfillment Simulator  
目标方向：仓库订单履约优化仿真器

Analysis date: 2026-06-19  
分析日期：2026-06-19

Repository: `Faraday-Future-AI/Robothon-starter`  
仓库：`Faraday-Future-AI/Robothon-starter`

Local path: `/Users/billyuanwang/Library/CloudStorage/Dropbox/Agentech智能体科技/020 Agentech Robotics/FF_hackathon_06.2026/Robothon-starter`  
本地路径：`/Users/billyuanwang/Library/CloudStorage/Dropbox/Agentech智能体科技/020 Agentech Robotics/FF_hackathon_06.2026/Robothon-starter`

## Executive Summary / 执行摘要

The official starter repository is a compact MuJoCo simulation starter kit, not a warehouse optimization framework. It provides robot assets, loading examples, video generation scripts, trajectory JSON output, and a submission template.

官方 starter 仓库是一个紧凑的 MuJoCo 机器人仿真起步包，不是仓库优化框架。它提供机器人资产、模型加载示例、视频生成脚本、轨迹 JSON 输出和提交模板。

It does not provide mission planning, order batching, warehouse layout modeling, inventory allocation, skill graphs, multi-agent scheduling, task execution runtime, or optimizer infrastructure.

它没有提供任务规划、订单批处理、仓库布局建模、库存分配、技能图、多智能体调度、任务执行运行时或优化器基础设施。

For this project, the fastest path is to reuse the repository as a MuJoCo validation shell and submission scaffold, while building the warehouse simulator as a higher-level runtime above MuJoCo.

对本项目来说，最快路径是把这个仓库当作 MuJoCo 物理验证外壳和提交脚手架复用，同时在 MuJoCo 之上构建更高层的仓库仿真运行时。

The core architecture should remain: Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization.

核心架构应保持为：Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization。

MuJoCo should only validate low-level robot actions such as move-to-station, pick, place, carry, avoid obstacle, and handoff. The warehouse-order logic should remain outside robotics-control code.

MuJoCo 只应该用于验证低层机器人动作，例如移动到工位、拾取、放置、搬运、避障和交接。仓库订单逻辑应保留在机器人控制代码之外。

## Official Context / 官方背景

The Robothon README describes the event as a MuJoCo robotics simulation hackathon. Submissions are expected to be runnable robot simulations, tasks, interactive systems, or data-collection environments.

Robothon README 将比赛描述为 MuJoCo 机器人仿真黑客松。参赛作品需要是可运行的机器人仿真、任务、交互系统或数据采集环境。

The public rubric emphasizes reproducibility, MuJoCo depth, task design, control or planning, engineering quality, demo clarity, and innovation.

公开评分标准强调可复现性、MuJoCo 深度、任务设计、控制或规划能力、工程质量、演示清晰度和创新性。

Relevant official requirements from the starter repository are: project code under `submissions/<project-name>/`, source code and assets, run instructions, demo video or link, and `registration.json`.

starter 仓库中的相关官方要求包括：项目代码放在 `submissions/<project-name>/` 下，包含源码和资产、运行说明、演示视频或链接，以及 `registration.json`。

The official examples generate videos and trajectory JSON files from code, which is a useful pattern for this warehouse simulator.

官方示例会通过代码生成视频和轨迹 JSON，这对仓库仿真器是一个很有用的可复用模式。

## Repository Structure / 仓库结构

The repository is small at the source-code level but dense in robot assets. Most of the size is in STL meshes under `assets/`.

这个仓库在源码层面很小，但机器人资产密度很高。大部分体积来自 `assets/` 下的 STL 网格文件。

| Path / 路径 | Role / 作用 |
|---|---|
| `README.md` | English overview, quick start, rubric, submission checklist / 英文介绍、快速开始、评分标准和提交清单 |
| `README.zh-CN.md` | Chinese overview / 中文介绍 |
| `requirements.txt` | Minimal runtime dependencies: `mujoco`, `numpy`, `imageio[ffmpeg]` / 最小运行依赖 |
| `model_catalog.json` | Suggested external robot models from MuJoCo Menagerie / 推荐外部机器人模型清单 |
| `examples/` | Three runnable demo scripts / 三个可运行 demo 脚本 |
| `assets/` | Robot model assets and visualization files / 机器人模型资产和可视化文件 |
| `submissions/SUBMISSION_TEMPLATE/` | Required submission folder template / 必需的提交目录模板 |
| `.github/pull_request_template.md` | PR checklist and required UUID field / PR 清单和必填 UUID 字段 |

Asset footprint: `assets/` is about 127 MB, with `assets/Master/` about 112 MB, `assets/Aegis/` about 12 MB, and `assets/Futurist/` about 2.5 MB.

资产体量：`assets/` 约 127 MB，其中 `assets/Master/` 约 112 MB，`assets/Aegis/` 约 12 MB，`assets/Futurist/` 约 2.5 MB。

Asset file types include STL meshes, XML/MJCF, URDF, PNG previews, RViz config, CSV, README files, and Python examples.

资产文件类型包括 STL 网格、XML/MJCF、URDF、PNG 预览图、RViz 配置、CSV、README 和 Python 示例。

## Existing Scenes / 现有场景

`assets/Master/scene.xml` is the only checked-in MJCF scene file. It includes `ff_master_ultra.xml`, defines visual settings, a skybox texture, a checker ground material, and a floor plane.

`assets/Master/scene.xml` 是仓库中唯一直接提交的 MJCF 场景文件。它 include 了 `ff_master_ultra.xml`，并定义了视觉设置、天空盒纹理、棋盘地面材质和地面平面。

This scene solves basic robot loading and a minimal ground environment. It does not include warehouse geometry, shelves, bins, SKUs, packages, stations, loading docks, aisles, or task objects.

这个场景解决了基础机器人加载和最小地面环境。它不包含仓库几何体、货架、料箱、SKU、包裹、工作站、装卸口、巷道或任务物体。

The Aegis and Futurist demos generate scene elements at runtime through `mujoco.MjSpec`, including floor planes, runways or walkways, start/goal pads, lights, free cameras, and an optional carry box.

Aegis 和 Futurist 的 demo 会通过 `mujoco.MjSpec` 在运行时生成场景元素，包括地面、跑道或步道、起点/终点垫、灯光、自由相机，以及可选的搬运箱子。

These generated scenes are useful references for building a warehouse validation scene in code, but they are not warehouse scenes yet.

这些运行时生成场景可以作为用代码构建仓库验证场景的参考，但它们本身还不是仓库场景。

## Existing Robots / 现有机器人

### FF Master Humanoid / FF Master 人形机器人

FF Master is located in `assets/Master/` and is the strongest MuJoCo-native asset in the starter repository.

FF Master 位于 `assets/Master/`，是 starter 仓库里最强的 MuJoCo 原生资产。

Important files include `ff_master_ultra.xml`, `ff_master_hand.xml`, `ff_master_fist.xml`, matching URDF variants, STL meshes, preview PNGs, and ROS/RViz launch files.

重要文件包括 `ff_master_ultra.xml`、`ff_master_hand.xml`、`ff_master_fist.xml`、对应 URDF 变体、STL 网格、预览 PNG 和 ROS/RViz 启动文件。

`ff_master_ultra.xml` contains 32 articulated joints plus 1 freejoint, 31 motor actuators, 32 bodies, 87 geoms, 37 mesh assets, 4 sites, a tracking light, and frame/IMU-style sensors.

`ff_master_ultra.xml` 包含 32 个关节加 1 个 freejoint、31 个 motor 执行器、32 个 body、87 个 geom、37 个 mesh asset、4 个 site、一个 tracking light，以及 frame/IMU 风格的传感器。

FF Master is the best candidate when the project needs MuJoCo depth such as MJCF, actuators, sensors, collisions, and articulated robot structure.

如果项目需要展示 MuJoCo 深度，例如 MJCF、执行器、传感器、碰撞和多关节机器人结构，FF Master 是最佳候选。

The limitation is that the provided demo does not use closed-loop actuator control. It directly writes poses into `data.qpos`, resets `data.qvel`, and calls `mujoco.mj_forward()`.

限制是官方 demo 并没有使用闭环执行器控制。它直接把姿态写入 `data.qpos`，重置 `data.qvel`，然后调用 `mujoco.mj_forward()`。

For warehouse order optimization, full humanoid control is unnecessary and likely too expensive for hackathon speed.

对仓库订单优化来说，完整人形机器人控制不是必要项，而且很可能会拖慢黑客松开发速度。

### Aegis Quadruped / Aegis 四足机器人

Aegis is located in `assets/Aegis/` and is provided as URDF plus meshes.

Aegis 位于 `assets/Aegis/`，以 URDF 加网格文件的形式提供。

The Aegis package contains `urdf/Aegis.urdf`, `urdf/Aegis_mujoco.urdf`, `urdf/Aegis.csv`, and 17 STL mesh files.

Aegis 包含 `urdf/Aegis.urdf`、`urdf/Aegis_mujoco.urdf`、`urdf/Aegis.csv` 和 17 个 STL 网格文件。

The URDF has 17 links, 16 joints, 17 visual elements, 17 collision elements, 17 inertials, and 34 mesh references. It does not declare actuators or sensors.

该 URDF 有 17 个 link、16 个 joint、17 个 visual、17 个 collision、17 个 inertial 和 34 个 mesh 引用。它没有声明执行器或传感器。

Aegis is useful for patrol or navigation-style visual demos, but it is not a complete warehouse picking robot.

Aegis 适合巡逻或导航风格的视觉 demo，但不是完整的仓库拣货机器人。

### FF Futurist Humanoid / FF Futurist 人形机器人

Futurist is located in `assets/Futurist/` and is provided as a URDF asset package.

Futurist 位于 `assets/Futurist/`，以 URDF 资产包形式提供。

The package contains `futurist.urdf` and 48 STL mesh files. The URDF has 50 links, 49 joints, 48 visual mesh references, and 37 inertials.

该包包含 `futurist.urdf` 和 48 个 STL 网格文件。URDF 有 50 个 link、49 个 joint、48 个 visual mesh 引用和 37 个 inertial。

Futurist does not provide collision geometry, actuators, or sensors in the checked-in URDF.

Futurist 在已提交的 URDF 中没有提供碰撞几何、执行器或传感器。

The `run_futurist_demo.py` script already includes a `carry_walk` scenario, which is a useful visual reference for package-carry validation.

`run_futurist_demo.py` 已经包含 `carry_walk` 场景，这对包裹搬运动作验证是有用的视觉参考。

However, because collision and actuator definitions are missing, Futurist should be treated as a visual validation platform unless additional proxy collision/control layers are added.

但是由于缺少碰撞和执行器定义，Futurist 应被视为视觉验证平台，除非之后额外添加代理碰撞层和控制层。

## Existing Assets / 现有资产

Reusable assets include FF Master MJCF and meshes, Aegis URDF and meshes, Futurist URDF and meshes, Master preview PNGs, MuJoCo scene material examples, and submission templates.

可复用资产包括 FF Master MJCF 和网格、Aegis URDF 和网格、Futurist URDF 和网格、Master 预览 PNG、MuJoCo 场景材质示例和提交模板。

The starter does not include warehouse shelves, bins, totes, SKUs, conveyor belts, dock doors, forklifts, barcode/RFID objects, order datasets, warehouse maps, path graphs, or optimization datasets.

starter 不包含仓库货架、料箱、周转箱、SKU、传送带、装卸门、叉车、条码/RFID 物体、订单数据集、仓库地图、路径图或优化数据集。

For this project, warehouse objects should be built as simple boxes and semantic objects first. Visual realism should come after the optimizer and runtime work.

对本项目来说，仓库物体应先用简单盒子和语义对象构建。视觉真实感应排在优化器和运行时之后。

## Existing Controllers / 现有控制器

There are no reusable robotics controllers in the starter repository.

starter 仓库中没有可复用的机器人控制器。

The demo scripts implement deterministic animation by directly setting `data.qpos`, zeroing `data.qvel`, and calling `mujoco.mj_forward()`.

demo 脚本通过直接设置 `data.qpos`、清零 `data.qvel` 并调用 `mujoco.mj_forward()` 来实现确定性动画。

This is useful for repeatable rendering, but it is not PID control, torque control, actuator position control, model predictive control, a locomotion policy, a grasp policy, or a multi-agent planner.

这对可复现渲染很有用，但它不是 PID 控制、力矩控制、执行器位置控制、模型预测控制、步态策略、抓取策略或多智能体规划器。

For the warehouse simulator, treat the demo scripts as examples of model loading, scripted motion, body-position sampling, rendering, video export, and trajectory JSON export.

对仓库仿真器来说，应把 demo 脚本视为模型加载、脚本动作、body 位置采样、渲染、视频导出和轨迹 JSON 导出的示例。

## Existing Sensors / 现有传感器

FF Master includes MuJoCo sensor definitions such as `framepos`, `framequat`, `accelerometer`, and `gyro`.

FF Master 包含 MuJoCo 传感器定义，例如 `framepos`、`framequat`、`accelerometer` 和 `gyro`。

FF Master also defines IMU-related sites such as `imu_0`, `imu_1`, and `imu_2`.

FF Master 还定义了与 IMU 相关的 site，例如 `imu_0`、`imu_1` 和 `imu_2`。

Aegis and Futurist do not declare sensors in the checked-in URDF files.

Aegis 和 Futurist 在已提交的 URDF 文件中没有声明传感器。

For warehouse optimization, most sensor streams can initially be simulated at the task layer: order state, robot graph location, package possession, shelf/bin state, blocked aisles, and low-level validation results.

对仓库优化来说，大多数传感器流一开始可以在任务层模拟：订单状态、机器人图节点位置、包裹持有状态、货架/料箱状态、堵塞巷道和低层验证结果。

MuJoCo sensors should be added only when they improve the physical validation story, such as contact checks, camera/depth frames, or robot body pose.

只有在能增强物理验证叙事时，才需要添加 MuJoCo 传感器，例如接触检查、相机/深度帧或机器人 body 位姿。

## Existing Actuators / 现有执行器

FF Master defines 31 motor actuators for hips, knees, ankles, waist, shoulders, elbows, wrists, and head.

FF Master 定义了 31 个 motor 执行器，覆盖髋、膝、踝、腰、肩、肘、腕和头部。

These actuators are valuable if a later validation layer needs to show real MuJoCo actuator usage.

如果后续验证层需要展示真实 MuJoCo 执行器使用，这些执行器很有价值。

However, the included demo does not use these actuators as a control stack; it writes joint positions directly.

但官方 demo 并没有把这些执行器作为控制栈使用，而是直接写入关节位置。

Aegis and Futurist do not declare actuators in their checked-in URDF assets.

Aegis 和 Futurist 在已提交的 URDF 资产中没有声明执行器。

The fastest warehouse simulator should not start by building full-body actuator control.

最快的仓库仿真器不应从构建全身执行器控制开始。

## Existing Demos / 现有 Demo

`examples/run_ff_master_demo.py` loads `assets/Master/scene.xml`, animates the FF Master humanoid, renders a video, and writes trajectory JSON.

`examples/run_ff_master_demo.py` 加载 `assets/Master/scene.xml`，为 FF Master 人形机器人生成动画，渲染视频，并写出轨迹 JSON。

Its outputs are `outputs/ff_master_demo.mp4` or GIF fallback, plus `outputs/ff_master_trajectory.json`.

它的输出是 `outputs/ff_master_demo.mp4` 或 GIF 备选文件，以及 `outputs/ff_master_trajectory.json`。

`examples/run_aegis_demo.py` loads Aegis through `mujoco.MjSpec`, adds a freejoint, adds a runway/start/goal/floor/lights/camera, and renders a deterministic patrol gait.

`examples/run_aegis_demo.py` 通过 `mujoco.MjSpec` 加载 Aegis，添加 freejoint、跑道、起点、终点、地面、灯光和相机，并渲染确定性的巡逻步态。

Its outputs are `outputs/aegis_demo_v4_wide.mp4` or GIF fallback, plus `outputs/aegis_trajectory_v4_wide.json`.

它的输出是 `outputs/aegis_demo_v4_wide.mp4` 或 GIF 备选文件，以及 `outputs/aegis_trajectory_v4_wide.json`。

`examples/run_futurist_demo.py` validates mesh files, injects MuJoCo compiler settings, loads the Futurist URDF, and supports `showcase`, `front_walk`, `carry_walk`, and `--check-assets`.

`examples/run_futurist_demo.py` 会验证网格文件，注入 MuJoCo compiler 设置，加载 Futurist URDF，并支持 `showcase`、`front_walk`、`carry_walk` 和 `--check-assets`。

Its outputs are `outputs/futurist_demo.mp4` or GIF fallback, plus `outputs/futurist_trajectory.json`.

它的输出是 `outputs/futurist_demo.mp4` 或 GIF 备选文件，以及 `outputs/futurist_trajectory.json`。

All three demos are best understood as runnable proof and rendering templates, not as production controllers.

这三个 demo 最适合被理解为可运行证明和渲染模板，而不是生产级控制器。

## Existing Visualization Tools / 现有可视化工具

The starter supports `python -m mujoco.viewer`, `mujoco.Renderer`, `imageio[ffmpeg]` video writing, `mujoco.MjvCamera`, and Master ROS/RViz files.

starter 支持 `python -m mujoco.viewer`、`mujoco.Renderer`、`imageio[ffmpeg]` 视频写出、`mujoco.MjvCamera`，以及 Master 的 ROS/RViz 文件。

Master preview PNGs in `assets/Master/visual/` are useful for documentation and robot selection.

`assets/Master/visual/` 中的 Master 预览 PNG 对文档和机器人选择有帮助。

The Futurist README includes PyBullet and ROS/RViz examples, but those are optional side references rather than core project infrastructure.

Futurist README 包含 PyBullet 和 ROS/RViz 示例，但它们只是可选参考，不是本项目的核心基础设施。

For this project, the most reusable visualization path is the Python renderer/video pattern from the example scripts.

对本项目来说，最可复用的可视化路径是示例脚本中的 Python renderer/video 模式。

## What Can Be Reused / 可以复用什么

Reuse the dependency baseline, submission template, example rendering scripts, trajectory JSON pattern, Master MJCF assets, and Futurist carry visual idea.

可以复用依赖基线、提交模板、示例渲染脚本、轨迹 JSON 模式、Master MJCF 资产，以及 Futurist 的搬运视觉思路。

Reuse `assets/Master/scene.xml` as a reference for MJCF scene composition, not as a final warehouse scene.

可以把 `assets/Master/scene.xml` 作为 MJCF 场景组织方式的参考，但不要把它当成最终仓库场景。

Reuse the Aegis and Futurist runtime scene-generation style when creating simple warehouse validation scenes in Python.

创建简单仓库验证场景时，可以复用 Aegis 和 Futurist 的运行时场景生成方式。

Reuse the demo success-summary JSON format for metrics, validation results, and demo evidence.

可以复用 demo 的 summary JSON 格式，用于输出指标、验证结果和演示证据。

## What Should Not Be Rebuilt / 不应该重建什么

Do not rebuild MuJoCo installation, rendering, video generation, model loading, robot meshes, submission templates, or basic trajectory export.

不要重建 MuJoCo 安装、渲染、视频生成、模型加载、机器人网格、提交模板或基础轨迹导出。

Do not rebuild full humanoid control unless a narrow physical validation task absolutely requires it.

除非某个很窄的物理验证任务绝对需要，否则不要重建完整人形机器人控制。

Do not treat the scripted qpos demos as real controllers.

不要把脚本化 qpos demo 当成真实控制器。

Do not depend on Futurist for collision-accurate manipulation without adding proxy collision geometry.

不要在没有添加代理碰撞几何的情况下依赖 Futurist 做碰撞精确的操作任务。

## What Is Already Solved / 已经解决什么

The starter already solves MuJoCo dependency setup, example model loading, MJCF include usage, URDF-to-MuJoCo loading via `MjSpec`, basic floor/lights/camera setup, deterministic demo generation, video export, trajectory summary export, submission folder expectations, and PR template requirements.

starter 已经解决了 MuJoCo 依赖设置、示例模型加载、MJCF include 用法、通过 `MjSpec` 将 URDF 加载进 MuJoCo、基础地面/灯光/相机设置、确定性 demo 生成、视频导出、轨迹 summary 导出、提交目录规范和 PR 模板要求。

It has not solved warehouse state modeling, order generation, SKU/bin/shelf modeling, mission planning, workflow execution, skill graphs, runtime scheduling, multi-agent coordination, optimization, traffic management, metrics, replay/debug tooling, physical validation APIs, or warehouse-specific scenes.

它没有解决仓库状态建模、订单生成、SKU/料箱/货架建模、任务规划、工作流执行、技能图、运行时调度、多智能体协同、优化、交通管理、指标、回放/调试工具、物理验证 API 或仓库专用场景。

## Fastest Path to a Warehouse Order Fulfillment Simulator / 仓库订单履约仿真器最快路径

Build the project as a layered simulation: Mission layer, Workflow layer, Skill Graph layer, Runtime layer, Multi-Agent Optimization layer, and MuJoCo validation layer.

将项目构建成分层仿真：Mission 层、Workflow 层、Skill Graph 层、Runtime 层、Multi-Agent Optimization 层，以及 MuJoCo 验证层。

The Mission layer receives orders, inventory, warehouse map, and fleet state, then outputs a fulfillment mission plan.

Mission 层接收订单、库存、仓库地图和车队状态，然后输出履约任务计划。

The Workflow layer decomposes orders into pick, move, handoff, pack, and deliver steps, while maintaining dependencies and completion criteria.

Workflow 层把订单拆解成拣选、移动、交接、打包和交付步骤，同时维护依赖关系和完成条件。

The Skill Graph layer defines reusable skills such as `navigate_to_zone`, `align_to_shelf`, `pick_item`, `place_in_tote`, `carry_tote`, `handoff_to_station`, `pack_order`, and `recover_from_blockage`.

Skill Graph 层定义可复用技能，例如 `navigate_to_zone`、`align_to_shelf`、`pick_item`、`place_in_tote`、`carry_tote`、`handoff_to_station`、`pack_order` 和 `recover_from_blockage`。

The Runtime layer simulates time, dispatches skills to agents, tracks resource locks, handles conflicts, and records event logs.

Runtime 层负责仿真时间推进、向智能体派发技能、追踪资源锁、处理冲突并记录事件日志。

The Multi-Agent Optimization layer assigns tasks, batches orders, routes agents through the aisle graph, resolves traffic conflicts, and optimizes makespan, lateness, distance, idle time, and congestion.

Multi-Agent Optimization 层负责任务分配、订单批处理、通过巷道图规划路径、解决交通冲突，并优化完工时间、延迟、距离、空闲时间和拥堵。

The MuJoCo validation layer should only validate selected low-level action snippets, such as carrying a box along a short path, placing an object at a station, avoiding shelf proxies, or checking pickup/drop-off pose plausibility.

MuJoCo 验证层只应验证选定的低层动作片段，例如沿短路径搬运箱子、把物体放到工位、避开货架代理几何，或检查拾取/放置姿态是否合理。

## Recommended Implementation Shape / 推荐实现形态

Place the new project under `submissions/warehouse-order-fulfillment/` and keep the starter assets untouched.

把新项目放在 `submissions/warehouse-order-fulfillment/` 下，并保持 starter 原始资产不被改动。

Use simple geometric boxes for shelves, bins, packages, stations, and aisles before adding any visual polish.

先用简单几何盒子表示货架、料箱、包裹、工作站和巷道，再考虑视觉打磨。

Use high-level agent simulation for orders and routing, then use MuJoCo only to validate representative physical actions.

用高层智能体仿真处理订单和路径规划，然后只用 MuJoCo 验证代表性的物理动作。

Produce one demo video, one trajectory JSON, and one metrics report showing fulfillment performance.

生成一个演示视频、一个轨迹 JSON 和一个展示履约表现的指标报告。

## Component Effort Estimate / 组件工程量估算

| Component / 组件 | Effort / 难度 | Reason / 原因 |
|---|---:|---|
| Repository setup and submission scaffold / 仓库设置与提交脚手架 | Easy | Template already exists / 模板已经存在 |
| Basic warehouse map / 基础仓库地图 | Easy | Simple boxes or generated geoms are enough / 简单盒子或生成 geom 即可 |
| Order and inventory model / 订单和库存模型 | Easy | Pure Python domain model / 纯 Python 领域模型 |
| Metrics and JSON logs / 指标与 JSON 日志 | Easy | Existing demos already write summaries / 现有 demo 已有 summary 模式 |
| Demo video generation / 演示视频生成 | Easy | Existing renderer pattern is reusable / 现有 renderer 模式可复用 |
| Mission planner / Mission 规划器 | Medium | Needs clean decomposition from orders to workflows / 需要把订单清晰拆成工作流 |
| Workflow engine / 工作流引擎 | Medium | Needs dependencies, states, and failure handling / 需要依赖、状态和失败处理 |
| Skill graph / 技能图 | Medium | Needs preconditions, effects, and resource locks / 需要前置条件、效果和资源锁 |
| Multi-agent scheduler / 多智能体调度器 | Medium | Heuristics are feasible; conflicts need care / 启发式可行，但冲突处理要仔细 |
| Aisle route planning / 巷道路径规划 | Medium | Shortest path is simple; congestion adds complexity / 最短路简单，拥堵增加复杂度 |
| MuJoCo warehouse scene / MuJoCo 仓库场景 | Medium | Boxes are easy; validation needs iteration / 盒子简单，验证需要迭代 |
| Carry-action validation / 搬运动作验证 | Medium | Futurist demo helps, but physical realism is limited / Futurist demo 有帮助，但物理真实度有限 |
| Advanced optimization / 高级优化 | Hard | MILP/CP-SAT/RL-style methods add time and dependencies / MILP/CP-SAT/RL 会增加时间和依赖 |
| Stable pick/place manipulation / 稳定拾取放置 | Hard | Starter does not provide grasp policies / starter 没有抓取策略 |
| Actuator-based humanoid control / 基于执行器的人形控制 | Hard | Requires a real control stack, not provided by starter / 需要真实控制栈，starter 未提供 |

## Recommended Scope for Hackathon Speed / 黑客松速度下的推荐范围

Must build: warehouse domain model, order fulfillment workflow, skill graph, multi-agent runtime, heuristic scheduler, metrics output, MuJoCo validation scene, and a demo script that produces video and JSON output.

必须构建：仓库领域模型、订单履约工作流、技能图、多智能体运行时、启发式调度器、指标输出、MuJoCo 验证场景，以及能生成视频和 JSON 输出的 demo 脚本。

Should defer: real grasp physics, full-body locomotion control, reinforcement learning, complex perception, photorealistic assets, large external robotics dependencies, and web dashboards.

应该推迟：真实抓取物理、全身步态控制、强化学习、复杂感知、照片级真实资产、大型外部机器人依赖和 Web 仪表盘。

## Key Architectural Recommendation / 核心架构建议

Keep MuJoCo behind a narrow validation interface: Warehouse Runtime -> Skill Execution -> Optional Physical Validator -> MuJoCo scene/action snippet -> pass/fail plus measurements.

把 MuJoCo 放在一个很窄的验证接口后面：Warehouse Runtime -> Skill Execution -> Optional Physical Validator -> MuJoCo scene/action snippet -> pass/fail plus measurements。

This keeps the project aligned with warehouse optimization while still satisfying the Robothon expectation of a runnable MuJoCo simulation.

这样可以让项目保持仓库优化的核心定位，同时满足 Robothon 对可运行 MuJoCo 仿真的期待。

## Risk Register / 风险清单

| Risk / 风险 | Severity / 严重性 | Mitigation / 缓解方式 |
|---|---:|---|
| Spending time on humanoid control instead of warehouse optimization / 把时间花在人形控制而不是仓库优化上 | High | Restrict MuJoCo to validation snippets / 限制 MuJoCo 只做验证片段 |
| Futurist lacks collision geometry / Futurist 缺少碰撞几何 | High | Add simple proxy collision geoms or use Master where needed / 添加简单代理碰撞几何，或必要时使用 Master |
| Demo looks like scripted animation only / demo 看起来只是脚本动画 | Medium | Show optimizer metrics, task assignments, and event logs / 展示优化指标、任务分配和事件日志 |
| Multi-agent optimization scope grows too large / 多智能体优化范围膨胀 | Medium | Start with deterministic heuristics, then add one improvement / 从确定性启发式开始，再添加一个优化点 |
| External model downloads hurt reproducibility / 外部模型下载影响可复现性 | Medium | Prefer checked-in starter assets first / 优先使用已提交的 starter 资产 |
| Submission must run cleanly / 提交必须顺利运行 | High | Keep install and run path minimal / 保持安装和运行路径最小化 |

## Conclusion / 结论

The starter repository is best understood as a MuJoCo asset and demo-generation foundation. It already solves robot asset loading, basic visualization, video generation, trajectory summaries, and submission packaging.

starter 仓库最适合理解为 MuJoCo 资产和 demo 生成基础。它已经解决了机器人资产加载、基础可视化、视频生成、轨迹摘要和提交包装。

It does not solve the warehouse-order-optimization problem, and it should not be treated as the main architecture for this project.

它没有解决仓库订单优化问题，也不应被当作本项目的主架构。

The fastest competitive project is to build a clear warehouse fulfillment simulator with a strong planning/runtime story, then use MuJoCo to validate and visualize selected low-level actions.

最快且有竞争力的项目路径，是构建一个清晰的仓库履约仿真器，突出规划和运行时能力，然后用 MuJoCo 验证和可视化选定的低层动作。

This keeps the architecture focused on Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization, with MuJoCo in its proper role as the physical-world validator.

这能让架构聚焦在 Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization，并让 MuJoCo 回到它合适的位置：物理世界验证器。

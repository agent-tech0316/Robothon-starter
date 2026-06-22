# Repository Scout Report

## 1. Current Finding

当前 starter repo 里已经可以复用 AEGIS 四足机器人模型，并且当前 submission 目录里已经做了三个仓储原子动作 demo：

- 机器狗带前置机械臂和篮子展示
- 从货架抓取包裹并放入篮子
- 两只机器狗之间交接包裹

最新版本里，包裹已经不再独立滑动，而是跟随夹爪腕部位置和姿态移动，并带有旋转。这个 demo 的重点不是完整机器人控制，而是为仓储订单优化项目提供低层动作的物理世界验证样例。

---

## 2. Relevant Files

- `assets/Aegis/urdf/Aegis_mujoco.urdf`
- `submissions/warehouse_quadbot_atomic_demos/run_quadbot_atomic_demos.py`
- `submissions/warehouse_quadbot_atomic_demos/outputs/arm_showcase.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/shelf_pick.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/handoff.mp4`
- `submissions/warehouse_quadbot_atomic_demos/outputs/preview_contact_sheet.png`
- `submissions/warehouse_quadbot_atomic_demos/outputs/*_trajectory.json`

---

## 3. What This Component Does

这个组件用于验证仓储任务里的低层原子动作：

- 四足机器人站在离散 tile 上
- 前置机械臂抓取包裹
- 包裹进入机器人背部篮子
- 两台机器人进行包裹交接
- MuJoCo 用来检查基本碰撞、接触、空间关系和动画合理性

它不是任务调度系统，也不是多智能体优化器。任务层应该继续保持在 Mission -> Workflow -> Skill Graph -> Runtime -> Multi-Agent Warehouse Optimization 的架构里。

---

## 4. Reusable Components

可直接复用：

- AEGIS 四足机器人 URDF
- MuJoCo 渲染流程
- 视频输出流程
- package / basket / shelf / tile 的 procedural scene 生成方式
- contact counters
- 原子动作 demo 结构
- 机械臂、夹爪、篮子的程序化附加装置
- `shelf_pick` 和 `handoff` 的夹爪跟随式包裹运动逻辑

---

## 5. MuJoCo Assets Involved

涉及：

- robot: `Aegis`
- scene: floor, tile, shelf, two-robot handoff layout
- mesh: AEGIS 自带 mesh
- texture: starter repo 自带材质；当前仓储 demo 主要使用 procedural rgba 材质
- package: cardboard / wood / metal 三种视觉和质量配置
- actuator: 当前 demo 主要是 scripted kinematic keyframes，不是完整 actuator control
- sensor: 当前 demo 未接入高级传感器，只读取 MuJoCo body pose / contact

---

## 6. Traps / Risks

主要风险：

- 当前抓取还不是完整闭环物理抓取，只是关键帧动作 + 夹爪跟随约束 + MuJoCo 碰撞验证。
- 如果后续做真实物理夹持，需要调 friction、solref、solimp、质量、接触 margin，成本会上升。
- AEGIS 原始模型是四足运动模型，不是仓储系统模型，不要把任务规划逻辑塞进 URDF/MuJoCo。
- 机械臂是程序化临时资产，不是官方真实机械臂模型。
- demo 视频会覆盖同名输出，目前不会不断生成新视频导致爆盘。
- 不建议在 starter 官方核心目录里直接改官方模型，除非最终 submission 规范要求。

---

## 7. Shortcuts

黑客松可利用捷径：

- 任务层用 Python 数据结构模拟，不必全部放进 MuJoCo。
- MuJoCo 只验证少量代表性原子动作。
- 包裹重量可以先用三档质量和颜色表达。
- 货架、tile、篮子都可以 procedural 生成，不必建复杂模型。
- 多智能体优化先在离散网格里跑，再把关键动作投影到 MuJoCo demo。
- 输出视频文件保持固定命名，方便反复覆盖和比较。

---

## 8. Recommendation

对于黑客松：

- 应该使用：AEGIS 机器人模型、现有 MuJoCo 渲染、当前 atomic demo 框架。
- 可以忽略：复杂机器人控制、真实 SLAM、真实感知 pipeline、完整动力学抓取。
- 不建议修改：官方 AEGIS 原始 URDF 和 starter repo 核心结构。
- 建议新增逻辑放在 `submissions/warehouse_quadbot_atomic_demos/` 或后续独立 submission 模块里。
- 后续如果要给多个智能体协作，建议把这个文件作为 handoff context 之一。

---

## 9. Questions

需要进一步调查：

- 官方评分是否更看重 MuJoCo 物理真实性，还是任务系统完整度？
- AEGIS 是否允许加装自定义机械臂和篮子作为 submission asset？
- 最终提交是否需要固定入口脚本？
- 多智能体调度结果是否需要可视化成完整 warehouse run，还是只展示关键原子动作即可？
- 是否需要把 `starter_analysis.md` 和 `starter_summary.md` 中的结论同步到一个更高层的 `docs/` 目录？

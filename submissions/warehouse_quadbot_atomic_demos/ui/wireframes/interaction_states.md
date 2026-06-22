# Interaction States

## Selection Rules

Selecting an order:

- Highlights the order row.
- Highlights assigned robot in Robot Panel.
- Highlights route on Warehouse Map.
- Filters Timeline to related events.
- Shows active workflow and skill graph steps for that order.

Selecting a robot:

- Highlights robot row.
- Highlights current tile and route.
- Highlights current order in Order Panel.
- Shows current target and next target.

Selecting a skill:

- Highlights active skill in Runtime Panel.
- Highlights related map operation if visible.
- Opens MuJoCo evidence only as supporting proof.

## Color Rules

Order waiting time:

- Green: fresh
- Yellow: aging
- Red: late

Robot status:

- idle: gray
- moving: cyan
- loading: yellow
- unloading: green
- blocked: red
- waiting: orange

Tile occupancy:

- free: neutral dark
- occupied: cyan outline
- reserved: yellow outline
- blocked: red fill

## Timeline Event Tags

```text
assignment | movement | completion | deadlock | replan | skill | throughput
```

Example visual:

```text
[00:12] assignment  Robot 3 assigned Order 28
[00:15] movement    Robot 2 entered Tile 5,8
[00:21] deadlock    Deadlock resolved
[00:24] replan      Replanning triggered
[00:29] completion  Order 19 completed
```

## Throughput Benchmark States

Healthy:

- Throughput trend is stable or rising.
- Pending orders are not aging into red.
- Deadlocks are low.

Warning:

- Throughput drops below target.
- Yellow orders increase.
- Replanning count rises.

Critical:

- Red orders increase.
- Deadlocks accumulate.
- Average completion time rises while throughput falls.

## Operations-Center Principle

Every interaction should answer one of these questions:

- What is the warehouse trying to complete?
- Which orders threaten throughput?
- What did the scheduler decide?
- Which robots are executing the plan?
- Where is the bottleneck?

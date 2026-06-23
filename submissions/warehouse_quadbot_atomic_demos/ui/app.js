"use strict";

const canvas = document.getElementById("warehouseCanvas");
const canvasCtx = canvas.getContext("2d");
const pixelCanvas = document.createElement("canvas");
const pixelCtx = pixelCanvas.getContext("2d");
let ctx = pixelCtx;
const DESIGN_SURFACE = { width: 3840, height: 2160 };
const GAME_PIXEL_RATIO = 1;
const SPRITE_VERSION = 28;
const PIXEL_PALETTE = {
  voidTop: "#091922",
  voidBottom: "#102534",
  floorA: "#2a4050",
  floorB: "#233746",
  floorEdge: "#142634",
  floorChip: "#3f6174",
  outline: "rgba(3,8,12,0.9)",
  cyan: "#18e0e6",
  cyanDim: "rgba(24,224,230,0.36)",
  orange: "#f28a1d",
  orangeDark: "#8e3d13",
  steelTop: "#8fa7b2",
  steelSide: "#405566",
  steelDark: "#1b2e3b",
};

const els = {
  runState: document.getElementById("runState"),
  simClock: document.getElementById("simClock"),
  fleetCount: document.getElementById("fleetCount"),
  selectedShelf: document.getElementById("selectedShelf"),
  pauseBtn: document.getElementById("pauseBtn"),
  tickBtn: document.getElementById("tickBtn"),
  resetBtn: document.getElementById("resetBtn"),
  recordBtn: document.getElementById("recordBtn"),
  topRuntime: document.getElementById("topRuntime"),
  topRobots: document.getElementById("topRobots"),
  topLocks: document.getElementById("topLocks"),
  topThroughput: document.getElementById("topThroughput"),
  topQueue: document.getElementById("topQueue"),
  topSla: document.getElementById("topSla"),
  plannerBtn: document.getElementById("plannerBtn"),
  activeLoadBadge: document.getElementById("activeLoadBadge"),
  speedBadge: document.getElementById("speedBadge"),
  recordBadge: document.getElementById("recordBadge"),
  tickLabel: document.getElementById("tickLabel"),
  decisionLog: document.getElementById("decisionLog"),
  wallClock: document.getElementById("wallClock"),
  ordersCompleted: document.getElementById("ordersCompleted"),
  throughputRate: document.getElementById("throughputRate"),
  activeOrders: document.getElementById("activeOrders"),
  pendingOrders: document.getElementById("pendingOrders"),
  throughputTrend: document.getElementById("throughputTrend"),
  baselineThroughput: document.getElementById("baselineThroughput"),
  localThroughput: document.getElementById("localThroughput"),
  safetyViolations: document.getElementById("safetyViolations"),
  throughputBars: document.getElementById("throughputBars"),
  utilization: document.getElementById("utilization"),
  congestion: document.getElementById("congestion"),
  fulfillment: document.getElementById("fulfillment"),
  queuePressure: document.getElementById("queuePressure"),
  queueA2: document.getElementById("queueA2"),
  queueB1: document.getElementById("queueB1"),
  queuePack: document.getElementById("queuePack"),
  pipelineState: document.getElementById("pipelineState"),
  activeSkillCount: document.getElementById("activeSkillCount"),
  deadlockCount: document.getElementById("deadlockCount"),
  replanCount: document.getElementById("replanCount"),
  leftTileLocks: document.getElementById("leftTileLocks"),
  schedulerDecision: document.getElementById("schedulerDecision"),
  judgeDecisionText: document.getElementById("judgeDecisionText"),
  judgeDecisionRobot: document.getElementById("judgeDecisionRobot"),
  judgeDecisionLock: document.getElementById("judgeDecisionLock"),
  judgeDecisionSkill: document.getElementById("judgeDecisionSkill"),
  plannerMetricOrders: document.getElementById("plannerMetricOrders"),
  plannerMetricLocks: document.getElementById("plannerMetricLocks"),
  plannerMetricReplans: document.getElementById("plannerMetricReplans"),
  plannerTableInput: document.getElementById("plannerTableInput"),
  plannerTableDecision: document.getElementById("plannerTableDecision"),
  plannerTableOutput: document.getElementById("plannerTableOutput"),
  plannerTextSummary: document.getElementById("plannerTextSummary"),
  fleetMode: document.getElementById("fleetMode"),
  robotStatusList: document.getElementById("robotStatusList"),
  orderTable: document.getElementById("orderTable"),
  selectedSkillStatus: document.getElementById("selectedSkillStatus"),
  skuMix: document.getElementById("skuMix"),
  skuInbound: document.getElementById("skuInbound"),
  skuPickQueue: document.getElementById("skuPickQueue"),
  skuOutbound: document.getElementById("skuOutbound"),
  orderFlowMode: document.getElementById("orderFlowMode"),
  orderNewCount: document.getElementById("orderNewCount"),
  orderAssignedCount: document.getElementById("orderAssignedCount"),
  orderAgingCount: document.getElementById("orderAgingCount"),
  orderIntakeList: document.getElementById("orderIntakeList"),
  runtimeLinkBadge: document.getElementById("runtimeLinkBadge"),
  humanRiskBadge: document.getElementById("humanRiskBadge"),
  humanModeBtn: document.getElementById("humanModeBtn"),
  runtimeControlState: document.getElementById("runtimeControlState"),
  runtimeSnapshotPort: document.getElementById("runtimeSnapshotPort"),
  robotsPort: document.getElementById("robotsPort"),
  ordersPort: document.getElementById("ordersPort"),
  locksPort: document.getElementById("locksPort"),
  zoneHealth: document.getElementById("zoneHealth"),
  contractState: document.getElementById("contractState"),
  recorderPort: document.getElementById("recorderPort"),
  thinPending: document.getElementById("thinPending"),
  thinReplans: document.getElementById("thinReplans"),
  thinDeadlocks: document.getElementById("thinDeadlocks"),
  thinSkills: document.getElementById("thinSkills"),
  thinRun: document.getElementById("thinRun"),
  detailModeBtn: document.getElementById("detailModeBtn"),
};

let grid = { cols: 16, rows: 12 };
let view = { width: 0, height: 0, tileW: 72, tileH: 38, originX: 0, originY: 0 };

const shelvesSeed = [
  { id: "A1", x: 3, y: 1, w: 1, d: 3, length: 3, direction: "ne", material: "cardboard", fill: "full", anchorX: 4, anchorY: 4 },
  { id: "A2", x: 6, y: 1, w: 1, d: 3, length: 3, direction: "ne", material: "metal", fill: "half", anchorX: 7, anchorY: 4 },
  { id: "A3", x: 9, y: 1, w: 1, d: 3, length: 3, direction: "ne", material: "wood", fill: "full", anchorX: 10, anchorY: 4 },
  { id: "A4", x: 12, y: 1, w: 1, d: 2, length: 2, direction: "ne", material: "cardboard", fill: "full", anchorX: 13, anchorY: 3 },
  { id: "B1", x: 3, y: 6, w: 1, d: 3, length: 3, direction: "ne", material: "wood", fill: "half", anchorX: 4, anchorY: 9 },
  { id: "B2", x: 6, y: 6, w: 1, d: 3, length: 3, direction: "ne", material: "cardboard", fill: "almost_none", anchorX: 7, anchorY: 9 },
  { id: "B3", x: 9, y: 6, w: 1, d: 3, length: 3, direction: "ne", material: "metal", fill: "half", anchorX: 10, anchorY: 9 },
  { id: "B4", x: 12, y: 6, w: 1, d: 2, length: 2, direction: "ne", material: "wood", fill: "empty", anchorX: 13, anchorY: 8 },
];

const zones = [
  { id: "DEPOT", x: 0, y: 11, w: 3, d: 3, color: "#38cae8" },
  { id: "CHARGE", x: 0, y: 0, w: 2, d: 1, color: "#38cae8" },
];

const ledTiles = {
  rest: [[0, 11], [1, 11], [2, 11], [0, 12], [1, 12], [2, 12], [0, 13], [1, 13], [2, 13]],
  delivery: [[19, 11], [16, 13], [16, 0], [0, 6]],
  route: [[4, 5], [5, 5]],
  congestion: [[5, 5]],
  pick: [[4, 2], [7, 2]],
};

const fallbackConveyors = [
  { conveyor_id: "CONV_EAST_01", unload_tile_id: "T_19_11", direction: "E", wall: "east", exterior_footprint: { x: 20, y: 11, w: 2, d: 1 }, door_line: { x1: 22, y1: 11, x2: 22, y2: 12 } },
  { conveyor_id: "CONV_SOUTH_01", unload_tile_id: "T_16_13", direction: "S", wall: "south", exterior_footprint: { x: 16, y: 14, w: 1, d: 2 }, door_line: { x1: 16, y1: 16, x2: 17, y2: 16 } },
  { conveyor_id: "CONV_NORTH_01", unload_tile_id: "T_16_00", direction: "N", wall: "north", exterior_footprint: { x: 16, y: -2, w: 1, d: 2 }, door_line: { x1: 16, y1: -2, x2: 17, y2: -2 } },
  { conveyor_id: "CONV_WEST_01", unload_tile_id: "T_00_06", direction: "W", wall: "west", exterior_footprint: { x: -2, y: 6, w: 2, d: 1 }, door_line: { x1: -2, y1: 6, x2: -2, y2: 7 } },
];

const facilitySprites = [
  { id: "SERVER", category: "visual", sprite: () => `computer_terminal_1x1_s_frame_${String(animationFrame()).padStart(2, "0")}`, x: 1, y: 2, depth: 4.0, label: "ORDERS", color: "#38cae8" },
];

function conveyorDirection(conveyor) {
  const direction = String(conveyor?.direction || conveyor?.wall || "E").trim().toLowerCase()[0] || "e";
  return ["e", "s", "w", "n"].includes(direction) ? direction : "e";
}

function conveyorUnloadPoint(conveyor) {
  return tileIdToPoint(conveyor?.unload_tile_id) || [0, 0];
}

function conveyorExteriorFootprint(conveyor, direction, unload) {
  const raw = conveyor?.exterior_footprint;
  if (raw && Number.isFinite(Number(raw.x)) && Number.isFinite(Number(raw.y))) {
    return {
      x: Number(raw.x),
      y: Number(raw.y),
      w: Math.max(0.25, Number(raw.w || raw.width || 1)),
      d: Math.max(0.25, Number(raw.d || raw.depth || 1)),
    };
  }
  const length = Math.max(1, Number(conveyor?.length_tiles || 2));
  if (direction === "e") return { x: unload[0] + 1, y: unload[1], w: length, d: 1 };
  if (direction === "w") return { x: unload[0] - length, y: unload[1], w: length, d: 1 };
  if (direction === "s") return { x: unload[0], y: unload[1] + 1, w: 1, d: length };
  return { x: unload[0], y: unload[1] - length, w: 1, d: length };
}

function conveyorAnchorFromFootprint(direction, footprint) {
  if (direction === "e") return { x: footprint.x + footprint.w + 0.2, y: footprint.y + footprint.d * 0.74 };
  if (direction === "w") return { x: footprint.x + 0.8, y: footprint.y + footprint.d * 0.74 };
  if (direction === "s") return { x: footprint.x + footprint.w * 0.74, y: footprint.y + footprint.d + 0.2 };
  return { x: footprint.x + footprint.w * 0.74, y: footprint.y + 0.8 };
}

function conveyorDoorLine(conveyor, direction, footprint) {
  const raw = conveyor?.door_line;
  if (raw && [raw.x1, raw.y1, raw.x2, raw.y2].every((value) => Number.isFinite(Number(value)))) {
    return { x1: Number(raw.x1), y1: Number(raw.y1), x2: Number(raw.x2), y2: Number(raw.y2) };
  }
  if (direction === "e") return { x1: footprint.x + footprint.w, y1: footprint.y, x2: footprint.x + footprint.w, y2: footprint.y + footprint.d };
  if (direction === "w") return { x1: footprint.x, y1: footprint.y, x2: footprint.x, y2: footprint.y + footprint.d };
  if (direction === "s") return { x1: footprint.x, y1: footprint.y + footprint.d, x2: footprint.x + footprint.w, y2: footprint.y + footprint.d };
  return { x1: footprint.x, y1: footprint.y, x2: footprint.x + footprint.w, y2: footprint.y };
}

function conveyorVisualFromRuntime(conveyor, index = 0) {
  const direction = conveyorDirection(conveyor);
  const unload = conveyorUnloadPoint(conveyor);
  const footprint = conveyorExteriorFootprint(conveyor, direction, unload);
  const anchor = conveyorAnchorFromFootprint(direction, footprint);
  return {
    id: conveyor?.conveyor_id || `CONV-${index + 1}`,
    category: "visual",
    sprite: () => `exit_gate_conveyor_3x1_${direction}_frame_${String(animationFrame()).padStart(2, "0")}`,
    x: anchor.x,
    y: anchor.y,
    depth: Math.max(unload[0] + unload[1], footprint.x + footprint.y + footprint.w + footprint.d) + 22 + index * 0.01,
    label: "BELT",
    color: "#5cdd61",
    shadow: { x: footprint.x, y: footprint.y, w: footprint.w, d: footprint.d },
    doorLine: conveyorDoorLine(conveyor, direction, footprint),
  };
}

function runtimeConveyors() {
  const conveyors = state.runtimeSnapshot?.warehouse?.conveyors || [];
  return conveyors.length ? conveyors : fallbackConveyors;
}

function activeFacilitySprites() {
  return [
    ...facilitySprites,
    ...runtimeConveyors().map((conveyor, index) => conveyorVisualFromRuntime(conveyor, index)),
  ];
}

function makeOrthRoute(points) {
  const route = [];
  const pushCenter = (x, y) => {
    const point = [x + 0.5, y + 0.5];
    const previous = route[route.length - 1];
    if (!previous || previous[0] !== point[0] || previous[1] !== point[1]) route.push(point);
  };

  points.forEach(([targetX, targetY], index) => {
    if (index === 0) {
      pushCenter(targetX, targetY);
      return;
    }
    let [x, y] = points[index - 1];
    while (x !== targetX) {
      x += Math.sign(targetX - x);
      pushCenter(x, y);
    }
    while (y !== targetY) {
      y += Math.sign(targetY - y);
      pushCenter(x, y);
    }
  });
  return route;
}

const routeSets = [
  makeOrthRoute([[0, 10], [2, 10], [2, 5], [5, 5], [5, 4], [8, 4], [8, 9], [14, 9], [14, 10]]),
  makeOrthRoute([[1, 0], [2, 0], [2, 4], [5, 4], [5, 5], [8, 5], [8, 10], [11, 10]]),
  makeOrthRoute([[0, 9], [2, 9], [2, 5], [4, 5], [4, 4], [10, 4], [10, 9], [14, 9]]),
  makeOrthRoute([[15, 10], [14, 10], [14, 9], [11, 9], [11, 5], [8, 5], [8, 4], [4, 4], [4, 9], [1, 9]]),
  makeOrthRoute([[1, 10], [2, 10], [2, 5], [5, 5], [5, 9], [8, 9], [8, 5], [11, 5], [11, 10]]),
  makeOrthRoute([[10, 10], [10, 9], [8, 9], [8, 5], [5, 5], [5, 4], [2, 4], [2, 1]]),
  makeOrthRoute([[1, 1], [2, 1], [2, 4], [4, 4], [4, 5], [7, 5], [7, 9], [10, 9], [10, 10]]),
  makeOrthRoute([[15, 11], [14, 11], [14, 9], [11, 9], [11, 5], [14, 5], [14, 1], [13, 1]]),
  makeOrthRoute([[0, 10], [1, 10], [1, 9], [2, 9], [2, 5], [5, 5], [5, 9], [8, 9], [8, 10], [14, 10]]),
];

const robotPalette = ["#38cae8", "#f7b733", "#5cdd61", "#b980ff", "#ff6848", "#d2d8dd", "#52a7ff", "#a0ce60"];

const orderSeed = [
  { id: "ORD-028", priority: "P1", difficulty: "hard", weight: 4.0, robot: "Q-03", age: 188, status: "assigned" },
  { id: "ORD-019", priority: "P2", difficulty: "med", weight: 2.0, robot: "Q-02", age: 102, status: "moving" },
  { id: "ORD-044", priority: "P1", difficulty: "hard", weight: 4.0, robot: "Q-07", age: 151, status: "loading" },
  { id: "ORD-031", priority: "P3", difficulty: "easy", weight: 0.8, robot: "-", age: 44, status: "pending" },
  { id: "ORD-052", priority: "P2", difficulty: "med", weight: 2.0, robot: "Q-06", age: 83, status: "assigned" },
  { id: "ORD-061", priority: "P1", difficulty: "hard", weight: 4.0, robot: "Q-04", age: 214, status: "blocked" },
  { id: "ORD-017", priority: "P3", difficulty: "easy", weight: 0.8, robot: "Q-01", age: 33, status: "packing" },
];

const robotTaskSeed = [
  { order: "ORD-017", target: "DEPOT", next: "A1-04", sku: "-", weight: "-" },
  { order: "ORD-019", target: "TILE 5,8", next: "PACK-1", sku: "WOOD", weight: "2.0" },
  { order: "ORD-028", target: "A2-07", next: "PACK-2", sku: "METAL", weight: "4.0" },
  { order: "ORD-061", target: "B2-04", next: "BUFFER", sku: "METAL", weight: "4.0" },
  { order: "ORD-036", target: "A3-02", next: "OUT-1", sku: "CARD", weight: "0.8" },
  { order: "ORD-052", target: "PACK-1", next: "OUT-2", sku: "WOOD", weight: "2.0" },
  { order: "ORD-044", target: "A2-11", next: "HANDOFF", sku: "METAL", weight: "4.0" },
  { order: "-", target: "CHARGE", next: "DEPOT", sku: "-", weight: "-" },
  { order: "ORD-073", target: "A4-03", next: "PACK-3", sku: "CARD", weight: "0.8" },
];

function cloneData(value) {
  return JSON.parse(JSON.stringify(value));
}

const state = {
  running: true,
  planner: true,
  speed: 1,
  load: "high",
  simTime: 9300,
  tick: 0,
  focusSkill: "shelf_pick",
  shelves: cloneData(shelvesSeed),
  selectedShelfId: "A2",
  dragShelf: null,
  dragOffset: { x: 0, y: 0 },
  log: [
    "Runtime initialized with medium load release.",
    "Skill graph linked to MuJoCo shelf_pick and handoff evidence.",
    "Congestion-aware planner assigned A2 priority route.",
  ],
  runtimeLinked: false,
  runtimeSnapshot: null,
  runtimeMetrics: null,
  runtimeEvents: [],
  runtimeEventIndex: 0,
  runtimeReplayStartTick: 0,
  runtimeReplayEndTick: 0,
  runtimeReplayTick: 0,
  runtimeOrderBook: new Map(),
  runtimeActiveLocks: new Map(),
  runtimeBlockedTiles: new Set(),
  runtimeOccupiedTiles: new Map(),
  humanIntrusionEnabled: true,
  humanScenario: null,
  orders: cloneData(orderSeed),
  ledTiles: cloneData(ledTiles),
  recording: false,
  recorder: null,
  recordChunks: [],
  robots: routeSets.map((route, index) => ({
    id: `Q-${String(index + 1).padStart(2, "0")}`,
    route,
    phase: index / routeSets.length,
    color: robotPalette[index],
    battery: 86 - index * 4,
    carrying: index % 3 === 0,
  })),
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[char]));
}

function tileIdToPoint(tileId) {
  const match = /^T_(\d+)_(\d+)$/.exec(tileId || "");
  if (!match) return null;
  return [Number(match[1]), Number(match[2])];
}

function pointToTileId(point) {
  if (!Array.isArray(point) || point.length < 2) return null;
  const x = Math.floor(Number(point[0]));
  const y = Math.floor(Number(point[1]));
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return `T_${String(x).padStart(2, "0")}_${String(y).padStart(2, "0")}`;
}

function normalizeTileId(tileId) {
  const point = tileIdToPoint(tileId);
  return point ? pointToTileId(point) : null;
}

function tileIdToCenter(tileId) {
  const point = tileIdToPoint(tileId);
  return point ? [point[0] + 0.5, point[1] + 0.5] : null;
}

function pointToCenter(point) {
  if (!Array.isArray(point) || point.length < 2) return [0.5, 0.5];
  return [Number(point[0]) + 0.5, Number(point[1]) + 0.5];
}

function tileCenterOrNull(tileId) {
  const center = tileIdToCenter(tileId);
  return center && center.every(Number.isFinite) ? center : null;
}

function tileIdsAreCardinalNeighbors(a, b) {
  const pa = tileIdToPoint(a);
  const pb = tileIdToPoint(b);
  if (!pa || !pb) return false;
  return Math.abs(pa[0] - pb[0]) + Math.abs(pa[1] - pb[1]) === 1;
}

function tileInBounds(tileId) {
  const point = tileIdToPoint(tileId);
  if (!point) return false;
  return point[0] >= 0 && point[1] >= 0 && point[0] < grid.cols && point[1] < grid.rows;
}

function compactTileLabel(tileId) {
  const point = tileIdToPoint(tileId);
  if (!point) return tileId || "-";
  return `T${point[0]},${point[1]}`;
}

function materialFromSku(sku) {
  const value = String(sku || "").toUpperCase();
  if (value.includes("WOOD")) return "wood";
  if (value.includes("METAL") || value.includes("TOOL")) return "metal";
  return "cardboard";
}

function difficultyFromLabel(value) {
  const label = String(value || "").toLowerCase();
  if (label.includes("hard")) return "hard";
  if (label.includes("med")) return "med";
  return label || "easy";
}

function statusFromRuntime(status, robot = {}) {
  const value = String(status || "").toLowerCase();
  if (["ready", "idle"].includes(value)) return "IDLE";
  if (value.includes("handoff") || value.includes("exchange")) return "EXCHANGE";
  if (["picking", "loading"].includes(value)) return "LOADING";
  if (["unloading", "unloading_at_conveyor"].includes(value)) return "UNLOADING";
  if (["waiting_for_tile_lock", "blocked", "error"].includes(value)) return robot.waitTicks > 0 ? "BLOCKED" : "WAITING";
  if (value.includes("navigating") || value.includes("relocating")) return "MOVING";
  return value ? value.toUpperCase() : "IDLE";
}

function normalizeRuntimeRoute(robot) {
  const route = Array.isArray(robot.route) ? robot.route.map(pointToCenter) : [];
  if (!route.length) {
    if (robot.tile_id) return [tileIdToCenter(robot.tile_id) || [Number(robot.x || 0) + 0.5, Number(robot.y || 0) + 0.5]];
    return [[Number(robot.x || 0) + 0.5, Number(robot.y || 0) + 0.5]];
  }
  return route;
}

function routeTileIds(route) {
  const ids = [];
  (route || []).forEach((point) => {
    const id = pointToTileId(point);
    if (id && ids[ids.length - 1] !== id) ids.push(id);
  });
  return ids;
}

function normalizeRuntimeRobot(robot, index) {
  const route = normalizeRuntimeRoute(robot);
  const routeTiles = routeTileIds(route);
  const currentTileId = normalizeTileId(robot.tile_id) || routeTiles[0] || null;
  const nextTileId = normalizeTileId(robot.next_target);
  const status = statusFromRuntime(robot.status, { waitTicks: Number(robot.wait_ticks || 0) });
  const currentOrder = robot.current_order || "-";
  const carriedSku = robot.carried_sku || "-";
  const carriedWeight = robot.carried_weight_kg ?? "-";
  const lockTiles = Array.isArray(robot.lock_tiles) ? robot.lock_tiles.map(normalizeTileId).filter(Boolean) : [];
  const waitTicks = Number(robot.wait_ticks || 0);
  return {
    id: robot.id || `Q-${String(index + 1).padStart(2, "0")}`,
    route,
    routeTiles,
    routeClosed: robot.route_closed === true,
    phase: 0,
    color: robotPalette[index % robotPalette.length],
    battery: Number(robot.battery ?? 86),
    carrying: Boolean(robot.carrying || robot.carried_sku),
    runtimeStatus: robot.status || "ready",
    status,
    tileId: currentTileId,
    nextTileId,
    heading: robot.heading,
    currentOrder,
    currentTarget: compactTileLabel(robot.current_target),
    nextTarget: compactTileLabel(robot.next_target),
    carriedSku,
    carriedWeight,
    carriedMaterial: materialFromSku(carriedSku),
    waitTicks,
    lockTiles,
    lockPressurePct: clamp(waitTicks * 12 + lockTiles.length * 18, 18, 96),
    utilizationPct: clamp(100 - Number(robot.battery ?? 86) * 0.35 + (status === "MOVING" ? 36 : 12), 18, 96),
    visualPose: null,
    visualTileId: currentTileId,
    motionDirection: 1,
    motion: null,
  };
}

function normalizeRuntimeShelf(shelf) {
  return {
    id: shelf.id,
    x: Number(shelf.x || 0),
    y: Number(shelf.y || 0),
    w: Number(shelf.w || 1),
    d: Number(shelf.d || 1),
    h: Number(shelf.h || 1.35),
    length: Number(shelf.length || Math.max(Number(shelf.w || 1), Number(shelf.d || 1))),
    direction: shelf.direction || "ne",
    material: shelf.material || "cardboard",
    fill: shelf.fill || "full",
    anchorX: Number(shelf.anchorX ?? (Number(shelf.x || 0) + Number(shelf.w || 1))),
    anchorY: Number(shelf.anchorY ?? (Number(shelf.y || 0) + Number(shelf.d || 1))),
    footprint_tiles: shelf.footprint_tiles || [],
    pick_tiles: shelf.pick_tiles || [],
    blocks_robot: shelf.blocks_robot !== false,
  };
}

function normalizeRuntimeOrders(rows) {
  return (rows || []).map((order) => ({
    id: order.id || "ORD--",
    priority: order.priority || "P2",
    difficulty: difficultyFromLabel(order.difficulty),
    weight: Number(order.weight_kg || 0),
    robot: order.assigned_robot || "-",
    age: Number(order.age_s || 0),
    status: order.status || "pending",
  }));
}

function uniqueRuntimeLockTiles(snapshot) {
  const tiles = new Set();
  (snapshot?.robots || []).forEach((robot) => (robot.lock_tiles || []).forEach((tile) => {
    const id = normalizeTileId(tile);
    if (id) tiles.add(id);
  }));
  (snapshot?.movement_locks?.occupied_tiles || []).forEach((entry) => {
    const id = normalizeTileId(entry.tile_id);
    if (id) tiles.add(id);
  });
  return tiles.size;
}

function blockedRuntimeTileSet(snapshot) {
  const ids = [
    ...(snapshot?.warehouse?.blocked_tiles || []),
    ...(snapshot?.warehouse?.rack_tiles || []),
  ];
  return new Set(ids.map(normalizeTileId).filter(Boolean));
}

function occupiedRuntimeTileMap(snapshot) {
  const occupied = new Map();
  (snapshot?.movement_locks?.occupied_tiles || []).forEach((entry) => {
    const tileId = normalizeTileId(entry.tile_id);
    if (tileId) occupied.set(tileId, entry.robot_id || "");
  });
  return occupied;
}

function ledTilesFromRuntime(snapshot) {
  const denied = snapshot?.movement_locks?.denied_moves || [];
  const rackPickTiles = (snapshot?.shelves || []).flatMap((shelf) => shelf.pick_tiles || []);
  const dropTileIds = (snapshot?.warehouse?.drop_tiles?.length
    ? snapshot.warehouse.drop_tiles
    : (snapshot?.warehouse?.conveyors || []).map((conveyor) => conveyor.unload_tile_id));
  return {
    rest: (snapshot?.warehouse?.depot_tiles || []).map(tileIdToPoint).filter(Boolean),
    delivery: dropTileIds.map((tile) => tileIdToPoint(tile)).filter(Boolean),
    route: (snapshot?.movement_locks?.granted_moves || []).map((move) => tileIdToPoint(move.destination_tile)).filter(Boolean),
    congestion: denied.map((move) => tileIdToPoint(move.destination_tile)).filter(Boolean),
    pick: rackPickTiles.slice(0, 4).map(tileIdToPoint).filter(Boolean),
  };
}

async function fetchJsonOrNull(url) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

async function fetchTextOrNull(url) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.text();
  } catch {
    return null;
  }
}

function parseRuntimeEvents(text) {
  if (!text) return [];
  return text
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean)
    .sort((a, b) => Number(a.tick || 0) - Number(b.tick || 0));
}

function pushRuntimeLog(message) {
  if (!message) return;
  state.log.push(message);
  if (state.log.length > 22) state.log.shift();
}

function runtimeOrderPriority(label) {
  const value = String(label || "").toLowerCase();
  if (value.includes("high")) return "P1";
  if (value.includes("low")) return "P3";
  return "P2";
}

function runtimeOrderWeightFromSku(sku) {
  const value = String(sku || "").toUpperCase();
  if (value.includes("HEAVY") || value.includes("METAL")) return 4.0;
  if (value.includes("WOOD") || value.includes("MEDICAL") || value.includes("BIN")) return 2.0;
  return 0.8;
}

function runtimeOrderDifficultyFromSku(sku) {
  const value = String(sku || "").toUpperCase();
  if (value.includes("HEAVY") || value.includes("METAL")) return "hard";
  if (value.includes("WOOD") || value.includes("MEDICAL") || value.includes("BIN")) return "med";
  return "easy";
}

function parseCreatedOrder(message, payload = {}) {
  const match = /Created\s+(\S+)\s+(\S+)\s+(\S+)\./.exec(message || "");
  const orderId = payload.order_id || match?.[1] || "ORD-RUNTIME";
  const sku = match?.[2] || "SKU_CARD_SMALL";
  const priorityLabel = match?.[3] || "normal";
  return { orderId, sku, priorityLabel };
}

function parseAssignedTarget(message) {
  const match = /for\s+(T_\d+_\d+)\./.exec(message || "");
  return normalizeTileId(match?.[1]);
}

function parseLockTile(message) {
  const match = /tile\s+(T_\d+_\d+)/.exec(message || "");
  return normalizeTileId(match?.[1]);
}

function parsePickedSku(message) {
  const match = /picked\s+([A-Z0-9_]+)/.exec(message || "");
  return match?.[1] || null;
}

function upsertRuntimeOrder(orderId, patch = {}) {
  if (!orderId) return null;
  const existing = state.runtimeOrderBook.get(orderId) || {
    id: orderId,
    priority: "P2",
    difficulty: "easy",
    weight: 0.8,
    robot: "-",
    age: 0,
    status: "pending",
    sku: "SKU_CARD_SMALL",
    createdTick: state.runtimeReplayTick || state.runtimeReplayStartTick || 0,
  };
  const next = { ...existing, ...patch };
  state.runtimeOrderBook.set(orderId, next);
  return next;
}

function syncRuntimeOrderRows() {
  const now = state.runtimeReplayTick || state.tick || 0;
  const statusRank = {
    picking: 0,
    dropping: 1,
    handoff: 2,
    navigating_to_conveyor: 3,
    navigating_to_rack: 4,
    assigned: 5,
    pending: 6,
    completed: 9,
  };
  state.orders = Array.from(state.runtimeOrderBook.values())
    .map((order) => ({
      id: order.id,
      priority: order.priority || "P2",
      difficulty: difficultyFromLabel(order.difficulty),
      weight: Number(order.weight || 0.8),
      robot: order.robot || "-",
      age: Math.max(0, Math.floor(now - Number(order.createdTick || now))),
      status: order.status || "pending",
    }))
    .sort((a, b) => (statusRank[a.status] ?? 7) - (statusRank[b.status] ?? 7) || b.age - a.age)
    .slice(0, 36);
}

function findRuntimeRobot(robotId) {
  return state.robots.find((robot) => robot.id === robotId) || null;
}

function setRuntimeActiveLock(tileId, robotId, reason, untilTick) {
  const id = normalizeTileId(tileId);
  if (!id) return;
  state.runtimeActiveLocks.set(id, { robotId, reason: reason || "reserved", untilTick });
}


function normalizeHumanScenario(snapshot) {
  const scenario = snapshot?.human_intrusion || null;
  if (!scenario?.enabled || !Array.isArray(scenario.agents)) return null;
  return scenario;
}

function humanScenarioTick() {
  return Math.floor(state.runtimeEvents.length ? state.runtimeReplayTick : state.tick || 0);
}

function interpolateHumanPath(path, progress) {
  const points = Array.isArray(path) ? path : [];
  if (!points.length) return { x: 0.5, y: 0.5 };
  if (points.length === 1) return { x: Number(points[0][0] || 0.5), y: Number(points[0][1] || 0.5) };
  const scaled = clamp(progress, 0, 1) * (points.length - 1);
  const index = Math.min(points.length - 2, Math.floor(scaled));
  const local = scaled - index;
  const a = points[index] || points[0];
  const b = points[index + 1] || a;
  const ax = Number(a[0] || 0);
  const ay = Number(a[1] || 0);
  const bx = Number(b[0] || ax);
  const by = Number(b[1] || ay);
  return { x: ax + (bx - ax) * local, y: ay + (by - ay) * local };
}

function humanPositionAt(agent, tick) {
  const start = Number(agent.start_tick || 0);
  const exit = Math.max(start + 1, Number(agent.exit_tick || start + 1));
  const activeDuration = exit - start;
  let progress = clamp((tick - start) / activeDuration, 0, 1);
  let mode = "walking";
  (agent.stop_windows || []).forEach((window) => {
    const windowStart = Number(window.start_tick ?? window.start ?? 0);
    const windowEnd = Number(window.end_tick ?? window.end ?? 0);
    if (tick >= windowStart && tick <= windowEnd) {
      progress = clamp((windowStart - start) / activeDuration, 0, 1);
      mode = "stopped";
    }
  });
  (agent.burst_windows || []).forEach((window) => {
    const windowStart = Number(window.start_tick ?? window.start ?? 0);
    const windowEnd = Number(window.end_tick ?? window.end ?? 0);
    if (tick >= windowStart && tick <= windowEnd) {
      const boost = Number(window.speed_multiplier || 1.6);
      progress = clamp(progress + ((tick - windowStart) / activeDuration) * (boost - 1), 0, 1);
      mode = "running";
    }
  });
  return { ...interpolateHumanPath(agent.path, progress), mode };
}

function riskTilesForHumanPosition(x, y, radiusTiles = 0.85) {
  const tiles = new Set();
  const minX = Math.max(0, Math.floor(x - radiusTiles));
  const maxX = Math.min(grid.cols - 1, Math.floor(x + radiusTiles));
  const minY = Math.max(0, Math.floor(y - radiusTiles));
  const maxY = Math.min(grid.rows - 1, Math.floor(y + radiusTiles));
  for (let ty = minY; ty <= maxY; ty += 1) {
    for (let tx = minX; tx <= maxX; tx += 1) {
      const distance = Math.hypot(tx + 0.5 - x, ty + 0.5 - y);
      const tileId = pointToTileId([tx, ty]);
      if (distance <= radiusTiles + 0.72 && !state.runtimeBlockedTiles.has(tileId)) tiles.add(tileId);
    }
  }
  return tiles;
}

function activeHumanAgents() {
  if (!state.humanIntrusionEnabled || !state.humanScenario?.enabled) return [];
  const tick = humanScenarioTick();
  return (state.humanScenario.agents || [])
    .filter((agent) => tick >= Number(agent.start_tick || 0) && tick <= Number(agent.exit_tick || 0))
    .map((agent) => {
      const position = humanPositionAt(agent, tick);
      const riskTiles = Array.from(riskTilesForHumanPosition(position.x, position.y, Number(agent.safety_radius_tiles || 0.85)));
      return {
        id: agent.human_id || "HUMAN",
        groupId: agent.group_id || "solo",
        profile: agent.profile || "visitor",
        x: position.x,
        y: position.y,
        mode: position.mode,
        color: agent.color || "#ffbf3d",
        safetyRadius: Number(agent.safety_radius_tiles || 0.85),
        riskTiles,
      };
    });
}

function currentHumanRiskTileIds(humans = activeHumanAgents()) {
  const tiles = new Set();
  humans.forEach((human) => human.riskTiles.forEach((tileId) => tiles.add(tileId)));
  return tiles;
}

function currentHumanRiskTilePoints(humans = activeHumanAgents()) {
  return Array.from(currentHumanRiskTileIds(humans)).map(tileIdToPoint).filter(Boolean);
}

function humanScenarioSummary(humans = activeHumanAgents()) {
  if (!state.humanIntrusionEnabled) return "Human intrusion disabled";
  if (!state.humanScenario?.enabled) return "Human runtime not loaded";
  const riskCount = currentHumanRiskTileIds(humans).size;
  return `${humans.length} humans / ${riskCount} risk tiles`;
}

function pruneRuntimeActiveLocks() {
  const now = state.runtimeReplayTick || state.tick || 0;
  Array.from(state.runtimeActiveLocks.entries()).forEach(([tileId, lock]) => {
    if (Number(lock.untilTick || 0) < now) state.runtimeActiveLocks.delete(tileId);
  });
}

function currentRuntimeLockTileIds() {
  pruneRuntimeActiveLocks();
  const tiles = new Set();
  state.runtimeActiveLocks.forEach((_, tileId) => tiles.add(tileId));
  state.robots.forEach((robot) => (robot.lockTiles || []).forEach((tileId) => {
    const id = normalizeTileId(tileId);
    if (id) tiles.add(id);
  }));
  return tiles;
}

function currentRuntimeLockTilePoints() {
  return Array.from(currentRuntimeLockTileIds()).map(tileIdToPoint).filter(Boolean);
}

function runtimeLockCount(snapshot) {
  if (state.runtimeEvents.length) return currentRuntimeLockTileIds().size;
  return snapshot ? uniqueRuntimeLockTiles(snapshot) : state.robots.length * 2 + (state.load === "high" ? 7 : state.load === "low" ? 2 : 4);
}

function nextSkillForRobotStatus(status, deniedMoves) {
  if (status === "LOADING") return "shelf_pick";
  if (status === "UNLOADING") return "drop_off";
  if (status === "EXCHANGE" || status === "HANDOFF") return "handoff";
  if (status === "WAITING" || status === "BLOCKED" || deniedMoves.length) return "replan";
  return "route_lock";
}

function currentJudgeDecision(snapshot, runtime, movementLocks) {
  const deniedMoves = movementLocks.denied_moves || [];
  const grantedMoves = movementLocks.granted_moves || [];
  const humans = activeHumanAgents();
  const humanRiskTiles = currentHumanRiskTileIds(humans);
  const activeRobot = state.robots.find((robot) => {
    const status = robotStatus(robot);
    return robot.currentOrder && robot.currentOrder !== "-" && status !== "IDLE";
  }) || state.robots[0] || {};
  const status = robotStatus(activeRobot || {});
  const lockTile = activeRobot.lockTiles?.[0]
    || grantedMoves.find((move) => move.robot_id === activeRobot.id)?.destination_tile
    || deniedMoves.find((move) => move.robot_id === activeRobot.id)?.destination_tile
    || grantedMoves[0]?.destination_tile
    || activeRobot.tileId
    || "T_00_00";
  const skill = nextSkillForRobotStatus(status, deniedMoves);
  const order = activeRobot.currentOrder && activeRobot.currentOrder !== "-" ? activeRobot.currentOrder : "next priority order";
  const baseText = runtime.latest_decision || state.log[state.log.length - 1] || "Planner is selecting the next safe route.";
  if (state.humanIntrusionEnabled && humans.length) {
    const firstRiskTile = Array.from(humanRiskTiles)[0] || lockTile;
    return {
      text: `Human-aware planner: ${humans.length} continuous people create ${humanRiskTiles.size} temporary risk tiles; hold or reroute ${activeRobot.id || "fleet"} before moving ${order}.`,
      robot: activeRobot.id || "FLEET",
      lock: compactTileLabel(firstRiskTile),
      skill: "human_aware_reroute",
    };
  }
  const readableText = deniedMoves.length
    ? `Hold ${activeRobot.id || "fleet"}: ${compactTileLabel(lockTile)} is occupied, replan before moving ${order}.`
    : `${baseText} Next: ${activeRobot.id || "fleet"} reserves ${compactTileLabel(lockTile)} for ${order}.`;
  return {
    text: readableText,
    robot: activeRobot.id || "FLEET",
    lock: compactTileLabel(lockTile),
    skill,
  };
}

function runtimeEventHomeTiles(events) {
  const homes = {};
  events.forEach((event) => {
    if (event.event_type !== "robot.moved") return;
    const robotId = event.payload?.robot_id;
    const source = normalizeTileId(event.payload?.source);
    if (robotId && source && !homes[robotId]) homes[robotId] = source;
  });
  return homes;
}

function resetRuntimeRobotForReplay(robot, homeTileId, index) {
  const fallback = `T_${String(index).padStart(2, "0")}_${String(Math.max(0, grid.rows - 1)).padStart(2, "0")}`;
  const tileId = normalizeTileId(homeTileId) || normalizeTileId(robot.tileId) || fallback;
  const center = tileCenterOrNull(tileId) || [0.5, 0.5];
  robot.route = [center];
  robot.routeTiles = [tileId];
  robot.routeClosed = false;
  robot.phase = 0;
  robot.carrying = false;
  robot.runtimeStatus = "ready";
  robot.status = "IDLE";
  robot.tileId = tileId;
  robot.nextTileId = null;
  robot.currentOrder = "-";
  robot.currentTarget = "-";
  robot.nextTarget = "-";
  robot.carriedSku = "-";
  robot.carriedWeight = "-";
  robot.carriedMaterial = "cardboard";
  robot.waitTicks = 0;
  robot.lockTiles = [tileId];
  robot.lockPressurePct = 24;
  robot.visualPose = staticRuntimePose(robot);
  robot.visualTileId = tileId;
  robot.motionDirection = 1;
  robot.motion = null;
  state.runtimeOccupiedTiles.set(tileId, robot.id);
}

function runtimeWarmStartTick(events) {
  const seenRobots = new Set();
  const targetRobotCount = state.load === "high" ? Math.min(9, state.robots.length) : Math.min(6, state.robots.length);
  let firstAssignedTick = null;
  for (const event of events) {
    const type = event.event_type || "";
    const robotId = event.payload?.robot_id;
    if (firstAssignedTick === null && type === "order.assigned") firstAssignedTick = Number(event.tick || 0);
    if (robotId && ["order.assigned", "robot.moved", "skill.started", "robot.lock_wait"].includes(type)) {
      seenRobots.add(robotId);
      if (seenRobots.size >= targetRobotCount) return Number(event.tick || 0);
    }
  }
  return firstAssignedTick ?? Number(events[0]?.tick || 0);
}

function initializeRuntimeReplay(events, logMessage) {
  if (!events.length) return;
  state.runtimeEvents = events;
  state.runtimeEventIndex = 0;
  state.runtimeReplayStartTick = runtimeWarmStartTick(events);
  state.runtimeReplayEndTick = Number(events[events.length - 1].tick || state.runtimeReplayStartTick);
  state.runtimeReplayTick = state.runtimeReplayStartTick;
  state.tick = state.runtimeReplayStartTick;
  state.simTime = state.runtimeReplayStartTick;
  state.runtimeOrderBook = new Map();
  state.runtimeActiveLocks = new Map();
  state.runtimeOccupiedTiles = new Map();
  state.log = [logMessage || `Runtime event replay loaded with ${events.length} events.`];

  const homes = runtimeEventHomeTiles(events);
  state.robots.forEach((robot, index) => resetRuntimeRobotForReplay(robot, homes[robot.id], index));
  applyRuntimeEventsThrough(state.runtimeReplayStartTick);
  syncRuntimeOrderRows();
}

function applyRuntimeEvents(eventsText) {
  const events = parseRuntimeEvents(eventsText);
  if (!events.length) {
    state.runtimeEvents = [];
    state.runtimeEventIndex = 0;
    state.runtimeReplayStartTick = 0;
    state.runtimeReplayEndTick = 0;
    state.runtimeReplayTick = 0;
    state.runtimeOrderBook = new Map();
    state.runtimeActiveLocks = new Map();
    return;
  }
  initializeRuntimeReplay(events, `Runtime event replay loaded: ${events.length} events.`);
}

function restartRuntimeEventReplay() {
  const events = state.runtimeEvents.slice();
  initializeRuntimeReplay(events, "Runtime event replay restarted from the first order.");
}

function motionDurationForRobot(robot, eventTick) {
  const nextMove = state.runtimeEvents.slice(state.runtimeEventIndex + 1).find((event) => (
    event.event_type === "robot.moved" && event.payload?.robot_id === robot.id
  ));
  const nextGap = nextMove ? Number(nextMove.tick || eventTick) - Number(eventTick || 0) : 2;
  const physicalCap = robot.carrying ? 3 : 2;
  return clamp(nextGap, 1, physicalCap);
}

function setRobotMotionFromEvent(robot, event) {
  const source = normalizeTileId(event.payload?.source);
  const destination = normalizeTileId(event.payload?.destination);
  if (!source || !destination) return;
  const segment = runtimeSegmentFromTiles(robot, source, destination, { visualOnly: true, allowOccupied: true });
  if (!segment) return;

  const eventTick = Number(event.tick || state.runtimeReplayTick || 0);
  segment.startTick = eventTick;
  segment.durationTicks = motionDurationForRobot(robot, eventTick);
  segment.progress = 0;
  robot.motion = segment;
  robot.tileId = source;
  robot.visualTileId = source;
  robot.nextTileId = destination;
  robot.route = [segment.source, segment.destination];
  robot.routeTiles = [source, destination];
  robot.runtimeStatus = "moving";
  robot.status = "MOVING";
  robot.waitTicks = 0;
  robot.lockTiles = [source, destination];
  robot.lockPressurePct = clamp((robot.lockPressurePct || 24) + 8, 18, 96);
  robot.nextTarget = compactTileLabel(destination);
  if (state.runtimeOccupiedTiles.get(source) === robot.id) state.runtimeOccupiedTiles.delete(source);
  state.runtimeOccupiedTiles.set(destination, robot.id);
  setRuntimeActiveLock(source, robot.id, "leaving", eventTick + segment.durationTicks);
  setRuntimeActiveLock(destination, robot.id, "reserved", eventTick + segment.durationTicks + 1);
}

function skillStatusFromMessage(message) {
  const value = String(message || "").toLowerCase();
  if (value.includes("unload")) return "UNLOADING";
  if (value.includes("handoff") || value.includes("exchange")) return "EXCHANGE";
  return "LOADING";
}

function runtimeOrderStatusFromRobotStatus(status) {
  if (status === "LOADING") return "picking";
  if (status === "UNLOADING") return "dropping";
  if (status === "EXCHANGE") return "handoff";
  return "assigned";
}

function applyRuntimeEvent(event) {
  const type = event.event_type || "";
  const payload = event.payload || {};
  const message = event.message || type;
  const robot = payload.robot_id ? findRuntimeRobot(payload.robot_id) : null;
  const tick = Number(event.tick || state.runtimeReplayTick || 0);

  if (["order.assigned", "skill.started", "skill.completed", "order.completed", "robot.lock_wait", "route.replanned", "planner.checked"].includes(type) || type.startsWith("human.")) {
    pushRuntimeLog(message);
  }

  if (type === "order.created") {
    const created = parseCreatedOrder(message, payload);
    upsertRuntimeOrder(created.orderId, {
      id: created.orderId,
      priority: runtimeOrderPriority(created.priorityLabel),
      difficulty: runtimeOrderDifficultyFromSku(created.sku),
      weight: runtimeOrderWeightFromSku(created.sku),
      robot: "-",
      status: "pending",
      sku: created.sku,
      createdTick: tick,
    });
  }

  if (type === "order.assigned") {
    const target = parseAssignedTarget(message);
    upsertRuntimeOrder(payload.order_id, {
      robot: payload.robot_id || "-",
      status: "assigned",
      target,
    });
    if (robot) {
      robot.currentOrder = payload.order_id || robot.currentOrder || "-";
      robot.currentTarget = compactTileLabel(target);
      robot.nextTarget = compactTileLabel(target);
      robot.runtimeStatus = "navigating_to_rack";
      robot.status = "MOVING";
      robot.lockPressurePct = clamp(robot.lockPressurePct || 28, 18, 96);
    }
  }

  if (type === "robot.moved" && robot) {
    setRobotMotionFromEvent(robot, event);
  }

  if (type === "robot.lock_wait" && robot) {
    const tileId = parseLockTile(message);
    robot.runtimeStatus = "waiting_for_tile_lock";
    robot.status = "WAITING";
    robot.waitTicks = (robot.waitTicks || 0) + 1;
    robot.lockTiles = tileId ? [tileId] : robot.lockTiles || [];
    robot.currentTarget = compactTileLabel(tileId || robot.nextTileId);
    robot.lockPressurePct = clamp(48 + robot.waitTicks * 8, 24, 98);
    setRuntimeActiveLock(tileId, robot.id, payload.reason || "wait", tick + 3);
  }

  if (type === "route.replanned" && robot) {
    robot.runtimeStatus = "route_replanned";
    robot.status = robot.motion ? "MOVING" : "WAITING";
    robot.lockPressurePct = clamp((robot.lockPressurePct || 42) + 12, 24, 98);
  }

  if (type === "skill.started" && robot) {
    const status = skillStatusFromMessage(message);
    robot.runtimeStatus = status === "LOADING" ? "picking" : status === "UNLOADING" ? "unloading" : "handoff";
    robot.status = status;
    robot.currentOrder = payload.order_id || robot.currentOrder || "-";
    robot.currentTarget = status === "UNLOADING" ? "PACK" : status === "EXCHANGE" ? "HANDOFF" : robot.currentTarget;
    if (status === "UNLOADING") robot.carrying = true;
    upsertRuntimeOrder(payload.order_id, {
      robot: robot.id,
      status: runtimeOrderStatusFromRobotStatus(status),
    });
  }

  if (type === "skill.completed" && robot) {
    const sku = parsePickedSku(message) || robot.carriedSku || "SKU_CARD_SMALL";
    robot.carrying = true;
    robot.carriedSku = sku;
    robot.carriedWeight = runtimeOrderWeightFromSku(sku);
    robot.carriedMaterial = materialFromSku(sku);
    robot.runtimeStatus = "navigating_to_conveyor";
    robot.status = "MOVING";
    robot.currentOrder = payload.order_id || robot.currentOrder || "-";
    robot.currentTarget = "PACK";
    upsertRuntimeOrder(payload.order_id, {
      robot: robot.id,
      sku,
      weight: runtimeOrderWeightFromSku(sku),
      difficulty: runtimeOrderDifficultyFromSku(sku),
      status: "navigating_to_conveyor",
    });
  }

  if (type === "order.completed") {
    upsertRuntimeOrder(payload.order_id, {
      robot: payload.robot_id || "-",
      status: "completed",
    });
    if (robot) {
      robot.runtimeStatus = "ready";
      robot.status = "IDLE";
      robot.carrying = false;
      robot.currentOrder = "-";
      robot.currentTarget = "DEPOT";
      robot.nextTarget = "-";
      robot.carriedSku = "-";
      robot.carriedWeight = "-";
      robot.lockTiles = robot.tileId ? [robot.tileId] : [];
      robot.lockPressurePct = 24;
    }
  }
}

function applyRuntimeEventsThrough(targetTick) {
  while (state.runtimeEventIndex < state.runtimeEvents.length) {
    const event = state.runtimeEvents[state.runtimeEventIndex];
    if (Number(event.tick || 0) > targetTick) break;
    applyRuntimeEvent(event);
    state.runtimeEventIndex += 1;
  }
  syncRuntimeOrderRows();
}

function applyRuntimeSnapshot(snapshot, metrics) {
  state.runtimeLinked = Boolean(snapshot);
  state.runtimeSnapshot = snapshot || null;
  state.runtimeMetrics = metrics || null;
  if (!snapshot) return;

  grid = {
    cols: Number(snapshot.warehouse?.width_tiles || grid.cols),
    rows: Number(snapshot.warehouse?.height_tiles || grid.rows),
  };
  state.tick = Number(snapshot.tick || 0);
  state.simTime = Number(snapshot.sim_time_s || 0);
  state.load = snapshot.load || state.load;
  state.planner = Boolean(snapshot.planner_enabled);
  state.runtimeBlockedTiles = blockedRuntimeTileSet(snapshot);
  state.runtimeOccupiedTiles = occupiedRuntimeTileMap(snapshot);
  state.humanScenario = normalizeHumanScenario(snapshot);
  state.shelves = (snapshot.shelves || []).map(normalizeRuntimeShelf);
  state.robots = (snapshot.robots || []).map(normalizeRuntimeRobot);
  state.orders = normalizeRuntimeOrders(snapshot.order_rows || []);
  state.ledTiles = ledTilesFromRuntime(snapshot);
  state.log = (snapshot.events || []).slice(-18);
  if (!state.log.length) state.log = ["Runtime snapshot linked."];
  state.selectedShelfId = state.shelves[0]?.id || null;
  resizeCanvas();
}

async function loadRuntimeProfile(load) {
  const suffix = state.humanIntrusionEnabled ? "_humans" : "";
  const primary = {
    label: `${load}${suffix}`,
    snapshotUrl: `../outputs/runtime_snapshot_${load}${suffix}.json`,
    metricsUrl: `../outputs/benchmark_metrics_${load}${suffix}.json`,
    eventsUrl: `../outputs/runtime_events_${load}${suffix}.jsonl`,
  };
  const fallback = {
    label: load,
    snapshotUrl: `../outputs/runtime_snapshot_${load}.json`,
    metricsUrl: `../outputs/benchmark_metrics_${load}.json`,
    eventsUrl: `../outputs/runtime_events_${load}.jsonl`,
  };

  let profile = primary;
  let [snapshot, metrics, eventsText] = await Promise.all([
    fetchJsonOrNull(primary.snapshotUrl),
    fetchJsonOrNull(primary.metricsUrl),
    fetchTextOrNull(primary.eventsUrl),
  ]);

  if (!snapshot && suffix) {
    profile = fallback;
    [snapshot, metrics, eventsText] = await Promise.all([
      fetchJsonOrNull(fallback.snapshotUrl),
      fetchJsonOrNull(fallback.metricsUrl),
      fetchTextOrNull(fallback.eventsUrl),
    ]);
  }

  if (snapshot) {
    applyRuntimeSnapshot(snapshot, metrics);
    applyRuntimeEvents(eventsText);
    if (els.runtimeSnapshotPort) els.runtimeSnapshotPort.textContent = `${profile.label}.json + events`;
    if (els.runtimeLinkBadge) els.runtimeLinkBadge.textContent = state.humanIntrusionEnabled && state.humanScenario ? "Human Runtime" : state.runtimeEvents.length ? "Runtime Events" : "Runtime JSON";
    const modeLabel = state.humanIntrusionEnabled && state.humanScenario ? "human-intrusion" : "standard";
    pushRuntimeLog(state.runtimeEvents.length
      ? `Loaded ${profile.label} ${modeLabel} runtime and event replay.`
      : `Loaded ${profile.label} ${modeLabel} runtime snapshot.`);
  } else {
    state.runtimeLinked = false;
    state.runtimeSnapshot = null;
    state.runtimeMetrics = null;
    state.runtimeEvents = [];
    state.runtimeEventIndex = 0;
    state.runtimeOrderBook = new Map();
    state.runtimeActiveLocks = new Map();
    state.runtimeBlockedTiles = new Set();
    state.runtimeOccupiedTiles = new Map();
    state.humanScenario = null;
    state.orders = cloneData(orderSeed);
    state.ledTiles = cloneData(ledTiles);
    if (els.runtimeSnapshotPort) els.runtimeSnapshotPort.textContent = "mock";
    if (els.runtimeLinkBadge) els.runtimeLinkBadge.textContent = "Mock Fallback";
  }
}


function manifestToSpriteMap(manifest) {
  return Object.fromEntries((manifest.sprites || []).map((sprite) => [
    sprite.name,
    {
      rect: sprite.rect,
      anchor: sprite.anchor,
      footprint: sprite.footprint || "",
    },
  ]));
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`Unable to load sprite sheet: ${src}`));
    image.src = src;
  });
}

async function loadSpriteAssets() {
  await Promise.all(Object.entries(SPRITE_CONFIG).map(async ([category, config]) => {
    const asset = spriteAssets[category];
    asset.sprites = SPRITE_FALLBACKS[category] || {};
    try {
      const [image, response] = await Promise.all([
        loadImage(config.sheet),
        fetch(config.manifest),
      ]);
      asset.image = image;
      if (response.ok) {
        const manifest = await response.json();
        asset.sprites = manifestToSpriteMap(manifest);
      }
    } catch {
      try {
        asset.image = await loadImage(config.sheet);
      } catch {
        asset.image = null;
      }
    }
    asset.ready = Boolean(asset.image && asset.image.complete && asset.image.naturalWidth > 0);
  }));
  state.log.push(`Sprite v${SPRITE_VERSION} sheets loaded into 03Canvas.`);
}

function applyModuleLabels() {
  MODULE_LABELS.forEach(([selector, label]) => {
    const host = document.querySelector(selector);
    if (!host || host.querySelector(":scope > .module-label")) return;
    host.classList.add("module-host");
    const tag = document.createElement("span");
    tag.className = "module-label";
    tag.textContent = label;
    host.prepend(tag);
  });
}

const loadProfiles = {
  low: { created: 185, completed: 174, queue: 23, congestion: 7, utilization: 49, fulfill: 11.8 },
  medium: { created: 342, completed: 289, queue: 53, congestion: 27, utilization: 74, fulfill: 18.6 },
  high: { created: 517, completed: 421, queue: 96, congestion: 58, utilization: 91, fulfill: 26.4 },
};

const skillJson = {
  shelf_pick: "../outputs/shelf_pick_trajectory.json",
  handoff: "../outputs/handoff_trajectory.json",
  arm_showcase: "../outputs/arm_showcase_trajectory.json",
};

const skillFocusMeta = {
  shelf_pick: {
    label: "Shelf Pick",
    status: "MuJoCo Verified",
    log: "Focused shelf_pick edge with gripper and basket contact evidence.",
  },
  handoff: {
    label: "Robot Handoff",
    status: "MuJoCo Verified",
    log: "Focused handoff edge between sender and receiver robots.",
  },
  arm_showcase: {
    label: "Arm + Basket",
    status: "Asset Verified",
    log: "Focused AEGIS basket and procedural gripper showcase.",
  },
  route_plan: {
    label: "Route Plan",
    status: "Runtime Sim",
    log: "Focused grid route planning edge for congestion-aware scheduling.",
  },
};

const MODULE_LABELS = [
  [".brand-block", "01Title"],
  [".left-rail", "02BenchmarkRail"],
  [".canvas-wrap", "03Canvas"],
  [".log-panel", "04Timeline"],
  [".legend-panel", "05Legend"],
  [".robot-module-panel", "06RobotModules"],
  [".order-intake-panel", "07OrderIntake"],
  [".package-panel", "08SKUClasses"],
  [".sim-control-panel", "09RuntimeControl"],
  [".asset-console", "10Console"],
  [".thin-rail", "11ProgramRail"],
];

const SPRITE_CONFIG = {
  floor: {
    sheet: `./sprites/floor/floor_sprite_sheet_v${SPRITE_VERSION}.png`,
    manifest: `./sprites/floor/floor_manifest_v${SPRITE_VERSION}.json`,
  },
  LED: {
    sheet: `./sprites/LED/LED_sprite_sheet_v${SPRITE_VERSION}.png`,
    manifest: `./sprites/LED/LED_manifest_v${SPRITE_VERSION}.json`,
  },
  rack: {
    sheet: `./sprites/rack/rack_sprite_sheet_v${SPRITE_VERSION}.png`,
    manifest: `./sprites/rack/rack_manifest_v${SPRITE_VERSION}.json`,
  },
  robot_dog: {
    sheet: `./sprites/robot_dog/robot_dog_sprite_sheet_v${SPRITE_VERSION}.png`,
    manifest: `./sprites/robot_dog/robot_dog_manifest_v${SPRITE_VERSION}.json`,
  },
  visual: {
    sheet: `./sprites/visual/visual_sprite_sheet_v${SPRITE_VERSION}.png`,
    manifest: `./sprites/visual/visual_manifest_v${SPRITE_VERSION}.json`,
  },
};

const spriteAssets = Object.fromEntries(Object.keys(SPRITE_CONFIG).map((category) => [
  category,
  { image: null, sprites: {}, ready: false },
]));

function rectSprite(x, y, w, h, ax, ay, footprint = "") {
  return {
    rect: { x, y, w, h },
    anchor: { x: ax, y: ay },
    footprint,
  };
}

function buildFallbackSprites() {
  const fallback = { floor: {}, LED: {}, rack: {}, robot_dog: {}, visual: {} };

  Array.from({ length: 8 }, (_, index) => {
    fallback.floor[`floor_concrete_${String(index + 1).padStart(2, "0")}`] =
      rectSprite(8 + index * 136, 8, 128, 128, 64, 92, "1x1 tile");
  });

  [
    "led_edge_pick_orange",
    "led_edge_delivery_green",
    "led_edge_robot_route_cyan",
    "led_edge_congestion_red",
  ].forEach((name, index) => {
    fallback.LED[name] = rectSprite(8 + index * 136, 8, 128, 128, 64, 92, "1x1 tile edge overlay");
  });

  [
    "robot_dog_base_n", "robot_dog_base_ne", "robot_dog_base_e", "robot_dog_base_se",
    "robot_dog_base_s", "robot_dog_base_sw", "robot_dog_base_w", "robot_dog_base_nw",
    "robot_dog_carry_cardboard_n", "robot_dog_carry_cardboard_ne", "robot_dog_carry_cardboard_e", "robot_dog_carry_cardboard_se",
    "robot_dog_carry_cardboard_s", "robot_dog_carry_cardboard_sw", "robot_dog_carry_cardboard_w", "robot_dog_carry_cardboard_nw",
    "robot_dog_carry_wood_n", "robot_dog_carry_wood_ne", "robot_dog_carry_wood_e", "robot_dog_carry_wood_se",
    "robot_dog_carry_wood_s", "robot_dog_carry_wood_sw", "robot_dog_carry_wood_w", "robot_dog_carry_wood_nw",
    "robot_dog_carry_metal_n", "robot_dog_carry_metal_ne", "robot_dog_carry_metal_e", "robot_dog_carry_metal_se",
    "robot_dog_carry_metal_s", "robot_dog_carry_metal_sw", "robot_dog_carry_metal_w", "robot_dog_carry_metal_nw",
  ].forEach((name, index) => {
    const col = index % 15;
    const row = Math.floor(index / 15);
    fallback.robot_dog[name] = rectSprite(8 + col * 136, 8 + row * 136, 128, 128, 64, 104, "robot dog");
  });

  [
    ["pallet_rack_1x2_ne_cardboard_full", 8, 8, 384, 384, 192, 308],
    ["pallet_rack_1x2_ne_metal_full", 1184, 400, 384, 384, 192, 308],
    ["pallet_rack_1x2_ne_wood_empty", 792, 400, 384, 384, 192, 308],
    ["pallet_rack_1x3_ne_metal_half", 1048, 5096, 512, 512, 256, 384],
    ["pallet_rack_1x3_ne_cardboard_full", 1184, 3536, 512, 512, 256, 384],
    ["pallet_rack_1x3_ne_cardboard_almost_none", 528, 4056, 512, 512, 256, 384],
    ["pallet_rack_1x3_ne_wood_full", 8, 4576, 512, 512, 256, 384],
    ["pallet_rack_1x3_ne_wood_half", 528, 4576, 512, 512, 256, 384],
  ].forEach(([name, x, y, w, h, ax, ay]) => {
    fallback.rack[name] = rectSprite(x, y, w, h, ax, ay, name.includes("1x3") ? "1x3 tiles" : "1x2 tiles");
  });

  fallback.visual.depot_zone_2x2 = rectSprite(8, 8, 288, 288, 144, 196, "2x2 tiles");
  [
    ["computer_terminal_1x1_e", [[304, 8], [568, 8], [832, 8], [1096, 8]]],
    ["computer_terminal_1x1_s", [[1360, 8], [1624, 8], [8, 304], [272, 304]]],
    ["computer_terminal_1x1_w", [[536, 304], [800, 304], [1064, 304], [1328, 304]]],
    ["computer_terminal_1x1_n", [[1592, 304], [8, 568], [272, 568], [536, 568]]],
  ].forEach(([prefix, positions]) => {
    positions.forEach(([x, y], frame) => {
      fallback.visual[`${prefix}_frame_${String(frame).padStart(2, "0")}`] =
        rectSprite(x, y, 256, 256, 128, 200, "1x1 tile");
    });
  });
  [
    ["exit_gate_conveyor_3x1_e", [[800, 568], [1320, 568], [8, 1088], [528, 1088]]],
    ["exit_gate_conveyor_3x1_s", [[1048, 1088], [8, 1608], [528, 1608], [1048, 1608]]],
    ["exit_gate_conveyor_3x1_w", [[8, 2128], [528, 2128], [1048, 2128], [8, 2648]]],
    ["exit_gate_conveyor_3x1_n", [[528, 2648], [1048, 2648], [8, 3168], [528, 3168]]],
  ].forEach(([prefix, positions]) => {
    positions.forEach(([x, y], frame) => {
      fallback.visual[`${prefix}_frame_${String(frame).padStart(2, "0")}`] =
        rectSprite(x, y, 512, 512, 256, 356, "3x1 tiles");
    });
  });
  [
    ["warehouse_wall_segment_ne_h3m", 1048, 3168, 352, 352, 176, 300],
    ["warehouse_wall_segment_ne_h6m", 1408, 3168, 528, 528, 264, 476],
    ["warehouse_wall_segment_nw_h3m", 8, 3704, 352, 352, 176, 300],
    ["warehouse_wall_segment_nw_h6m", 368, 3704, 528, 528, 264, 476],
    ["warehouse_wall_corner_back_h3m", 904, 3704, 384, 384, 192, 328],
  ].forEach(([name, x, y, w, h, ax, ay]) => {
    fallback.visual[name] = rectSprite(x, y, w, h, ax, ay, "rear wall");
  });
  return fallback;
}

const SPRITE_FALLBACKS = buildFallbackSprites();

function resizeCanvas() {
  const rect = {
    width: canvas.clientWidth,
    height: canvas.clientHeight,
  };
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  canvasCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  canvasCtx.imageSmoothingEnabled = false;

  pixelCanvas.width = Math.max(1, Math.floor(rect.width * GAME_PIXEL_RATIO));
  pixelCanvas.height = Math.max(1, Math.floor(rect.height * GAME_PIXEL_RATIO));
  pixelCtx.setTransform(1, 0, 0, 1, 0, 0);
  pixelCtx.imageSmoothingEnabled = false;
  ctx = pixelCtx;

  view.width = pixelCanvas.width;
  view.height = pixelCanvas.height;

  const tileFromWidth = ((view.width - 28) * 2) / (grid.cols + grid.rows + 3.2);
  const tileFromHeight = ((view.height - 54) * 4) / (grid.cols + grid.rows + 3.6);
  view.tileW = clamp(Math.min(tileFromWidth, tileFromHeight), 84, 172);
  view.tileH = view.tileW * 0.5;
  view.originX = view.width * 0.5;
  view.originY = Math.max(22, view.height * 0.062);
}

function scaleDesignSurface() {
  const scale = Math.min(
    window.innerWidth / DESIGN_SURFACE.width,
    window.innerHeight / DESIGN_SURFACE.height,
    1,
  );
  document.documentElement.style.setProperty("--ui-scale", String(scale));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function project(x, y, z = 0) {
  return {
    x: view.originX + (x - y) * view.tileW * 0.5,
    y: view.originY + (x + y) * view.tileH * 0.5 - z * view.tileH,
  };
}

function snap(value) {
  return Math.round(value);
}

function snapPoint(point) {
  return { x: snap(point.x), y: snap(point.y) };
}

function screenToGrid(sx, sy) {
  const dx = (sx - view.originX) / (view.tileW * 0.5);
  const dy = (sy - view.originY) / (view.tileH * 0.5);
  return { x: (dy + dx) * 0.5, y: (dy - dx) * 0.5 };
}

function spriteScale() {
  return view.tileW / 128;
}

function tileAnchor(x, y) {
  const s = spriteScale();
  const bottom = project(x + 1, y + 1, 0);
  return { x: bottom.x, y: bottom.y + 16 * s };
}

function worldAnchor(x, y, z = 0) {
  const s = spriteScale();
  const point = project(x, y, z);
  return { x: point.x, y: point.y + 16 * s };
}

function getSprite(category, name) {
  const asset = spriteAssets[category];
  if (!asset) return null;
  const sprite = asset.sprites[name];
  if (!sprite || !asset.image) return null;
  return { image: asset.image, ...sprite };
}

function drawSprite(category, name, anchor, options = {}) {
  const sprite = getSprite(category, name);
  if (!sprite) return false;
  const scale = options.scale ?? spriteScale();
  const alpha = options.alpha ?? 1;
  const { rect, anchor: spriteAnchor } = sprite;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.drawImage(
    sprite.image,
    rect.x,
    rect.y,
    rect.w,
    rect.h,
    snap(anchor.x - spriteAnchor.x * scale),
    snap(anchor.y - spriteAnchor.y * scale),
    snap(rect.w * scale),
    snap(rect.h * scale),
  );
  ctx.restore();
  return true;
}

function drawSpriteLabel(text, anchor, color = "#38cae8") {
  const s = spriteScale();
  ctx.save();
  ctx.font = `700 ${Math.max(7, Math.round(7 * s))}px Monaco, "Courier New", monospace`;
  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(0,0,0,0.82)";
  ctx.fillText(text, snap(anchor.x + 1), snap(anchor.y + 1));
  ctx.fillStyle = color;
  ctx.fillText(text, snap(anchor.x), snap(anchor.y));
  ctx.restore();
}

function directionFromDelta(dx, dy) {
  const sx = Math.abs(dx) < 0.18 ? 0 : Math.sign(dx);
  const sy = Math.abs(dy) < 0.18 ? 0 : Math.sign(dy);
  if (sx === 0 && sy < 0) return "n";
  if (sx > 0 && sy < 0) return "ne";
  if (sx > 0 && sy === 0) return "e";
  if (sx > 0 && sy > 0) return "se";
  if (sx === 0 && sy > 0) return "s";
  if (sx < 0 && sy > 0) return "sw";
  if (sx < 0 && sy === 0) return "w";
  if (sx < 0 && sy < 0) return "nw";
  return "s";
}

function cargoForRobot(robot, status, index) {
  if (robot.carriedMaterial && (robot.carrying || ["MOVING", "LOADING", "UNLOADING"].includes(status))) return robot.carriedMaterial;
  if (!["MOVING", "LOADING", "UNLOADING"].includes(status)) return null;
  const task = robotTaskSeed[index % robotTaskSeed.length];
  if (task.sku === "WOOD") return "wood";
  if (task.sku === "METAL") return "metal";
  if (task.sku === "CARD") return "cardboard";
  return robot.carrying ? "cardboard" : null;
}

function rackSpriteName(rack) {
  return `pallet_rack_1x${rack.length}_${rack.direction}_${rack.material}_${rack.fill}`;
}

function animationFrame() {
  return Math.floor(state.simTime / 18) % 4;
}

function poly(points, fill, stroke, lineWidth = 1) {
  const snapped = points.map(snapPoint);
  ctx.beginPath();
  snapped.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.closePath();
  if (fill) {
    ctx.fillStyle = fill;
    ctx.fill();
  }
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
  }
}

function pixelPoly(points, fill, stroke = "rgba(0,0,0,0.82)", lineWidth = 1) {
  const outlineWidth = Math.max(1, lineWidth + 1);
  poly(points, fill, "rgba(0,0,0,0.86)", outlineWidth);
  if (stroke) poly(points, null, stroke, lineWidth);
}

function segment(a, b, color, width = 1) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(snap(a.x), snap(a.y));
  ctx.lineTo(snap(b.x), snap(b.y));
  ctx.stroke();
  ctx.restore();
}

function drawTile(x, y, options = {}) {
  const p0 = project(x, y);
  const p1 = project(x + 1, y);
  const p2 = project(x + 1, y + 1);
  const p3 = project(x, y + 1);
  const fill = options.fill || ((x + y) % 2 ? PIXEL_PALETTE.floorA : PIXEL_PALETTE.floorB);
  pixelPoly([p0, p1, p2, p3], fill, options.stroke || PIXEL_PALETTE.floorEdge, Math.max(1, view.tileW / 118));

  const s = view.tileW / 76;
  if (!options.fill) {
    const detailSeed = (x * 37 + y * 19) % 7;
    const chipA = project(x + 0.18 + (detailSeed % 3) * 0.08, y + 0.18 + (detailSeed % 2) * 0.08, 0.012);
    const chipB = project(x + 0.62, y + 0.38 + (detailSeed % 3) * 0.07, 0.012);
    ctx.save();
    ctx.globalAlpha = 0.36;
    ctx.strokeStyle = detailSeed % 2 ? "rgba(242,138,29,0.18)" : "rgba(142,187,206,0.18)";
    ctx.lineWidth = Math.max(1, 1.1 * s);
    ctx.beginPath();
    ctx.moveTo(snap(chipA.x), snap(chipA.y));
    ctx.lineTo(snap(chipA.x + 10 * s), snap(chipA.y + 4 * s));
    ctx.lineTo(snap(chipA.x + 20 * s), snap(chipA.y));
    ctx.stroke();
    ctx.fillStyle = "rgba(5,16,22,0.42)";
    ctx.fillRect(Math.round(chipB.x), Math.round(chipB.y), Math.max(2, Math.round(3 * s)), Math.max(2, Math.round(3 * s)));
    ctx.restore();
  }

  if (options.dash) {
    ctx.save();
    ctx.setLineDash([9 * s, 7 * s]);
    poly([p0, p1, p2, p3], null, "rgba(0,0,0,0.85)", Math.max(3, 3 * s));
    poly([p0, p1, p2, p3], null, options.dash, Math.max(2, 1.8 * s));
    ctx.restore();
  }
}

function drawIsoBox(x, y, w, d, h, colors, stroke = "rgba(255,255,255,0.14)") {
  return drawIsoBoxAt(x, y, w, d, 0, h, colors, stroke);
}

function drawIsoBoxAt(x, y, w, d, z, h, colors, stroke = "rgba(255,255,255,0.14)") {
  const b1 = project(x + w, y, z);
  const b2 = project(x + w, y + d, z);
  const b3 = project(x, y + d, z);
  const t0 = project(x, y, z + h);
  const t1 = project(x + w, y, z + h);
  const t2 = project(x + w, y + d, z + h);
  const t3 = project(x, y + d, z + h);
  const bb0 = project(x, y, z);

  const s = view.tileW / 76;
  const sideWidth = Math.max(1, 1.1 * s);
  const topWidth = Math.max(1.5, 1.6 * s);
  pixelPoly([b1, b2, t2, t1], colors.right, stroke, sideWidth);
  pixelPoly([b2, b3, t3, t2], colors.left, stroke, sideWidth);
  pixelPoly([t0, t1, t2, t3], colors.top, stroke, topWidth);
  segment(t0, t1, "rgba(255,255,255,0.22)", Math.max(1, 1.1 * s));
  segment(t0, t3, "rgba(255,255,255,0.12)", Math.max(1, 1 * s));
  return { base: [bb0, b1, b2, b3], top: [t0, t1, t2, t3], center: project(x + w / 2, y + d / 2, z + h) };
}

function floorVariant(x, y) {
  const block = (Math.floor(x / 2) + Math.floor(y / 2) * 2) % 4;
  const checker = (x + y) % 2;
  return ((block + checker) % 4) + 1;
}

function drawFloorUnifier(x, y, variant) {
  const p0 = project(x, y, 0.012);
  const p1 = project(x + 1, y, 0.012);
  const p2 = project(x + 1, y + 1, 0.012);
  const p3 = project(x, y + 1, 0.012);
  const fill = variant % 2 ? "rgba(28, 58, 68, 0.16)" : "rgba(13, 31, 40, 0.11)";
  poly([p0, p1, p2, p3], fill, "rgba(132, 176, 190, 0.08)", Math.max(1, view.tileW / 170));
}

function drawZoneMicroLabel(text, tileX, tileY, color) {
  const point = project(tileX + 0.5, tileY + 0.5, 0.08);
  drawSpriteLabel(text, { x: point.x, y: point.y }, color);
}

function drawIsoFootprint(x, y, w, d, options = {}) {
  const expand = options.expand ?? 0.08;
  const z = options.z ?? 0.018;
  const points = [
    project(x - expand, y - expand, z),
    project(x + w + expand, y - expand, z),
    project(x + w + expand, y + d + expand, z),
    project(x - expand, y + d + expand, z),
  ];
  ctx.save();
  ctx.globalAlpha = options.alpha ?? 0.32;
  poly(points, options.fill || "rgba(0, 0, 0, 0.54)", null);
  ctx.restore();
}

function drawFloorPaintSegment(a, b, color = "rgba(238, 164, 35, 0.74)") {
  const s = spriteScale();
  const start = project(a[0] + 0.5, a[1] + 0.5, 0.045);
  const end = project(b[0] + 0.5, b[1] + 0.5, 0.045);
  ctx.save();
  ctx.lineCap = "square";
  ctx.lineJoin = "miter";
  ctx.setLineDash([10 * s, 8 * s]);
  ctx.strokeStyle = "rgba(0, 0, 0, 0.72)";
  ctx.lineWidth = Math.max(2, 3 * s);
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, 1.4 * s);
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();
  ctx.restore();
}

function drawFloorPaint() {
  [
    [[2, 0], [2, 11]],
    [[5, 0], [5, 11]],
    [[8, 0], [8, 11]],
    [[11, 0], [11, 11]],
    [[14, 1], [14, 10]],
    [[0, 4], [15, 4]],
    [[0, 5], [15, 5]],
    [[0, 9], [15, 9]],
  ].forEach(([a, b], index) => {
    drawFloorPaintSegment(a, b, index % 3 === 0 ? "rgba(245, 181, 49, 0.72)" : "rgba(212, 127, 26, 0.58)");
  });

  const s = spriteScale();
  [
    [13, 4, 1],
    [10, 9, 1],
    [2, 5, -1],
  ].forEach(([x, y, dir]) => {
    const p = project(x + 0.5, y + 0.5, 0.05);
    ctx.save();
    ctx.translate(snap(p.x), snap(p.y));
    ctx.rotate(dir > 0 ? -Math.PI / 4 : Math.PI * 0.75);
    ctx.fillStyle = "rgba(0,0,0,0.65)";
    ctx.fillRect(snap(-5 * s), snap(-9 * s), snap(16 * s), snap(5 * s));
    ctx.fillStyle = "rgba(245,181,49,0.76)";
    ctx.beginPath();
    ctx.moveTo(10 * s, 0);
    ctx.lineTo(-4 * s, -8 * s);
    ctx.lineTo(-4 * s, 8 * s);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  });
}

function drawBackground() {
  const gradient = ctx.createLinearGradient(0, 0, 0, view.height);
  gradient.addColorStop(0, PIXEL_PALETTE.voidTop);
  gradient.addColorStop(1, PIXEL_PALETTE.voidBottom);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, view.width, view.height);

  const base = [
    project(-2.35, -2.25, -0.03),
    project(grid.cols + 2.35, -2.25, -0.03),
    project(grid.cols + 2.35, grid.rows + 2.25, -0.03),
    project(-2.35, grid.rows + 2.25, -0.03),
  ];
  pixelPoly(base, "#122533", "rgba(24,224,230,0.12)", Math.max(1, view.tileW / 96));

  for (let y = 0; y < grid.rows; y += 1) {
    for (let x = 0; x < grid.cols; x += 1) {
      const variant = floorVariant(x, y);
      drawSprite("floor", `floor_concrete_${String(variant).padStart(2, "0")}`, tileAnchor(x, y), { alpha: 0.94 });
      drawFloorUnifier(x, y, variant);
    }
  }

  drawFloorPaint();

  const activeLedTiles = state.ledTiles || ledTiles;
  const restTiles = activeLedTiles.rest || [];
  const deliveryTiles = activeLedTiles.delivery || [];
  const lockTiles = state.runtimeEvents.length
    ? currentRuntimeLockTilePoints()
    : [...(activeLedTiles.route || []), ...(activeLedTiles.congestion || [])];

  restTiles.forEach(([x, y]) => drawSprite("LED", "led_edge_robot_route_cyan", tileAnchor(x, y), { alpha: 0.72 }));
  deliveryTiles.forEach(([x, y]) => drawSprite("LED", "led_edge_delivery_green", tileAnchor(x, y), { alpha: 0.82 }));
  lockTiles.forEach(([x, y], index) => {
    const pulse = 0.56 + Math.sin(state.simTime * 0.08 + index) * 0.16;
    drawSprite("LED", "led_edge_congestion_red", tileAnchor(x, y), { alpha: clamp(pulse, 0.38, 0.82) });
  });

  drawZoneMicroLabel("DEPOT", 1, Math.max(0, grid.rows - 2), "#38cae8");
  deliveryTiles.forEach(([x, y], index) => {
    if (index < 4) drawZoneMicroLabel("DROP", x, y, "#5cdd61");
  });
}

function drawFacilityProps() {
  const s = view.tileW / 76;

  drawIsoBox(0.25, 5.9, 0.48, 0.56, 0.58, {
    top: "#6e91a4",
    left: "#243849",
    right: "#35566d",
  }, PIXEL_PALETTE.outline);
  const terminalScreen = project(0.44, 5.94, 0.58);
  ctx.save();
  ctx.fillStyle = "rgba(24,224,230,0.34)";
  ctx.strokeStyle = PIXEL_PALETTE.cyan;
  ctx.lineWidth = Math.max(1, 1.2 * s);
  ctx.fillRect(snap(terminalScreen.x - 16 * s), snap(terminalScreen.y - 11 * s), snap(32 * s), snap(20 * s));
  ctx.strokeRect(snap(terminalScreen.x - 16 * s), snap(terminalScreen.y - 11 * s), snap(32 * s), snap(20 * s));
  ctx.fillStyle = "#62ff6d";
  ctx.fillRect(snap(terminalScreen.x - 10 * s), snap(terminalScreen.y - 4 * s), snap(5 * s), snap(5 * s));
  ctx.fillRect(snap(terminalScreen.x - 1 * s), snap(terminalScreen.y - 4 * s), snap(14 * s), snap(5 * s));
  ctx.restore();
  drawWorldLabel("ORDER IN", terminalScreen.x, terminalScreen.y - 10 * s, PIXEL_PALETTE.cyan);

  const doorBase = { x: 10.35, y: 6.1, w: 0.5, d: 1.35, h: 1.25 };
  const door = drawIsoBox(doorBase.x, doorBase.y, doorBase.w, doorBase.d, doorBase.h, {
    top: "#96a9ad",
    left: "#263844",
    right: "#4e6472",
  }, PIXEL_PALETTE.outline);
  const a = project(doorBase.x + 0.02, doorBase.y + 0.08, doorBase.h * 0.9);
  const b = project(doorBase.x + 0.02, doorBase.y + doorBase.d - 0.08, doorBase.h * 0.9);
  ctx.save();
  ctx.strokeStyle = PIXEL_PALETTE.orange;
  ctx.lineWidth = Math.max(1, 1.3 * s);
  for (let i = 0; i < 7; i += 1) {
    const offset = i * 0.13;
    const p0 = project(doorBase.x + 0.04, doorBase.y + 0.12 + offset, doorBase.h * 0.55);
    const p1 = project(doorBase.x + 0.04, doorBase.y + 0.24 + offset, doorBase.h * 0.55);
    segment(p0, p1, "rgba(242,138,29,0.58)", Math.max(1, 1.2 * s));
  }
  ctx.restore();
  drawWorldLabel("EXIT", door.center.x + 18 * s, door.center.y - 12 * s, PIXEL_PALETTE.orange);
}

function drawFloorLighting() {
  const s = view.tileW / 76;
  ctx.save();
  ctx.globalAlpha = 0.2;
  ctx.strokeStyle = "#ffbf3d";
  ctx.lineWidth = Math.max(1, 1.2 * s);
  for (let x = 1; x < grid.cols; x += 2) {
    const a = project(x, 0.15, 0.025);
    const b = project(x + 0.8, 0.15, 0.025);
    segment(a, b, ctx.strokeStyle, ctx.lineWidth);
  }
  for (let y = 2; y < grid.rows; y += 3) {
    const a = project(grid.cols - 0.25, y, 0.025);
    const b = project(grid.cols - 0.25, y + 0.65, 0.025);
    segment(a, b, ctx.strokeStyle, ctx.lineWidth);
  }
  ctx.restore();
}

function drawWarehouseWalls() {
  const wallColors = { top: "#8da4ad", left: "#34495a", right: "#5d7482" };
  for (let x = 0; x < grid.cols; x += 1) {
    drawIsoBox(x, -0.28, 0.95, 0.24, 0.58 + (x % 3 === 0 ? 0.12 : 0), wallColors, PIXEL_PALETTE.outline);
    if (x % 3 === 1) {
      drawIsoBox(x + 0.17, -0.34, 0.42, 0.08, 0.08, {
        top: "#4fb7ff",
        left: "#153b56",
        right: "#256b9b",
      }, PIXEL_PALETTE.outline);
    }
  }
  for (let y = 0; y < grid.rows; y += 1) {
    drawIsoBox(grid.cols + 0.05, y, 0.24, 0.95, 0.58 + (y % 3 === 0 ? 0.12 : 0), wallColors, PIXEL_PALETTE.outline);
    if (y % 3 === 1) {
      drawIsoBox(grid.cols + 0.18, y + 0.18, 0.08, 0.42, 0.08, {
        top: "#4fb7ff",
        left: "#153b56",
        right: "#256b9b",
      }, PIXEL_PALETTE.outline);
    }
  }
}

function drawLaneArrows() {
  const lanes = [
    [[1.0, 6.6], [3.2, 5.2], [6.8, 5.6], [9.2, 6.6]],
    [[1.1, 1.1], [3.4, 2.1], [6.2, 2.4], [9.4, 3.4]],
    [[4.2, 7.4], [4.8, 5.4], [5.1, 3.0], [6.3, 1.2]],
  ];

  ctx.save();
  const s = view.tileW / 76;
  ctx.lineWidth = Math.max(3, 3 * s);
  ctx.setLineDash([10 * s, 8 * s]);
  lanes.forEach((lane, index) => {
    ctx.strokeStyle = index === 0 ? "rgba(255,191,61,0.72)" : "rgba(50,201,244,0.42)";
    ctx.beginPath();
    lane.forEach(([x, y], pointIndex) => {
      const p = project(x, y, 0.03);
      if (pointIndex === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
    const tail = lane[lane.length - 2];
    const head = lane[lane.length - 1];
    const pTail = project(tail[0], tail[1], 0.04);
    const pHead = project(head[0], head[1], 0.04);
    const angle = Math.atan2(pHead.y - pTail.y, pHead.x - pTail.x);
    ctx.beginPath();
    ctx.moveTo(pHead.x, pHead.y);
    ctx.lineTo(pHead.x - Math.cos(angle - 0.55) * 22 * s, pHead.y - Math.sin(angle - 0.55) * 22 * s);
    ctx.lineTo(pHead.x - Math.cos(angle + 0.55) * 22 * s, pHead.y - Math.sin(angle + 0.55) * 22 * s);
    ctx.closePath();
    ctx.fillStyle = ctx.strokeStyle;
    ctx.fill();
    ctx.setLineDash([10 * s, 8 * s]);
  });
  ctx.restore();
}

function drawWorldLabel(text, x, y, color = "#38cae8") {
  const s = view.tileW / 76;
  ctx.save();
  ctx.font = `700 ${Math.round(12 * s)}px Monaco, "Courier New", monospace`;
  const metrics = ctx.measureText(text);
  const width = metrics.width + 16 * s;
  ctx.fillStyle = "rgba(4, 7, 10, 0.93)";
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, 1.2 * s);
  ctx.beginPath();
  const left = x - width / 2;
  const top = y - 31 * s;
  ctx.moveTo(left, top + 5 * s);
  ctx.lineTo(left + 5 * s, top);
  ctx.lineTo(left + width - 5 * s, top);
  ctx.lineTo(left + width, top + 5 * s);
  ctx.lineTo(left + width, top + 22 * s);
  ctx.lineTo(left, top + 22 * s);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.92)";
  ctx.lineWidth = Math.max(2, 2 * s);
  ctx.stroke();
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, 1.2 * s);
  ctx.stroke();
  ctx.fillStyle = "#eef4f8";
  ctx.textAlign = "center";
  ctx.fillStyle = "#05070a";
  ctx.fillText(text, x + 2 * s, y - 14 * s);
  ctx.fillStyle = "#eef4f8";
  ctx.fillText(text, x, y - 16 * s);
  ctx.restore();
}

function drawWallSprite(wall) {
  drawSprite(wall.category, wall.sprite, worldAnchor(wall.x, wall.y));
}

function drawFacilitySprite(prop) {
  const sprite = typeof prop.sprite === "function" ? prop.sprite() : prop.sprite;
  const anchor = worldAnchor(prop.x, prop.y);
  drawSprite(prop.category, sprite, anchor);
  if (prop.label) drawSpriteLabel(prop.label, { x: anchor.x, y: anchor.y - 54 * spriteScale() }, prop.color);
}

function drawFacilityShadow(prop) {
  if (prop.id === "SERVER") drawIsoFootprint(0.66, 1.68, 1.05, 1.05, { alpha: 0.22, expand: 0.12 });
  if (prop.shadow) drawIsoFootprint(prop.shadow.x, prop.shadow.y, prop.shadow.w, prop.shadow.d, { alpha: 0.32, expand: 0.1 });
  if (prop.doorLine) {
    const a = project(prop.doorLine.x1, prop.doorLine.y1, 0.08);
    const b = project(prop.doorLine.x2, prop.doorLine.y2, 0.08);
    segment(a, b, "rgba(247, 183, 51, 0.82)", Math.max(2, view.tileW / 34));
  }
}

function drawRackShadow(rack) {
  drawIsoFootprint(rack.x, rack.y, rack.w, rack.d, { alpha: 0.42, expand: 0.18, z: 0.014, fill: "rgba(0, 0, 0, 0.66)" });
}

function drawRackContactBase(rack) {
  const inset = 0.035;
  const width = Math.max(0.35, rack.w - inset * 2);
  const depth = Math.max(0.35, rack.d - inset * 2);
  drawIsoBoxAt(rack.x + inset, rack.y + inset, width, depth, 0.006, 0.09, {
    top: "rgba(38, 62, 70, 0.92)",
    left: "rgba(8, 17, 23, 0.96)",
    right: "rgba(15, 31, 39, 0.96)",
  }, "rgba(0, 0, 0, 0.78)");
}

function drawRackSprite(rack) {
  const selected = state.dragShelf?.id === rack.id || state.selectedShelfId === rack.id;
  const anchor = worldAnchor(rack.anchorX, rack.anchorY);
  const name = rackSpriteName(rack);
  drawRackContactBase(rack);
  drawSprite("rack", name, anchor);
  if (selected) {
    drawSpriteLabel(rack.id, { x: anchor.x, y: anchor.y - 118 * spriteScale() }, "#f7b733");
  }
}

function robotSpriteName(robot, status, direction, index) {
  const cargo = cargoForRobot(robot, status, index);
  if (cargo) return `robot_dog_carry_${cargo}_${direction}`;
  return `robot_dog_base_${direction}`;
}

function displayRobotStatus(status) {
  if (status === "LOADING") return "PICKING";
  if (status === "UNLOADING") return "DROPPING";
  if (status === "HANDOFF" || status === "EXCHANGE") return "EXCHANGING";
  return status;
}

function drawRobotSprite(robot, index) {
  const pos = robotDisplayPosition(robot);
  const status = robotStatus(robot);
  const anchor = worldAnchor(pos.x, pos.y);
  const name = robotSpriteName(robot, status, pos.direction, index);
  drawSprite("robot_dog", name, anchor);
  drawRobotTag(robot, status, anchor.x, anchor.y - 18 * spriteScale(), robot.color);
}

function drawRobotPreview(canvasElement, robot, index) {
  if (!canvasElement) return;
  const previewCtx = canvasElement.getContext("2d");
  const width = canvasElement.width;
  const height = canvasElement.height;
  previewCtx.clearRect(0, 0, width, height);
  previewCtx.imageSmoothingEnabled = false;

  const pos = robotDisplayPosition(robot);
  const status = robotStatus(robot);
  const spriteName = robotSpriteName(robot, status, pos.direction, index);
  const sprite = getSprite("robot_dog", spriteName);
  const pulse = (Math.sin(state.simTime * 0.035 + index) + 1) * 0.5;
  const scaleBase = Math.min(width / 112, height / 96);
  const baseY = height - 18;
  const shadowW = Math.round(width * 0.56);
  const shadowX = Math.round((width - shadowW) / 2);

  previewCtx.save();
  previewCtx.fillStyle = "rgba(0,0,0,0.6)";
  previewCtx.fillRect(shadowX, baseY - 6, shadowW, 5);
  previewCtx.strokeStyle = robot.color;
  previewCtx.globalAlpha = status === "IDLE" ? 0.28 : 0.55 + pulse * 0.25;
  previewCtx.lineWidth = 2;
  previewCtx.strokeRect(shadowX - 3, baseY - 14, shadowW + 6, 14);
  previewCtx.globalAlpha = 1;

  if (sprite) {
    const scale = (status === "IDLE" ? 0.47 : 0.5 + pulse * 0.015) * scaleBase;
    const bob = status === "MOVING" ? Math.round((pulse - 0.5) * 4 * scaleBase) : 0;
    const anchor = sprite.anchor || { x: sprite.rect.w / 2, y: sprite.rect.h * 0.82 };
    previewCtx.drawImage(
      sprite.image,
      sprite.rect.x,
      sprite.rect.y,
      sprite.rect.w,
      sprite.rect.h,
      Math.round(width / 2 - anchor.x * scale),
      Math.round(baseY - anchor.y * scale + bob),
      Math.round(sprite.rect.w * scale),
      Math.round(sprite.rect.h * scale),
    );
  } else {
    previewCtx.fillStyle = robot.color;
    previewCtx.fillRect(Math.round(width * 0.34), Math.round(height * 0.38), Math.round(width * 0.34), Math.round(height * 0.18));
    previewCtx.fillStyle = "#d2d8dd";
    previewCtx.fillRect(Math.round(width * 0.27), Math.round(height * 0.58), 14, 14);
    previewCtx.fillRect(Math.round(width * 0.64), Math.round(height * 0.58), 14, 14);
  }

  if (status === "LOADING" || status === "UNLOADING") {
    previewCtx.fillStyle = status === "LOADING" ? "#f7b733" : "#5cdd61";
    previewCtx.fillRect(Math.round(width * 0.72), Math.round(height * 0.17 + pulse * 4), 12, 12);
  }
  previewCtx.restore();
}

function drawRobotPreviewById(id, robot, index) {
  drawRobotPreview(document.getElementById(id), robot, index);
}

function drawRobotShadow(robot) {
  const pos = robotDisplayPosition(robot);
  drawIsoFootprint(pos.x - 0.28, pos.y - 0.2, 0.56, 0.4, { alpha: 0.26, expand: 0.05, z: 0.026 });
}

function shelfColors(tone, selected) {
  const map = {
    blue: ["#517b91", "#192b39", "#29495c"],
    cyan: ["#3c8f9d", "#17323c", "#245868"],
    amber: ["#d57922", "#45210e", "#7e3b13"],
    green: ["#5a8f55", "#1e3b24", "#326338"],
    violet: ["#6c5c98", "#28203c", "#483269"],
    orange: ["#cc6421", "#421b0e", "#783014"],
  };
  const [top, left, right] = map[tone] || map.blue;
  if (!selected) return { top, left, right };
  return {
    top: "#d09a35",
    left: "#5c3b16",
    right: "#78511d",
  };
}

function drawShelf(shelf) {
  const s = view.tileW / 76;
  const selected = state.dragShelf && state.dragShelf.id === shelf.id;
  const colors = shelfColors(shelf.tone, selected);
  const railColor = selected ? "#ffbf3d" : PIXEL_PALETTE.cyan;
  const frame = {
    top: selected ? "#ffbf3d" : PIXEL_PALETTE.orange,
    left: selected ? "#4b2d10" : "#0a1720",
    right: selected ? "#704418" : "#24485a",
  };
  const plank = {
    top: selected ? "#785224" : "#315164",
    left: "#101e28",
    right: selected ? "#513318" : "#1e3948",
  };

  const footprint = [
    project(shelf.x, shelf.y, 0.01),
    project(shelf.x + shelf.w, shelf.y, 0.01),
    project(shelf.x + shelf.w, shelf.y + shelf.d, 0.01),
    project(shelf.x, shelf.y + shelf.d, 0.01),
  ];
  pixelPoly(footprint, "rgba(4,10,14,0.4)", "rgba(24,224,230,0.14)", Math.max(1, s));

  drawIsoBoxAt(shelf.x - 0.04, shelf.y - 0.03, shelf.w + 0.08, shelf.d + 0.06, 0.03, 0.08, {
    top: "#243b4a",
    left: "#0b1218",
    right: "#172936",
  }, "rgba(24,224,230,0.16)");

  const boxTones = [
    { top: "#f1a139", left: "#7d3512", right: "#b95419" },
    { top: "#73b559", left: "#315126", right: "#4f8338" },
    { top: "#27d6ce", left: "#0b676b", right: "#159ca1" },
    { top: "#a9bcc3", left: "#4b6774", right: "#78929e" },
  ];

  const levels = [0.32, 0.64, 0.96, 1.28].filter((z) => z < shelf.h + 0.12);
  levels.forEach((z, levelIndex) => {
    drawIsoBoxAt(shelf.x + 0.03, shelf.y + 0.04, shelf.w - 0.06, shelf.d - 0.08, z - 0.08, 0.06, plank, "rgba(255,255,255,0.08)");
    segment(project(shelf.x + 0.08, shelf.y + shelf.d - 0.07, z + 0.01), project(shelf.x + shelf.w - 0.08, shelf.y + shelf.d - 0.07, z + 0.01), PIXEL_PALETTE.cyanDim, Math.max(1, 1.6 * s));

    for (let row = 0; row < 3; row += 1) {
      for (let col = 0; col < 3; col += 1) {
        if ((row * 2 + col + levelIndex) % 7 === 0) continue;
        const px = shelf.x + 0.1 + col * 0.29;
        const py = shelf.y + 0.16 + row * ((shelf.d - 0.58) / 2);
        const tone = boxTones[(row + col + levelIndex) % boxTones.length];
        drawIsoBoxAt(px, py, 0.23, 0.28, z - 0.21, 0.17, tone, "rgba(0,0,0,0.68)");
        const stripeA = project(px + 0.06, py + 0.04, z - 0.04);
        const stripeB = project(px + 0.18, py + 0.04, z - 0.04);
        segment(stripeA, stripeB, "rgba(255,255,255,0.28)", Math.max(1, 0.9 * s));
      }
    }

    drawIsoBoxAt(shelf.x - 0.01, shelf.y - 0.02, shelf.w + 0.02, 0.08, z, 0.06, frame, "rgba(0,0,0,0.85)");
    drawIsoBoxAt(shelf.x - 0.01, shelf.y + shelf.d - 0.07, shelf.w + 0.02, 0.08, z, 0.06, frame, "rgba(0,0,0,0.85)");
    drawIsoBoxAt(shelf.x - 0.02, shelf.y, 0.08, shelf.d, z, 0.06, frame, "rgba(0,0,0,0.85)");
    drawIsoBoxAt(shelf.x + shelf.w - 0.06, shelf.y, 0.08, shelf.d, z, 0.06, frame, "rgba(0,0,0,0.85)");
  });

  const postSize = 0.08;
  [
    [shelf.x - 0.02, shelf.y - 0.02],
    [shelf.x + shelf.w - postSize + 0.02, shelf.y - 0.02],
    [shelf.x + shelf.w - postSize + 0.02, shelf.y + shelf.d - postSize + 0.02],
    [shelf.x - 0.02, shelf.y + shelf.d - postSize + 0.02],
  ].forEach(([px, py]) => {
    drawIsoBoxAt(px, py, postSize, postSize, 0.06, shelf.h + 0.1, frame, "rgba(0,0,0,0.92)");
  });

  drawIsoBoxAt(shelf.x + 0.03, shelf.y + shelf.d - 0.12, shelf.w - 0.06, 0.1, shelf.h + 0.02, 0.06, {
    top: colors.top,
    left: colors.left,
    right: colors.right,
  }, "rgba(0,0,0,0.82)");

  const signPos = project(shelf.x + shelf.w + 0.04, shelf.y + 0.22, shelf.h * 0.72);
  drawWorldLabel(shelf.id, signPos.x, signPos.y, railColor);
}

function cardinalizeRoute(route) {
  const result = [];
  const pushPoint = (point) => {
    const previous = result[result.length - 1];
    if (!previous || previous[0] !== point[0] || previous[1] !== point[1]) result.push(point);
  };

  (route || []).forEach((point) => {
    const previous = result[result.length - 1];
    if (!previous) {
      pushPoint(point);
      return;
    }
    const dx = Math.abs(point[0] - previous[0]);
    const dy = Math.abs(point[1] - previous[1]);
    if (dx > 0.001 && dy > 0.001) pushPoint([point[0], previous[1]]);
    pushPoint(point);
  });
  return result;
}

function runtimeMoveForRobot(kind, robot) {
  const moves = state.runtimeSnapshot?.movement_locks?.[kind] || [];
  return moves.find((move) => move.robot_id === robot.id) || null;
}

function runtimeRobotCanMove(robot) {
  const runtimeStatus = String(robot.runtimeStatus || "").toLowerCase();
  if (["picking", "loading", "unloading", "unloading_at_conveyor", "waiting_for_tile_lock", "blocked", "ready", "idle"].includes(runtimeStatus)) return false;
  const hasRoutePlayback = (robot.routeTiles || routeTileIds(robot.route)).length > 1;
  return robotStatus(robot) === "MOVING" && hasRoutePlayback && (runtimeStatus.includes("navigating") || runtimeStatus.includes("relocating") || runtimeStatus === "moving");
}

function runtimeTileIsAvailable(tileId, robotId = "", options = {}) {
  const id = normalizeTileId(tileId);
  if (!id || !tileInBounds(id)) return false;
  if (state.runtimeBlockedTiles?.has(id)) return false;
  const allowOccupied = options === true || options.allowOccupied === true;
  const allowMovingOccupant = typeof options === "object" && options.allowMovingOccupant === true;
  if (allowOccupied) return true;
  const occupant = state.runtimeOccupiedTiles?.get(id);
  if (!occupant || occupant === robotId) return true;
  return allowMovingOccupant && runtimeOccupantMovesAway(id, occupant);
}

function runtimeSegmentFromTiles(robot, sourceTileId, destinationTileId, options = {}) {
  const source = normalizeTileId(sourceTileId);
  const destination = normalizeTileId(destinationTileId);
  if (!source || !destination || source === destination) return null;
  if (!tileIdsAreCardinalNeighbors(source, destination)) return null;
  if (!runtimeTileIsAvailable(source, robot.id, true)) return null;
  const visualOnly = typeof options === "object" && options.visualOnly === true;
  if (!visualOnly && !runtimeTileIsAvailable(destination, robot.id, {
    allowOccupied: Boolean(options.allowOccupied),
    allowMovingOccupant: Boolean(options.allowMovingOccupant),
  })) return null;
  const sourceCenter = tileCenterOrNull(source);
  const destinationCenter = tileCenterOrNull(destination);
  if (!sourceCenter || !destinationCenter) return null;
  return {
    sourceTileId: source,
    destinationTileId: destination,
    source: sourceCenter,
    destination: destinationCenter,
    progress: 0,
    done: false,
  };
}

function nextRuntimeRouteTile(robot, fromTileId) {
  const current = normalizeTileId(fromTileId);
  const routeTiles = robot.routeTiles || routeTileIds(robot.route);
  const index = routeTiles.indexOf(current);
  if (index >= 0 && index < routeTiles.length - 1) return routeTiles[index + 1];
  return null;
}

function runtimeRouteNeighbor(robot, fromTileId, direction) {
  const current = normalizeTileId(fromTileId);
  const routeTiles = robot.routeTiles || routeTileIds(robot.route);
  const index = routeTiles.indexOf(current);
  if (index < 0) return null;
  return routeTiles[index + direction] || null;
}

function runtimeOccupantMovesAway(tileId, occupantId) {
  const occupant = state.robots.find((robot) => robot.id === occupantId);
  if (!occupant || !runtimeRobotCanMove(occupant)) return false;

  const grantedMove = runtimeMoveForRobot("granted_moves", occupant);
  if (grantedMove) {
    const source = normalizeTileId(grantedMove.source_tile);
    const destination = normalizeTileId(grantedMove.destination_tile);
    return source === tileId && tileIdsAreCardinalNeighbors(source, destination) && runtimeTileIsAvailable(destination, occupant.id, true);
  }

  const nextTile = occupant.nextTileId || nextRuntimeRouteTile(occupant, occupant.tileId);
  return occupant.tileId === tileId && tileIdsAreCardinalNeighbors(tileId, nextTile) && runtimeTileIsAvailable(nextTile, occupant.id, true);
}

function initialRuntimeSegment(robot) {
  const deniedMove = runtimeMoveForRobot("denied_moves", robot);
  if (deniedMove) return null;

  const grantedMove = runtimeMoveForRobot("granted_moves", robot);
  if (grantedMove) {
    const grantedSegment = runtimeSegmentFromTiles(robot, grantedMove.source_tile, grantedMove.destination_tile, { allowOccupied: true });
    if (grantedSegment) return grantedSegment;
  }

  const source = robot.tileId || robot.visualTileId || robot.routeTiles?.[0];
  if (robot.nextTileId) {
    const nextSegment = runtimeSegmentFromTiles(robot, source, robot.nextTileId, { allowMovingOccupant: true });
    if (nextSegment) return nextSegment;
  }

  const routeNext = nextRuntimeRouteTile(robot, source);
  return runtimeSegmentFromTiles(robot, source, routeNext, { allowMovingOccupant: true, visualOnly: true });
}

function advanceRuntimeSegment(robot, fromTileId) {
  const direction = robot.motionDirection === -1 ? -1 : 1;
  let routeNext = runtimeRouteNeighbor(robot, fromTileId, direction);
  if (!routeNext) {
    robot.motionDirection = direction === 1 ? -1 : 1;
    routeNext = runtimeRouteNeighbor(robot, fromTileId, robot.motionDirection);
  }
  return runtimeSegmentFromTiles(robot, fromTileId, routeNext, { allowMovingOccupant: true, visualOnly: true });
}

function poseFromSegment(segment) {
  const t = clamp(segment.progress, 0, 1);
  const eased = t * t * (3 - 2 * t);
  const dx = segment.destination[0] - segment.source[0];
  const dy = segment.destination[1] - segment.source[1];
  return {
    x: segment.source[0] + dx * eased,
    y: segment.source[1] + dy * eased,
    heading: Math.atan2(dy, dx),
    direction: directionFromDelta(dx, dy),
    local: t,
  };
}

function staticRuntimePose(robot) {
  const center = tileCenterOrNull(robot.visualTileId || robot.tileId) || robot.route?.[0] || [0.5, 0.5];
  const next = tileCenterOrNull(robot.nextTileId) || robot.route?.[1] || center;
  return {
    x: center[0],
    y: center[1],
    heading: Math.atan2(next[1] - center[1], next[0] - center[0]),
    direction: directionFromDelta(next[0] - center[0], next[1] - center[1]),
    local: 0,
  };
}

function routePosition(route, phase) {
  const playbackRoute = cardinalizeRoute(route);
  if (!playbackRoute.length) return { x: 0, y: 0, heading: 0, direction: "s", local: 0 };
  if (playbackRoute.length === 1 || state.runtimeLinked) {
    const point = playbackRoute[0];
    const next = playbackRoute[1] || point;
    return {
      x: point[0],
      y: point[1],
      heading: Math.atan2(next[1] - point[1], next[0] - point[0]),
      direction: directionFromDelta(next[0] - point[0], next[1] - point[1]),
      local: 0,
    };
  }

  const segments = [];
  let total = 0;
  for (let i = 0; i < playbackRoute.length - 1; i += 1) {
    const a = playbackRoute[i];
    const b = playbackRoute[i + 1];
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (length <= 0.001) continue;
    segments.push({ a, b, length });
    total += length;
  }
  if (!segments.length || total <= 0) return { x: playbackRoute[0][0], y: playbackRoute[0][1], heading: 0, direction: "s", local: 0 };

  const normalized = ((phase % 1) + 1) % 1;
  const reverse = normalized > 0.5;
  let target = (reverse ? (1 - normalized) * 2 : normalized * 2) * total;
  for (const segment of segments) {
    if (target <= segment.length) {
      const local = target / segment.length;
      const eased = local * local * (3 - 2 * local);
      const dx = segment.b[0] - segment.a[0];
      const dy = segment.b[1] - segment.a[1];
      const headingDx = reverse ? -dx : dx;
      const headingDy = reverse ? -dy : dy;
      return {
        x: segment.a[0] + dx * eased,
        y: segment.a[1] + dy * eased,
        heading: Math.atan2(headingDy, headingDx),
        direction: directionFromDelta(headingDx, headingDy),
        local,
      };
    }
    target -= segment.length;
  }
  const last = playbackRoute[playbackRoute.length - 1];
  return { x: last[0], y: last[1], heading: 0, direction: "s", local: 1 };
}

function robotDisplayPosition(robot) {
  if (state.runtimeLinked) return robot.visualPose || staticRuntimePose(robot);
  return routePosition(robot.route, robot.phase);
}

function robotStatus(robot) {
  if (robot.status) return robot.status;
  const phase = ((robot.phase % 1) + 1) % 1;
  if (phase < 0.16) return "IDLE";
  if (phase < 0.34) return "MOVING";
  if (state.load === "high" && robot.id === "Q-04" && phase > 0.44 && phase < 0.62) return "BLOCKED";
  if (phase < 0.49) return "LOADING";
  if (phase < 0.68) return "MOVING";
  if (phase < 0.82) return "UNLOADING";
  return "WAITING";
}

function drawRoute(route, color, active) {
  const displayRoute = cardinalizeRoute(route);
  if (displayRoute.length < 2) return;
  const s = view.tileW / 76;
  ctx.save();
  ctx.lineCap = "square";
  ctx.lineJoin = "miter";
  ctx.globalAlpha = active ? 0.8 : 0.34;
  ctx.lineWidth = active ? Math.max(3, 2.2 * s) : Math.max(1, 1.4 * s);
  ctx.setLineDash(active ? [11 * s, 7 * s] : [5 * s, 9 * s]);
  ctx.beginPath();
  displayRoute.forEach(([x, y], index) => {
    const p = project(x, y, 0.06);
    if (index === 0) ctx.moveTo(p.x, p.y);
    else ctx.lineTo(p.x, p.y);
  });
  ctx.strokeStyle = "rgba(0,0,0,0.86)";
  ctx.lineWidth = active ? Math.max(5, 4 * s) : Math.max(2, 2 * s);
  ctx.stroke();
  ctx.strokeStyle = active ? color : PIXEL_PALETTE.cyanDim;
  ctx.lineWidth = active ? Math.max(2, 1.8 * s) : Math.max(1, 1.2 * s);
  ctx.stroke();

  displayRoute.filter((_, index) => index % 3 === 0).forEach(([x, y]) => {
    const p = project(x, y, 0.065);
    ctx.fillStyle = "rgba(0,0,0,0.86)";
    ctx.fillRect(snap(p.x - 3 * s), snap(p.y - 3 * s), snap(6 * s), snap(6 * s));
    ctx.fillStyle = active ? color : "rgba(50,201,244,0.4)";
    ctx.fillRect(snap(p.x - 2 * s), snap(p.y - 2 * s), snap(4 * s), snap(4 * s));
  });
  ctx.restore();
}

function drawRobot(robot) {
  const pos = robotDisplayPosition(robot);
  const status = robotStatus(robot);
  const color = robot.color;
  const center = project(pos.x, pos.y, 0.05);
  const s = view.tileW / 76;

  const shadow = [
    project(pos.x - 0.38, pos.y - 0.02, 0.02),
    project(pos.x - 0.02, pos.y - 0.28, 0.02),
    project(pos.x + 0.42, pos.y + 0.02, 0.02),
    project(pos.x + 0.02, pos.y + 0.28, 0.02),
  ];
  pixelPoly(shadow, "rgba(0,0,0,0.38)", null, Math.max(1, 1 * s));

  drawIsoBoxAt(pos.x - 0.3, pos.y - 0.22, 0.6, 0.44, 0.08, 0.16, {
    top: "#536c7a",
    left: "#182a35",
    right: "#2d4a5b",
  }, PIXEL_PALETTE.outline);

  drawIsoBoxAt(pos.x - 0.2, pos.y - 0.14, 0.4, 0.28, 0.23, 0.12, {
    top: PIXEL_PALETTE.orange,
    left: PIXEL_PALETTE.orangeDark,
    right: "#c45b19",
  }, PIXEL_PALETTE.outline);

  drawIsoBoxAt(pos.x - 0.03, pos.y - 0.09, 0.22, 0.18, 0.36, 0.1, {
    top: "#3ddf96",
    left: "#0d412e",
    right: "#16815a",
  }, PIXEL_PALETTE.outline);

  const footOffsets = [
    [-0.28, -0.2],
    [0.22, -0.18],
    [-0.26, 0.2],
    [0.24, 0.18],
  ];
  footOffsets.forEach(([dx, dy], index) => {
    drawIsoBoxAt(pos.x + dx, pos.y + dy, 0.1, 0.1, 0.03, 0.07, {
      top: index % 2 ? "#8ca5b2" : "#6c8391",
      left: "#05070a",
      right: "#142632",
    }, PIXEL_PALETTE.outline);
  });

  if (robot.carrying || status === "LOADING" || status === "UNLOADING") {
    drawIsoBoxAt(pos.x - 0.17, pos.y + 0.02, 0.28, 0.22, 0.42, 0.16, {
      top: "#f0a338",
      left: "#78320f",
      right: "#b44b16",
    }, PIXEL_PALETTE.outline);
  }

  const armStart = project(pos.x + 0.2, pos.y - 0.05, 0.36);
  const armEnd = project(pos.x + 0.46, pos.y - 0.22, 0.28 + Math.sin(state.simTime * 0.006 + robot.phase * 8) * 0.05);
  ctx.save();
  ctx.strokeStyle = "rgba(0,0,0,0.86)";
  ctx.lineWidth = Math.max(5, 5 * s);
  ctx.lineCap = "square";
  ctx.beginPath();
  ctx.moveTo(armStart.x, armStart.y);
  ctx.lineTo(armEnd.x, armEnd.y);
  ctx.stroke();
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(3, 3 * (view.tileW / 76));
  ctx.beginPath();
  ctx.moveTo(armStart.x, armStart.y);
  ctx.lineTo(armEnd.x, armEnd.y);
  ctx.stroke();
  ctx.fillStyle = "rgba(0,0,0,0.86)";
  ctx.fillRect(armEnd.x - 5 * s, armEnd.y - 5 * s, 10 * s, 10 * s);
  ctx.fillStyle = color;
  ctx.fillRect(snap(armEnd.x - 3 * s), snap(armEnd.y - 3 * s), snap(6 * s), snap(6 * s));
  const statusPixel = project(pos.x - 0.19, pos.y - 0.08, 0.42);
  ctx.fillStyle = "#05070a";
  ctx.fillRect(snap(statusPixel.x - 7 * s), snap(statusPixel.y - 3 * s), snap(14 * s), snap(6 * s));
  ctx.fillStyle = "#62ff6d";
  ctx.fillRect(snap(statusPixel.x - 5 * s), snap(statusPixel.y - 1.5 * s), snap(10 * s), snap(3 * s));
  ctx.restore();

  drawRobotTag(robot, status, center.x, center.y - 18, color);
}

function drawRobotTag(robot, status, x, y, color) {
  const s = view.tileW / 76;
  const text = `${robot.id} ${displayRobotStatus(status)}`;
  ctx.save();
  ctx.font = `700 ${Math.round(10 * s)}px Monaco, "Courier New", monospace`;
  const width = ctx.measureText(text).width + 12 * s;
  ctx.fillStyle = "rgba(4,7,10,0.94)";
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, s);
  ctx.beginPath();
  const left = x - width / 2;
  const top = y - 23 * s;
  ctx.moveTo(left, top + 4 * s);
  ctx.lineTo(left + 4 * s, top);
  ctx.lineTo(left + width - 4 * s, top);
  ctx.lineTo(left + width, top + 4 * s);
  ctx.lineTo(left + width, top + 18 * s);
  ctx.lineTo(left, top + 18 * s);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,0.92)";
  ctx.lineWidth = Math.max(2, 2 * s);
  ctx.stroke();
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, s);
  ctx.stroke();
  ctx.fillStyle = "#eef4f8";
  ctx.textAlign = "center";
  ctx.fillStyle = "#05070a";
  ctx.fillText(text, x + 1.5 * s, y - 8.5 * s);
  ctx.fillStyle = "#eef4f8";
  ctx.fillText(text, x, y - 10 * s);
  ctx.restore();
}

function drawShelfGhost() {
  if (!state.dragShelf) return;
  const shelf = state.dragShelf;
  const p = project(shelf.x + shelf.w / 2, shelf.y + shelf.d / 2, 0.02);
  ctx.save();
  ctx.strokeStyle = "#f7b733";
  ctx.setLineDash([7, 5]);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(p.x, p.y, Math.max(22, view.tileW * 0.34), 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

function drawHumanRiskOverlay(humans = activeHumanAgents()) {
  const riskTiles = currentHumanRiskTilePoints(humans);
  riskTiles.forEach(([x, y], index) => {
    const pulse = 0.42 + Math.sin(state.simTime * 0.12 + index * 0.7) * 0.18;
    drawIsoFootprint(x, y, 1, 1, {
      fill: "rgba(255, 103, 61, 0.42)",
      alpha: clamp(pulse, 0.24, 0.62),
      expand: 0.04,
      z: 0.032,
    });
    drawSprite("LED", "led_edge_congestion_red", tileAnchor(x, y), { alpha: clamp(0.36 + pulse, 0.42, 0.78) });
  });
}

function drawHumanShadow(human) {
  const p = project(human.x, human.y, 0.05);
  const s = spriteScale();
  ctx.save();
  ctx.globalAlpha = 0.36;
  ctx.fillStyle = "rgba(0,0,0,0.72)";
  ctx.beginPath();
  ctx.ellipse(p.x, p.y + 7 * s, 15 * s, 7 * s, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawHumanAgent(human) {
  const p = project(human.x, human.y, 0.18);
  const s = spriteScale();
  const bob = Math.sin(state.simTime * (human.mode === "running" ? 0.24 : 0.12) + human.x) * 2 * s;
  const color = human.mode === "running" ? "#ff6b3d" : human.color || "#ffbf3d";
  ctx.save();
  ctx.lineWidth = Math.max(1, 1.6 * s);
  ctx.strokeStyle = "rgba(0,0,0,0.82)";
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(p.x, p.y - 31 * s + bob, 6 * s, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = human.profile === "visitor_group" ? "#8adfff" : color;
  ctx.fillRect(Math.round(p.x - 5 * s), Math.round(p.y - 26 * s + bob), Math.round(10 * s), Math.round(18 * s));
  ctx.strokeRect(Math.round(p.x - 5 * s), Math.round(p.y - 26 * s + bob), Math.round(10 * s), Math.round(18 * s));
  ctx.strokeStyle = color;
  ctx.beginPath();
  ctx.moveTo(p.x - 4 * s, p.y - 9 * s + bob);
  ctx.lineTo(p.x - 10 * s, p.y + 4 * s);
  ctx.moveTo(p.x + 4 * s, p.y - 9 * s + bob);
  ctx.lineTo(p.x + 10 * s, p.y + 4 * s);
  ctx.moveTo(p.x - 4 * s, p.y - 22 * s + bob);
  ctx.lineTo(p.x - 11 * s, p.y - 15 * s);
  ctx.moveTo(p.x + 4 * s, p.y - 22 * s + bob);
  ctx.lineTo(p.x + 11 * s, p.y - 15 * s);
  ctx.stroke();
  if (human.mode === "stopped") drawWorldLabel("WAIT", p.x, p.y - 44 * s, "#ffbf3d");
  if (human.mode === "running") drawWorldLabel("RUN", p.x, p.y - 44 * s, "#ff6b3d");
  ctx.restore();
}

function render() {
  ctx.clearRect(0, 0, view.width, view.height);
  drawBackground();

  state.robots
    .filter((robot) => robot.route && robot.route.length > 1)
    .slice(0, state.runtimeLinked ? 5 : 3)
    .forEach((robot, index) => drawRoute(robot.route, robot.color, index === 0));

  const humans = activeHumanAgents();
  drawHumanRiskOverlay(humans);

  const facilities = activeFacilitySprites();
  const objects = [
    ...facilities.map((prop) => ({ type: "facility", depth: prop.depth, value: prop })),
    ...state.shelves.map((shelf) => ({ type: "rack", depth: shelf.anchorX + shelf.anchorY + shelf.length * 0.25, value: shelf })),
    ...humans.map((human) => ({ type: "human", depth: human.x + human.y + 0.62, value: human })),
    ...state.robots.map((robot) => {
      const pos = robotDisplayPosition(robot);
      return { type: "robot", depth: pos.x + pos.y + 0.6, value: robot };
    }),
  ].sort((a, b) => a.depth - b.depth);

  state.shelves.forEach((shelf) => drawRackShadow(shelf));
  facilities.forEach((prop) => drawFacilityShadow(prop));
  humans.forEach((human) => drawHumanShadow(human));
  state.robots.forEach((robot) => drawRobotShadow(robot));

  objects.forEach((object, index) => {
    if (object.type === "facility") drawFacilitySprite(object.value);
    else if (object.type === "rack") drawRackSprite(object.value);
    else if (object.type === "human") drawHumanAgent(object.value);
    else drawRobotSprite(object.value, state.robots.indexOf(object.value));
  });

  drawShelfGhost();

  canvasCtx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  canvasCtx.imageSmoothingEnabled = false;
  canvasCtx.drawImage(pixelCanvas, 0, 0, canvas.clientWidth, canvas.clientHeight);
}

function drawPulseHighlights() {
  const pulse = (Math.sin(state.simTime * 0.018) + 1) * 0.5;
  const s = view.tileW / 76;
  const targets = [
    { x: 4.9, y: 2.8, color: "#38cae8", label: "PICK" },
    { x: 6.7, y: 5.8, color: "#5cdd61", label: "HANDOFF" },
    { x: 8.1, y: 6.9, color: "#f7b733", label: "DROP" },
  ];
  targets.forEach((target) => {
    const p = project(target.x, target.y, 0.09);
    ctx.save();
    ctx.strokeStyle = target.color;
    ctx.lineWidth = Math.max(2, 2 * s);
    ctx.globalAlpha = 0.35 + pulse * 0.45;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 12 * s + pulse * 12 * s, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
    if (pulse > 0.64) drawWorldLabel(target.label, p.x, p.y - 8 * s, target.color);
  });
}

function formatTime(seconds) {
  const total = Math.floor(seconds);
  const hh = String(Math.floor(total / 3600) % 24).padStart(2, "0");
  const mm = String(Math.floor(total / 60) % 60).padStart(2, "0");
  const ss = String(total % 60).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function metricValue(base, variance, freq = 0.02) {
  return base + Math.sin(state.simTime * freq + base) * variance;
}

function formatAge(seconds) {
  const total = Math.max(0, Math.floor(seconds));
  const mm = String(Math.floor(total / 60)).padStart(2, "0");
  const ss = String(total % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function agingClass(seconds) {
  if (seconds >= 165) return "late";
  if (seconds >= 85) return "aging";
  return "fresh";
}

function statusClass(status) {
  return status.toLowerCase();
}

function renderThroughputBars(completed) {
  if (!els.throughputBars) return;
  const bars = Array.from(els.throughputBars.querySelectorAll("i"));
  bars.forEach((bar, index) => {
    const pulse = Math.sin(state.simTime * 0.012 + index * 0.72) * 10;
    const drift = state.load === "high" ? 10 : state.load === "low" ? -8 : 0;
    const height = clamp(42 + index * 4.1 + pulse + drift + completed * 0.015, 24, 96);
    bar.style.height = `${height}%`;
  });
}

function updateDom() {
  const profile = loadProfiles[state.load] || loadProfiles.medium;
  const snapshot = state.runtimeSnapshot;
  const metrics = state.runtimeMetrics || {};
  const orders = snapshot?.orders || {};
  const runtime = snapshot?.runtime || {};
  const movementLocks = snapshot?.movement_locks || {};
  const humans = activeHumanAgents();
  const humanRiskTiles = currentHumanRiskTileIds(humans);
  const humanActiveCount = humans.length;
  const humanRiskCount = humanRiskTiles.size;

  const fallbackCompleted = Math.round(metricValue(profile.completed, 7, 0.005));
  const fallbackQueue = Math.round(metricValue(profile.queue, 6, 0.012));
  const completedOrders = metrics.completed_orders ?? fallbackCompleted;
  const completedRate = orders.completed_per_hr ?? metrics.throughput_orders_per_simulated_hour ?? fallbackCompleted;
  const createdRate = orders.created_per_hr ?? profile.created;
  const activeOrders = orders.active ?? clamp(fallbackQueue, 8, 140);
  const pendingOrders = orders.pending ?? clamp(fallbackQueue + (state.load === "high" ? 45 : state.load === "low" ? 18 : 34), 18, 180);
  const queue = orders.open ?? activeOrders;
  const slaRisk = orders.sla_risk ?? Math.max(2, Math.round(queue * (state.load === "high" ? 0.22 : state.load === "low" ? 0.08 : 0.14)));
  const replanCount = metrics.replan_count ?? runtime.replans ?? Math.max(1, Math.round(metricValue(state.load === "high" ? 14 : state.load === "low" ? 3 : 7, 2, 0.018)));
  const deadlockCount = metrics.deadlock_count ?? runtime.deadlocks ?? Math.max(0, Math.round(metricValue(state.load === "high" ? 4 : state.load === "low" ? 0.6 : 2, 1.1, 0.015)));
  const baseActiveSkillCount = runtime.active_skills?.length ?? (state.load === "high" ? 16 : state.load === "low" ? 8 : 12);
  const activeSkillCount = baseActiveSkillCount + (humanActiveCount && !(runtime.active_skills || []).includes("human_aware_reroute") ? 1 : 0);
  const tileLocks = runtimeLockCount(snapshot);
  const deniedLocks = movementLocks.denied_moves?.length || 0;
  const congestion = snapshot
    ? deniedLocks + humanRiskCount + state.robots.filter((robot) => robot.status === "BLOCKED" || robot.status === "WAITING").length
    : Math.max(0, Math.round(metricValue(profile.congestion, 5, 0.014))) + humanRiskCount;
  const utilization = metrics.robot_utilization_pct ?? clamp(Math.round(metricValue(profile.utilization, 4, 0.01)), 0, 99);
  const fulfillment = orders.avg_fulfillment_min ?? Math.max(7.5, metricValue(profile.fulfill, 1.1, 0.008)).toFixed(1);
  const healthBad = (runtime.route_blocked_tile_violations || 0) + (runtime.route_cardinality_violations || 0) + (runtime.collision_violations || 0) + (runtime.lock_overlap_violations || 0);
  const displayTick = Math.floor(state.tick);

  if (els.runState) els.runState.textContent = state.running ? "Live" : "Paused";
  if (els.simClock) els.simClock.textContent = formatTime(state.simTime);
  if (els.tickLabel) els.tickLabel.textContent = `Tick ${String(displayTick).padStart(4, "0")}`;
  if (els.activeLoadBadge) els.activeLoadBadge.textContent = `${capitalize(state.load)} Load`;
  if (els.speedBadge) els.speedBadge.textContent = `${state.speed}x`;
  if (els.recordBadge) els.recordBadge.textContent = state.recording ? "Recording" : "Standby";
  if (els.runtimeLinkBadge) els.runtimeLinkBadge.textContent = state.humanIntrusionEnabled && state.humanScenario ? "Human Runtime" : state.runtimeEvents.length ? "Runtime Events" : state.runtimeLinked ? "Runtime JSON" : "Mock Fallback";
  if (els.humanRiskBadge) els.humanRiskBadge.textContent = state.humanIntrusionEnabled ? humanScenarioSummary(humans) : "Human Risk Off";
  if (els.humanModeBtn) {
    els.humanModeBtn.textContent = state.humanIntrusionEnabled ? "Humans On" : "Humans Off";
    els.humanModeBtn.classList.toggle("active", state.humanIntrusionEnabled);
  }
  if (els.wallClock) els.wallClock.textContent = new Date().toLocaleTimeString("en-US", { hour12: false });
  if (els.ordersCompleted) els.ordersCompleted.textContent = `${completedOrders}`;
  if (els.throughputRate) els.throughputRate.textContent = `${Math.round(completedRate)}/hr`;
  if (els.activeOrders) els.activeOrders.textContent = `${activeOrders}`;
  if (els.pendingOrders) els.pendingOrders.textContent = `${pendingOrders}`;
  if (els.topRuntime) els.topRuntime.textContent = formatTime(state.simTime);
  if (els.topRobots) els.topRobots.textContent = String(state.robots.length).padStart(2, "0");
  if (els.topLocks) els.topLocks.textContent = String(tileLocks).padStart(2, "0");
  if (els.topThroughput) els.topThroughput.textContent = `${Math.round(completedRate)}/hr`;
  if (els.topQueue) els.topQueue.textContent = `${queue}`;
  if (els.topSla) els.topSla.textContent = `${String(slaRisk).padStart(2, "0")}`;
  const mediumBenchmark = { baselineThroughput: 288, localThroughput: 324, upliftPct: 12.5, stressUpliftPct: 60.3 };
  const safetyViolations = healthBad;
  if (els.throughputTrend) {
    els.throughputTrend.textContent = state.runtimeLinked ? `Stress +${mediumBenchmark.stressUpliftPct.toFixed(1)}%` : (state.load === "high" ? "+31%" : state.load === "low" ? "+09%" : "+18%");
  }
  if (els.baselineThroughput) els.baselineThroughput.textContent = `${mediumBenchmark.baselineThroughput}/hr`;
  if (els.localThroughput) els.localThroughput.textContent = `${mediumBenchmark.localThroughput}/hr`;
  if (els.safetyViolations) els.safetyViolations.textContent = `${safetyViolations}`;
  if (els.queuePressure) els.queuePressure.textContent = `${queue} open`;
  if (els.congestion) els.congestion.textContent = `${congestion}`;
  if (els.utilization) els.utilization.textContent = `${Math.round(utilization)}%`;
  if (els.fulfillment) els.fulfillment.textContent = `${Number(fulfillment).toFixed(1)} min`;
  if (els.queueA2) els.queueA2.value = clamp(queue + deniedLocks * 5, 0, 100);
  if (els.queueB1) els.queueB1.value = clamp(activeOrders * 3, 0, 100);
  if (els.queuePack) els.queuePack.value = clamp(pendingOrders + congestion * 4, 0, 100);
  if (els.pipelineState) els.pipelineState.textContent = state.planner ? (state.runtimeLinked ? "Linked" : "Optimizing") : "Manual";
  if (els.activeSkillCount) els.activeSkillCount.textContent = `${activeSkillCount}`;
  if (els.deadlockCount) els.deadlockCount.textContent = `${String(deadlockCount).padStart(2, "0")}`;
  if (els.replanCount) els.replanCount.textContent = `${String(replanCount).padStart(2, "0")}`;
  if (els.leftTileLocks) els.leftTileLocks.textContent = `${String(tileLocks).padStart(2, "0")}`;
  const judgeDecision = currentJudgeDecision(snapshot, runtime, movementLocks);
  if (els.schedulerDecision) els.schedulerDecision.textContent = runtime.latest_decision || state.log[state.log.length - 1] || "Awaiting runtime event.";
  if (els.judgeDecisionText) els.judgeDecisionText.textContent = judgeDecision.text;
  if (els.judgeDecisionRobot) els.judgeDecisionRobot.textContent = judgeDecision.robot;
  if (els.judgeDecisionLock) els.judgeDecisionLock.textContent = judgeDecision.lock;
  if (els.judgeDecisionSkill) els.judgeDecisionSkill.textContent = judgeDecision.skill;
  if (els.plannerMetricOrders) els.plannerMetricOrders.textContent = `${completedOrders}/${createdRate ? Math.max(completedOrders, Math.round(createdRate * 0.35)) : "140"}`;
  if (els.plannerMetricLocks) els.plannerMetricLocks.textContent = String(tileLocks).padStart(2, "0");
  if (els.plannerMetricReplans) els.plannerMetricReplans.textContent = String(replanCount).padStart(2, "0");
  if (els.plannerTableInput) els.plannerTableInput.textContent = `${capitalize(state.load)} load / ${pendingOrders} pending / ${congestion} congestion signals / ${humanActiveCount} humans`;
  if (els.plannerTableDecision) els.plannerTableDecision.textContent = `${judgeDecision.robot} reserves ${judgeDecision.lock}, then runs ${judgeDecision.skill}`;
  if (els.plannerTableOutput) els.plannerTableOutput.textContent = `${Math.round(completedRate)}/hr, ${safetyViolations} safety violations, ${Math.round(utilization)}% utilization, ${humanRiskCount} human-risk tiles`;
  if (els.plannerTextSummary) els.plannerTextSummary.textContent = `Planner graph: mission orders become workflow steps, human-risk projection, skill-graph actions, tile-lock reservations, and KPI updates. Current decision: ${judgeDecision.text}`;
  if (els.fleetMode) els.fleetMode.textContent = state.load === "high" ? "Surge" : state.load === "low" ? "Economy" : "Balanced";
  if (els.zoneHealth) els.zoneHealth.textContent = healthBad ? "Check" : (congestion ? "Busy" : "Clear");
  if (els.skuMix) els.skuMix.textContent = state.load === "high" ? "Heavy Mix" : state.load === "low" ? "Light Mix" : "Live Mix";
  if (els.contractState) els.contractState.textContent = state.runtimeLinked && !healthBad ? "Ready" : "Fallback";
  if (els.runtimeControlState) els.runtimeControlState.textContent = state.running ? "Ready" : "Paused";
  if (els.runtimeSnapshotPort) els.runtimeSnapshotPort.textContent = state.runtimeEvents.length ? `${state.load}.events` : state.runtimeLinked ? `${state.load}.json` : "mock";
  if (els.robotsPort) els.robotsPort.textContent = String(state.robots.length).padStart(2, "0");
  if (els.ordersPort) els.ordersPort.textContent = String(activeOrders).padStart(2, "0");
  if (els.locksPort) els.locksPort.textContent = String(tileLocks).padStart(2, "0");
  if (els.recorderPort) els.recorderPort.textContent = state.recording ? "active" : "standby";
  if (els.thinPending) els.thinPending.textContent = String(pendingOrders).padStart(3, "0");
  if (els.thinReplans) els.thinReplans.textContent = String(replanCount).padStart(2, "0");
  if (els.thinDeadlocks) els.thinDeadlocks.textContent = String(deadlockCount).padStart(2, "0");
  if (els.thinSkills) els.thinSkills.textContent = String(activeSkillCount).padStart(2, "0");
  if (els.thinRun) els.thinRun.textContent = state.planner ? "ON" : "OFF";
  if (els.pauseBtn) els.pauseBtn.textContent = state.running ? "Pause" : "Resume";
  if (els.plannerBtn) {
    els.plannerBtn.textContent = state.planner ? "On" : "Off";
    els.plannerBtn.classList.toggle("active", state.planner);
  }
  if (els.selectedShelf) els.selectedShelf.textContent = state.dragShelf ? state.dragShelf.id : state.selectedShelfId || "None";
  if (els.fleetCount) els.fleetCount.textContent = `${String(state.robots.length).padStart(2, "0")} AEGIS`;
  if (els.orderFlowMode) els.orderFlowMode.textContent = state.runtimeEvents.length ? "Event Replay" : state.runtimeLinked ? "Runtime Feed" : (state.load === "high" ? "Surge Feed" : state.load === "low" ? "Steady Feed" : "Live Feed");
  if (els.orderNewCount) els.orderNewCount.textContent = String(clamp(Math.round(createdRate / 10), 0, 99)).padStart(2, "0");
  if (els.orderAssignedCount) els.orderAssignedCount.textContent = String(clamp(activeOrders - pendingOrders, 0, 99)).padStart(2, "0");
  if (els.orderAgingCount) els.orderAgingCount.textContent = String(slaRisk).padStart(2, "0");
  if (els.skuInbound) els.skuInbound.textContent = String(clamp(Math.round(createdRate * 0.13), 0, 99)).padStart(2, "0");
  if (els.skuPickQueue) els.skuPickQueue.textContent = String(clamp(activeOrders + pendingOrders, 0, 99)).padStart(2, "0");
  if (els.skuOutbound) els.skuOutbound.textContent = String(clamp(Math.round(completedRate * 0.09), 0, 99)).padStart(2, "0");

  renderThroughputBars(Number(completedRate));
  renderLog();
  renderOrders();
  renderRobotStatus();
  renderOrderIntake();
}

function renderLog() {
  els.decisionLog.innerHTML = "";
  state.log.slice(-6).forEach((entry, index) => {
    const li = document.createElement("li");
    const tick = Math.floor(state.tick) - state.log.slice(-6).length + index + 1;
    li.innerHTML = `<b>[${String(Math.max(0, tick)).padStart(4, "0")}]</b> ${escapeHtml(entry)}`;
    els.decisionLog.appendChild(li);
  });
}

function renderRobotStatus() {
  if (!els.robotStatusList) return;
  els.robotStatusList.innerHTML = "";
  state.robots.forEach((robot, index) => {
    const status = robotStatus(robot);
    const fallback = robotTaskSeed[index % robotTaskSeed.length];
    const task = {
      order: robot.currentOrder || fallback.order,
      target: robot.currentTarget || fallback.target,
      next: robot.nextTarget || fallback.next,
      sku: robot.carriedSku || fallback.sku,
      weight: robot.carriedWeight || fallback.weight,
    };
    const displayStatus = displayRobotStatus(status);
    const previewId = `robotPreview${index}`;
    const battery = Math.round(robot.battery ?? 80);
    const lockPct = robot.lockPressurePct ?? clamp(38 + index * 6 + (status === "BLOCKED" ? 36 : status === "WAITING" ? 24 : 0), 24, 96);
    const row = document.createElement("div");
    row.className = `robot-row robot-module-card ${statusClass(status)}`;
    row.innerHTML = `
      <div class="robot-module-id"><strong>${escapeHtml(robot.id)}</strong><small>${escapeHtml(robot.tileId || "AEGIS")}</small></div>
      <span class="robot-sprite-cell"><canvas id="${previewId}" width="160" height="120" aria-label="${escapeHtml(robot.id)} sprite preview"></canvas></span>
      <div class="robot-module-main">
        <div class="robot-module-task">
          <span class="status-pill ${statusClass(status)}">${escapeHtml(displayStatus)}</span>
          <b>${escapeHtml(task.order)}</b>
        </div>
        <div class="robot-module-path">
          <small>target ${escapeHtml(task.target)}</small>
          <small>next ${escapeHtml(task.next)}</small>
        </div>
        <div class="robot-module-bars" aria-hidden="true">
          <span><i style="width:${battery}%"></i></span>
          <span class="lock-bar"><i style="width:${lockPct}%"></i></span>
        </div>
      </div>
      <div class="robot-module-cargo">
        <span>carried SKU</span>
        <strong>${escapeHtml(task.sku)}</strong>
        <small>${escapeHtml(task.weight)}kg</small>
      </div>
    `;
    els.robotStatusList.appendChild(row);
    drawRobotPreviewById(previewId, robot, index);
  });
}

function renderOrderIntake() {
  if (!els.orderIntakeList) return;
  els.orderIntakeList.innerHTML = "";
  state.orders.slice(0, 4).forEach((order, index) => {
    const age = state.runtimeLinked ? order.age : order.age + Math.floor(state.tick * 1.4) + (state.load === "high" ? index * 4 : 0);
    const severity = agingClass(age);
    const card = document.createElement("article");
    card.className = `order-intake-card ${severity}`;
    const sku = order.weight >= 4 ? "METAL" : order.weight >= 2 ? "WOOD" : "CARD";
    card.innerHTML = `
      <strong>${escapeHtml(order.id)}</strong>
      <span>${escapeHtml(order.priority)}</span>
      <small>${sku} / ${Number(order.weight || 0).toFixed(1)}kg / ${escapeHtml(order.status)} / ${formatAge(age)}</small>
    `;
    els.orderIntakeList.appendChild(card);
  });
}

function renderOrders() {
  if (!els.orderTable) return;
  els.orderTable.innerHTML = "";
  state.orders.forEach((order, index) => {
    const age = state.runtimeLinked ? order.age : order.age + Math.floor(state.tick * 1.7) + (state.load === "high" ? index * 5 : 0);
    const severity = agingClass(age);
    const row = document.createElement("div");
    row.className = `order-row ${severity}`;
    row.innerHTML = `
      <strong>${escapeHtml(order.id)}</strong>
      <span>${escapeHtml(order.priority)}</span>
      <span>${escapeHtml(order.difficulty)}</span>
      <span>${Number(order.weight || 0).toFixed(1)}kg</span>
      <span>${escapeHtml(order.robot)}</span>
      <span>${formatAge(age)}</span>
      <span>${escapeHtml(order.status)}</span>
    `;
    els.orderTable.appendChild(row);
  });
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function emitDecisionEvent() {
  const events = [
    "Assigned shelf_pick to Q-03 near A2.",
    "Rebalanced outbound lane after congestion spike.",
    "Validated handoff edge against MuJoCo contact totals.",
    "Rerouted Q-06 around B2 buffer zone.",
    "Packed high-priority order with two-hop transfer.",
    "Reserved charging window for Q-01.",
    "Skill graph selected basket carry over direct aisle crossing.",
  ];
  const event = events[state.tick % events.length];
  state.log.push(event);
  if (state.log.length > 22) state.log.shift();
}

function setFocusedSkill(skill) {
  state.focusSkill = skill;
  const meta = skillFocusMeta[skill] || skillFocusMeta.shelf_pick;
  if (els.selectedSkillStatus) els.selectedSkillStatus.textContent = meta.status;

  document.querySelectorAll("[data-focus-skill]").forEach((button) => {
    button.classList.toggle("active", button.dataset.focusSkill === skill);
  });

  document.querySelectorAll("[data-skill]").forEach((card) => {
    card.classList.toggle("active", card.dataset.skill === skill);
  });

  if (meta.log) state.log.push(meta.log);
  if (state.log.length > 22) state.log.shift();
}

function runtimeTilesPerSecond() {
  const nominalRobotSpeedMps = 1.0;
  const tileSizeM = 2.0;
  const physicalTilesPerSecond = nominalRobotSpeedMps / tileSizeM;
  return Math.min(12, physicalTilesPerSecond * Math.max(1, state.speed));
}

function holdRuntimeRobot(robot) {
  robot.motion = null;
  robot.visualPose = staticRuntimePose(robot);
  robot.visualTileId = robot.tileId || robot.visualTileId;
}

function stepRuntimeEventRobotAnimation(robot) {
  if (!robot.motion) {
    holdRuntimeRobot(robot);
    return;
  }

  const elapsed = (state.runtimeReplayTick || state.tick || 0) - Number(robot.motion.startTick || 0);
  robot.motion.progress = clamp(elapsed / Math.max(0.001, Number(robot.motion.durationTicks || 1)), 0, 1);
  robot.visualPose = poseFromSegment(robot.motion);
  if (robot.motion.progress >= 1) {
    robot.visualTileId = robot.motion.destinationTileId;
    robot.tileId = robot.motion.destinationTileId;
    robot.motion = null;
    robot.visualPose = staticRuntimePose(robot);
  }
}

function stepRuntimeRobotAnimation(robot, dt) {
  if (state.runtimeEvents.length) {
    stepRuntimeEventRobotAnimation(robot);
    return;
  }

  if (!runtimeRobotCanMove(robot)) {
    holdRuntimeRobot(robot);
    return;
  }

  if (robot.motion?.done) {
    robot.motion = advanceRuntimeSegment(robot, robot.visualTileId || robot.motion.destinationTileId);
    if (!robot.motion) {
      robot.visualPose = staticRuntimePose(robot);
      return;
    }
  }

  if (!robot.motion) {
    robot.motion = initialRuntimeSegment(robot);
    if (!robot.motion) {
      holdRuntimeRobot(robot);
      return;
    }
    robot.visualTileId = robot.motion.sourceTileId;
  }

  robot.motion.progress += dt * runtimeTilesPerSecond();

  while (robot.motion && robot.motion.progress >= 1) {
    const overflow = robot.motion.progress - 1;
    const reachedTile = robot.motion.destinationTileId;
    robot.visualTileId = reachedTile;
    const nextSegment = advanceRuntimeSegment(robot, reachedTile);
    if (!nextSegment) {
      robot.motion.progress = 1;
      robot.motion.done = true;
      break;
    }
    nextSegment.progress = Math.min(overflow, 0.98);
    robot.motion = nextSegment;
  }

  robot.visualPose = robot.motion ? poseFromSegment(robot.motion) : staticRuntimePose(robot);
}

function updateRuntimeDebugAttributes() {
  const humans = activeHumanAgents();
  const humanRiskCount = currentHumanRiskTileIds(humans).size;
  const movingRobots = state.robots.filter((robot) => robot.motion && !robot.motion.done && robot.visualPose);
  const visualBlockedViolations = state.robots.filter((robot) => {
    if (!robot.visualPose) return false;
    const tileId = pointToTileId([robot.visualPose.x, robot.visualPose.y]);
    return tileId ? state.runtimeBlockedTiles?.has(tileId) : false;
  });
  document.documentElement.dataset.runtimeLinked = state.runtimeLinked ? "true" : "false";
  document.documentElement.dataset.runtimeLoad = state.load;
  document.documentElement.dataset.runtimeSpeed = String(state.speed);
  document.documentElement.dataset.runtimeTick = String(Math.floor(state.tick));
  document.documentElement.dataset.runtimeMovingRobots = String(movingRobots.length);
  document.documentElement.dataset.runtimeBlockedVisualViolations = String(visualBlockedViolations.length);
  document.documentElement.dataset.humanIntrusionEnabled = state.humanIntrusionEnabled ? "true" : "false";
  document.documentElement.dataset.humanActiveCount = String(humans.length);
  document.documentElement.dataset.humanRiskTiles = String(humanRiskCount);
  document.documentElement.dataset.runtimeVisualSample = state.robots
    .map((robot) => {
      const pose = robot.visualPose || staticRuntimePose(robot);
      return `${robot.id}:${pose.x.toFixed(2)},${pose.y.toFixed(2)}`;
    })
    .join("|");
}

function stepSimulation(dt) {
  if (!state.running) return;
  if (state.runtimeLinked) {
    if (state.runtimeEvents.length) {
      state.runtimeReplayTick += dt * state.speed;
      if (state.runtimeReplayTick > state.runtimeReplayEndTick) {
        restartRuntimeEventReplay();
        return;
      }
      state.tick = state.runtimeReplayTick;
      state.simTime = state.runtimeReplayTick;
      applyRuntimeEventsThrough(state.runtimeReplayTick);
      state.robots.forEach((robot) => stepRuntimeRobotAnimation(robot, dt));
      pruneRuntimeActiveLocks();
      syncRuntimeOrderRows();
      return;
    }
    state.simTime += dt * state.speed;
    state.tick += dt * state.speed;
    state.robots.forEach((robot) => stepRuntimeRobotAnimation(robot, dt));
    return;
  }
  const loadBoost = state.load === "low" ? 0.75 : state.load === "high" ? 1.45 : 1;
  state.simTime += dt * state.speed * 18;
  state.robots.forEach((robot, index) => {
    robot.phase = (robot.phase + dt * state.speed * loadBoost * (0.006 + index * 0.00035)) % 1;
    robot.battery = clamp(robot.battery - dt * 0.008 * state.speed + (robotStatus(robot) === "IDLE" ? dt * 0.02 : 0), 18, 98);
    robot.carrying = ["LOADING", "MOVING", "UNLOADING"].includes(robotStatus(robot)) && index % 3 !== 0;
  });

  const nextTick = Math.floor(state.simTime / 12);
  if (nextTick > state.tick) {
    state.tick = nextTick;
    emitDecisionEvent();
  }
}

async function setLoad(load) {
  state.load = load;
  document.querySelectorAll("[data-load]").forEach((button) => {
    button.classList.toggle("active", button.dataset.load === load);
  });
  state.log.push(`Load profile switched to ${load}.`);
  if (state.log.length > 22) state.log.shift();
  await loadRuntimeProfile(load);
  updateDom();
  render();
}

function setSpeed(speed) {
  state.speed = Number(speed);
  document.querySelectorAll("[data-speed]").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.speed) === state.speed);
  });
  state.log.push(`Runtime time scale set to ${state.speed}x.`);
}

async function toggleHumanIntrusion() {
  state.humanIntrusionEnabled = !state.humanIntrusionEnabled;
  state.log.push(state.humanIntrusionEnabled
    ? "Human intrusion scenario enabled: planner projects continuous people into temporary risk tiles."
    : "Human intrusion scenario disabled: standard robot-only runtime loaded.");
  if (state.log.length > 22) state.log.shift();
  await loadRuntimeProfile(state.load);
  updateDom();
  updateRuntimeDebugAttributes();
  render();
}

async function resetSimulation() {
  state.running = true;
  state.speed = 1;
  state.load = "high";
  state.simTime = 9300;
  state.tick = 0;
  state.shelves = cloneData(shelvesSeed);
  state.selectedShelfId = "A2";
  state.dragShelf = null;
  state.orders = cloneData(orderSeed);
  state.ledTiles = cloneData(ledTiles);
  state.robots = routeSets.map((route, index) => ({
    id: `Q-${String(index + 1).padStart(2, "0")}`,
    route,
    phase: index / routeSets.length,
    color: robotPalette[index],
    battery: 86 - index * 4,
    carrying: index % 3 === 0,
  }));
  state.log = [
    "Runtime reset to medium load release.",
    "Skill graph linked to MuJoCo shelf_pick and handoff evidence.",
    "Congestion-aware planner assigned A2 priority route.",
  ];
  state.focusSkill = "shelf_pick";
  setSpeed(1);
  await setLoad("high");
  setFocusedSkill("shelf_pick");
}

async function toggleRecording() {
  if (!window.MediaRecorder || !canvas.captureStream) {
    state.log.push("Canvas recording is unavailable in this browser.");
    return;
  }

  if (!state.recording) {
    const stream = canvas.captureStream(30);
    state.recordChunks = [];
    try {
      state.recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
    } catch {
      state.recorder = new MediaRecorder(stream);
    }
    state.recorder.ondataavailable = (event) => {
      if (event.data.size > 0) state.recordChunks.push(event.data);
    };
    state.recorder.onstop = () => {
      const blob = new Blob(state.recordChunks, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `agentic-warehouse-runtime-${Date.now()}.webm`;
      link.click();
      URL.revokeObjectURL(url);
      state.log.push("Canvas runtime recording exported.");
    };
    state.recorder.start();
    state.recording = true;
    if (els.recordBtn) {
      els.recordBtn.classList.add("recording");
      els.recordBtn.textContent = "Stop Rec";
    }
    state.log.push("Canvas runtime recording started.");
  } else {
    state.recorder.stop();
    state.recording = false;
    if (els.recordBtn) {
      els.recordBtn.classList.remove("recording");
      els.recordBtn.textContent = "Record";
    }
  }
}

function pointerPosition(event) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = (canvas.clientWidth / rect.width) * GAME_PIXEL_RATIO;
  const scaleY = (canvas.clientHeight / rect.height) * GAME_PIXEL_RATIO;
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY,
  };
}

function nearestShelf(point) {
  let best = null;
  let bestDistance = Infinity;
  state.shelves.forEach((shelf) => {
    const center = worldAnchor(shelf.anchorX, shelf.anchorY);
    const distance = Math.hypot(point.x - center.x, point.y - center.y);
    if (distance < bestDistance) {
      best = shelf;
      bestDistance = distance;
    }
  });
  return bestDistance < Math.max(42, view.tileW * 0.8) ? best : null;
}

function handlePointerDown(event) {
  const point = pointerPosition(event);
  const shelf = nearestShelf(point);
  if (!shelf) return;
  const gridPoint = screenToGrid(point.x, point.y);
  state.dragShelf = shelf;
  state.selectedShelfId = shelf.id;
  state.dragOffset.x = gridPoint.x - shelf.x;
  state.dragOffset.y = gridPoint.y - shelf.y;
  canvas.setPointerCapture(event.pointerId);
  state.running = false;
  state.log.push(`Shelf ${shelf.id} selected for layout adjustment.`);
}

function handlePointerMove(event) {
  if (!state.dragShelf) return;
  const point = pointerPosition(event);
  const gridPoint = screenToGrid(point.x, point.y);
  const shelf = state.dragShelf;
  shelf.x = clamp(Math.round(gridPoint.x - state.dragOffset.x), 0, grid.cols - shelf.w);
  shelf.y = clamp(Math.round(gridPoint.y - state.dragOffset.y), 0, grid.rows - shelf.d);
  shelf.anchorX = shelf.x + 1;
  shelf.anchorY = shelf.y + shelf.length;
}

function handlePointerUp(event) {
  if (!state.dragShelf) return;
  const id = state.dragShelf.id;
  state.log.push(`Shelf ${id} placement committed to runtime map.`);
  state.dragShelf = null;
  canvas.releasePointerCapture(event.pointerId);
}

async function loadSkillStats() {
  await Promise.all(Object.entries(skillJson).map(async ([skill, url]) => {
    try {
      const response = await fetch(url);
      if (!response.ok) return;
      const data = await response.json();
      const card = document.querySelector(`[data-skill="${skill}"]`);
      if (!card || !data.contact_totals) return;
      card.querySelectorAll("[data-stat]").forEach((node) => {
        const key = node.dataset.stat;
        if (data.contact_totals[key] !== undefined) node.textContent = String(data.contact_totals[key]);
      });
    } catch {
      // Opening the UI directly from file:// can block JSON fetches; static fallback stats remain visible.
    }
  }));
}

function bindEvents() {
  window.addEventListener("resize", () => {
    scaleDesignSurface();
    resizeCanvas();
    render();
  });

  document.querySelectorAll("[data-load]").forEach((button) => {
    button.addEventListener("click", () => setLoad(button.dataset.load));
  });

  document.querySelectorAll("[data-speed]").forEach((button) => {
    button.addEventListener("click", () => setSpeed(button.dataset.speed));
  });

  document.querySelectorAll("[data-focus-skill]").forEach((button) => {
    button.addEventListener("click", () => setFocusedSkill(button.dataset.focusSkill));
  });

  if (els.pauseBtn) {
    els.pauseBtn.addEventListener("click", () => {
      state.running = !state.running;
      state.log.push(state.running ? "Runtime resumed." : "Runtime paused.");
    });
  }

  if (els.tickBtn) {
    els.tickBtn.addEventListener("click", () => {
      state.simTime += 12 * state.speed;
      state.tick += 1;
      emitDecisionEvent();
      state.running = false;
    });
  }

  if (els.resetBtn) els.resetBtn.addEventListener("click", resetSimulation);

  if (els.recordBtn) els.recordBtn.addEventListener("click", toggleRecording);

  if (els.humanModeBtn) els.humanModeBtn.addEventListener("click", toggleHumanIntrusion);

  if (els.detailModeBtn) {
    els.detailModeBtn.addEventListener("click", () => {
      const simple = document.body.classList.toggle("judge-simple");
      els.detailModeBtn.textContent = simple ? "Show Ops Detail" : "Back To Judge View";
      requestAnimationFrame(() => {
        scaleDesignSurface();
        resizeCanvas();
        render();
      });
    });
  }

  if (els.plannerBtn) {
    els.plannerBtn.addEventListener("click", () => {
      state.planner = !state.planner;
      state.log.push(state.planner ? "Agentic planner enabled." : "Planner switched to manual queue mode.");
    });
  }

  document.querySelectorAll("[data-planner-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.plannerTab;
      document.querySelectorAll("[data-planner-tab]").forEach((node) => node.classList.toggle("active", node === button));
      document.querySelectorAll("[data-planner-panel]").forEach((panel) => panel.classList.toggle("active", panel.dataset.plannerPanel === tab));
    });
  });

  canvas.addEventListener("pointerdown", handlePointerDown);
  canvas.addEventListener("pointermove", handlePointerMove);
  canvas.addEventListener("pointerup", handlePointerUp);
  canvas.addEventListener("pointercancel", handlePointerUp);
}

let lastTime = performance.now();
let lastFrameWallTime = lastTime;
let domAccumulator = 0;
let fallbackFrameTimer = null;

function runFrame(now) {
  const dt = Math.min(0.05, (now - lastTime) / 1000);
  lastTime = now;
  lastFrameWallTime = now;
  stepSimulation(dt);
  updateRuntimeDebugAttributes();
  render();
  domAccumulator += dt;
  if (domAccumulator > 0.18) {
    updateDom();
    domAccumulator = 0;
  }
}

function frame(now) {
  runFrame(now);
  requestAnimationFrame(frame);
}

async function init() {
  scaleDesignSurface();
  applyModuleLabels();
  bindEvents();
  resizeCanvas();
  loadSpriteAssets().then(() => render());
  loadSkillStats();
  await loadRuntimeProfile(state.load);
  setFocusedSkill("shelf_pick");
  updateDom();
  updateRuntimeDebugAttributes();
  render();
  if (!fallbackFrameTimer) {
    fallbackFrameTimer = setInterval(() => {
      const now = performance.now();
      if (now - lastFrameWallTime > 160) runFrame(now);
    }, 80);
  }
  requestAnimationFrame(frame);
}

window.__warehouseRuntimeDebug = () => ({
  runtimeLinked: state.runtimeLinked,
  runtimeEventCount: state.runtimeEvents.length,
  runtimeEventIndex: state.runtimeEventIndex,
  runtimeReplayTick: Number((state.runtimeReplayTick || 0).toFixed(2)),
  runtimeLockCount: currentRuntimeLockTileIds().size,
  humanIntrusionEnabled: state.humanIntrusionEnabled,
  humanActiveCount: activeHumanAgents().length,
  humanRiskTiles: currentHumanRiskTileIds().size,
  load: state.load,
  speed: state.speed,
  tick: Math.floor(state.tick),
  blockedTileCount: state.runtimeBlockedTiles?.size || 0,
  occupiedTileCount: state.runtimeOccupiedTiles?.size || 0,
  dropTiles: state.runtimeSnapshot?.warehouse?.drop_tiles || [],
  conveyors: state.runtimeSnapshot?.warehouse?.conveyors || [],
  robots: state.robots.map((robot) => ({
    id: robot.id,
    status: robot.runtimeStatus || robot.status || robotStatus(robot),
    normalizedStatus: robotStatus(robot),
    tileId: robot.tileId,
    nextTileId: robot.nextTileId,
    visualTileId: robot.visualTileId,
    routeClosed: robot.routeClosed === true,
    motion: robot.motion ? {
      sourceTileId: robot.motion.sourceTileId,
      destinationTileId: robot.motion.destinationTileId,
      progress: Number(robot.motion.progress.toFixed(3)),
      done: Boolean(robot.motion.done),
    } : null,
    visualPose: robot.visualPose ? {
      x: Number(robot.visualPose.x.toFixed(3)),
      y: Number(robot.visualPose.y.toFixed(3)),
      direction: robot.visualPose.direction,
    } : null,
  })),
});

init();

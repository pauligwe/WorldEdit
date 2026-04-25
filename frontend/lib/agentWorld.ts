"use client";

import type { StatusEvent } from "./api";

export type BuildMode = "real" | "simulated";
export type AgentVisualState = "idle" | "walking" | "working" | "chatting" | "done" | "error";

export interface AgentMeta {
  key: string;
  name: string;
  description: string;
  phase: "sequential-prefix" | "parallel-middle" | "post-processing";
  station: [number, number, number];
}

export interface AgentWorldEvent {
  id: string;
  ts: number;
  simulated: boolean;
  event: StatusEvent;
}

export interface AgentWorldSnapshot {
  key: string;
  name: string;
  description: string;
  phase: AgentMeta["phase"];
  station: [number, number, number];
  status: "idle" | "running" | "done" | "error";
  visualState: AgentVisualState;
  activityLabel: string;
  stateText: string;
  progress?: number;
  lastUpdateAt?: number;
  message?: string;
  error?: string;
  metadata?: Record<string, unknown>;
  recentEvents: AgentWorldEvent[];
}

const AGENT_META: AgentMeta[] = [
  {
    key: "intent_parser",
    name: "Intent Parser",
    description: "Turns the natural language prompt into structured world intent.",
    phase: "sequential-prefix",
    station: [-8, 0.45, -6],
  },
  {
    key: "blueprint_architect",
    name: "Blueprint Architect",
    description: "Designs room layout, floor boundaries, and circulation.",
    phase: "sequential-prefix",
    station: [-5.4, 0.45, -6],
  },
  {
    key: "compliance_critic",
    name: "Compliance Critic",
    description: "Checks blueprint consistency and structural plausibility.",
    phase: "sequential-prefix",
    station: [-2.8, 0.45, -6],
  },
  {
    key: "geometry_builder",
    name: "Geometry Builder",
    description: "Builds geometry primitives from the validated blueprint.",
    phase: "parallel-middle",
    station: [-4.2, 0.45, -1.3],
  },
  {
    key: "lighting_designer",
    name: "Lighting Designer",
    description: "Plans room lighting and ambience choices.",
    phase: "parallel-middle",
    station: [-1.5, 0.45, -1.3],
  },
  {
    key: "material_stylist",
    name: "Material Stylist",
    description: "Chooses wall, floor, and ceiling material palettes.",
    phase: "parallel-middle",
    station: [1.2, 0.45, -1.3],
  },
  {
    key: "furniture_planner",
    name: "Furniture Planner",
    description: "Plans furniture types, placement intents, and sizing.",
    phase: "post-processing",
    station: [-4.8, 0.45, 3.6],
  },
  {
    key: "placement_validator",
    name: "Placement Validator",
    description: "Checks collision and placement validity for furniture.",
    phase: "post-processing",
    station: [-2.1, 0.45, 3.6],
  },
  {
    key: "product_scout",
    name: "Product Scout",
    description: "Finds product alternates for generated furniture items.",
    phase: "post-processing",
    station: [0.6, 0.45, 3.6],
  },
  {
    key: "style_matcher",
    name: "Style Matcher",
    description: "Aligns furniture options with the desired room style.",
    phase: "post-processing",
    station: [3.2, 0.45, 3.6],
  },
  {
    key: "pricing_estimator",
    name: "Pricing Estimator",
    description: "Computes per-room and total cost estimates.",
    phase: "post-processing",
    station: [5.8, 0.45, 3.6],
  },
  {
    key: "navigation_planner",
    name: "Navigation Planner",
    description: "Creates spawn and walkable navigation metadata.",
    phase: "post-processing",
    station: [8.3, 0.45, 3.6],
  },
];

export const AGENT_ORDER = AGENT_META.map((a) => a.key);

export function getAgentMeta(key: string): AgentMeta | undefined {
  return AGENT_META.find((agent) => agent.key === key);
}

export function getAllAgentMeta(): AgentMeta[] {
  return AGENT_META;
}

export function createInitialAgentSnapshots(): Record<string, AgentWorldSnapshot> {
  const entries = AGENT_META.map((agent) => [
    agent.key,
    {
      key: agent.key,
      name: agent.name,
      description: agent.description,
      phase: agent.phase,
      station: agent.station,
      status: "idle" as const,
      visualState: "idle" as const,
      activityLabel: "Waiting for turn",
      stateText: "idle",
      recentEvents: [],
    },
  ]);
  return Object.fromEntries(entries);
}

export function normalizeStatusEvent(evt: StatusEvent): StatusEvent {
  return {
    agent: evt.agent,
    state: evt.state,
    message: evt.message ?? "",
    data: evt.data ?? {},
  };
}

export function applyAgentWorldEvent(
  snapshots: Record<string, AgentWorldSnapshot>,
  events: AgentWorldEvent[],
  evt: StatusEvent,
  simulated: boolean,
): { snapshots: Record<string, AgentWorldSnapshot>; events: AgentWorldEvent[] } {
  const event = normalizeStatusEvent(evt);
  const meta = getAgentMeta(event.agent);
  if (!meta) return { snapshots, events };

  const next = { ...snapshots };
  const current = next[event.agent] ?? createInitialAgentSnapshots()[event.agent];
  const ts = Date.now();
  const eventWithMeta: AgentWorldEvent = {
    id: `${event.agent}-${ts}-${events.length}`,
    ts,
    simulated,
    event,
  };
  const recentEvents = [eventWithMeta, ...current.recentEvents].slice(0, 8);

  let visualState: AgentVisualState = current.visualState;
  let activityLabel = current.activityLabel;
  let stateText = event.state;
  let progress = current.progress;
  let error = current.error;

  if (event.state === "running") {
    visualState = meta.phase === "parallel-middle" ? "chatting" : "working";
    activityLabel = runningLabel(meta.key);
    progress = deriveProgress(event, meta.key);
    error = undefined;
  } else if (event.state === "done") {
    visualState = "done";
    activityLabel = "Finished step";
    progress = 100;
    error = undefined;
    stateText = "done";
  } else if (event.state === "error") {
    visualState = "error";
    activityLabel = "Needs attention";
    stateText = "error";
    error = event.message || "Unknown error";
  }

  next[event.agent] = {
    ...current,
    status: event.state,
    visualState,
    activityLabel,
    stateText: event.message || stateText,
    progress,
    error,
    message: event.message,
    metadata: event.data ?? {},
    lastUpdateAt: ts,
    recentEvents,
  };

  return { snapshots: next, events: [...events, eventWithMeta].slice(-160) };
}

function runningLabel(key: string): string {
  switch (key) {
    case "intent_parser":
      return "Interpreting prompt intent";
    case "blueprint_architect":
      return "Drafting room blueprint";
    case "compliance_critic":
      return "Reviewing layout constraints";
    case "geometry_builder":
      return "Constructing geometry primitives";
    case "lighting_designer":
      return "Balancing light ambiance";
    case "material_stylist":
      return "Styling material palette";
    case "furniture_planner":
      return "Placing furniture candidates";
    case "placement_validator":
      return "Checking spacing and collisions";
    case "product_scout":
      return "Searching product alternates";
    case "style_matcher":
      return "Matching style signatures";
    case "pricing_estimator":
      return "Calculating cost totals";
    case "navigation_planner":
      return "Planning navigation spawn";
    default:
      return "Working";
  }
}

function deriveProgress(evt: StatusEvent, key: string): number {
  const fromData = Number(evt.data?.progress);
  if (!Number.isNaN(fromData) && fromData >= 0 && fromData <= 100) return fromData;
  const idx = AGENT_ORDER.indexOf(key);
  if (idx < 0) return 0;
  const base = (idx / AGENT_ORDER.length) * 100;
  return Math.min(95, Math.round(base + 8));
}

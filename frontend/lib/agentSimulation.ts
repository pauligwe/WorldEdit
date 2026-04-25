"use client";

import type { StatusEvent } from "./api";
import { AGENT_ORDER } from "./agentWorld";

type EventScheduleItem = {
  waitMs: number;
  event: StatusEvent;
};

export function startAgentSimulation(
  onEvent: (evt: StatusEvent) => void,
  onComplete?: () => void,
): () => void {
  const scheduled = buildSimulationSchedule();
  const timers: number[] = [];
  let elapsed = 0;

  for (const item of scheduled) {
    elapsed += item.waitMs;
    const timer = window.setTimeout(() => onEvent(item.event), elapsed);
    timers.push(timer);
  }

  const doneTimer = window.setTimeout(() => onComplete?.(), elapsed + 200);
  timers.push(doneTimer);

  return () => {
    for (const id of timers) window.clearTimeout(id);
  };
}

function buildSimulationSchedule(): EventScheduleItem[] {
  const events: EventScheduleItem[] = [];

  const prefix = ["intent_parser", "blueprint_architect", "compliance_critic"];
  for (const key of prefix) {
    events.push(stepStart(key, 500));
    events.push(stepDone(key, 1200));
  }

  const parallel = ["geometry_builder", "lighting_designer", "material_stylist"];
  for (const key of parallel) events.push(stepStart(key, 350));
  for (const key of parallel) events.push(stepDone(key, 1650));

  const suffix = AGENT_ORDER.filter((a) => !prefix.includes(a) && !parallel.includes(a));
  for (const key of suffix) {
    events.push(stepStart(key, 420));
    events.push(stepDone(key, 980));
  }

  events.push({
    waitMs: 300,
    event: {
      agent: "__final__",
      state: "done",
      message: "Simulation complete",
      data: { simulated: true },
    },
  });

  return events;
}

function stepStart(agent: string, waitMs: number): EventScheduleItem {
  return {
    waitMs,
    event: {
      agent,
      state: "running",
      message: `Simulating ${human(agent)}`,
      data: { simulated: true, progress: 15 },
    },
  };
}

function stepDone(agent: string, waitMs: number): EventScheduleItem {
  return {
    waitMs,
    event: {
      agent,
      state: "done",
      message: `${human(agent)} complete`,
      data: { simulated: true, progress: 100 },
    },
  };
}

function human(agent: string): string {
  return agent.split("_").join(" ");
}

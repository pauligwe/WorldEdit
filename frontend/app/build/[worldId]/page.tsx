"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useParams, useSearchParams } from "next/navigation";
import { openStatusSocket, getWorld, type StatusEvent } from "@/lib/api";
import type { WorldSpec } from "@/lib/worldSpec";
import { applyAgentWorldEvent, createInitialAgentSnapshots, type BuildMode, type AgentWorldEvent, type AgentWorldSnapshot } from "@/lib/agentWorld";
import { startAgentSimulation } from "@/lib/agentSimulation";

const World3D = dynamic(() => import("@/components/World3D"), { ssr: false });

export default function BuildPage() {
  const params = useParams<{ worldId: string }>();
  const searchParams = useSearchParams();
  const autoSimulate = searchParams.get("simulate") === "1";
  const worldId = params.worldId;
  const [mode, setMode] = useState<BuildMode>(autoSimulate ? "simulated" : "real");
  const [agentSnapshots, setAgentSnapshots] = useState<Record<string, AgentWorldSnapshot>>(createInitialAgentSnapshots());
  const [agentEvents, setAgentEvents] = useState<AgentWorldEvent[]>([]);
  const [spec, setSpec] = useState<WorldSpec | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [simRunning, setSimRunning] = useState(false);
  const simStopRef = useRef<(() => void) | null>(null);
  const eventsRef = useRef<AgentWorldEvent[]>([]);
  const autoStartedSimRef = useRef(false);

  const onAgentEvent = useCallback((event: StatusEvent, simulated: boolean) => {
    if (event.agent === "__final__") {
      if (simulated) {
        setSimRunning(false);
        return;
      }
      getWorld(worldId).then(setSpec).catch(() => {});
      return;
    }
    if (event.agent === "__pipeline__" && event.state === "error") {
      setError(event.message ?? "Pipeline error");
      return;
    }
    if (event.agent.startsWith("__")) return;

    setAgentSnapshots((prev) => {
      const next = applyAgentWorldEvent(prev, eventsRef.current, event, simulated);
      eventsRef.current = next.events;
      setAgentEvents(next.events);
      return next.snapshots;
    });
  }, [worldId]);

  useEffect(() => {
    setAgentSnapshots(createInitialAgentSnapshots());
    setAgentEvents([]);
    eventsRef.current = [];
    setSpec(null);
    setError(null);
    simStopRef.current?.();
    simStopRef.current = null;
    setSimRunning(false);
    setMode(autoSimulate ? "simulated" : "real");
    autoStartedSimRef.current = false;
  }, [worldId, autoSimulate]);

  useEffect(() => {
    if (mode !== "real") return;
    let cancelled = false;
    let close: (() => void) | null = null;
    (async () => {
      try {
        const existing = await getWorld(worldId);
        if (cancelled) return;
        if (existing && existing.cost && existing.navigation) {
          setSpec(existing);
          return;
        }
      } catch {}
      if (cancelled) return;
      close = openStatusSocket(worldId, async (e) => {
        onAgentEvent(e, false);
      });
    })();
    return () => { cancelled = true; close?.(); };
  }, [worldId, mode, onAgentEvent]);

  useEffect(() => {
    return () => simStopRef.current?.();
  }, []);

  const startSimulation = useCallback(() => {
    simStopRef.current?.();
    setMode("simulated");
    setError(null);
    setAgentSnapshots(createInitialAgentSnapshots());
    setAgentEvents([]);
    eventsRef.current = [];
    setSimRunning(true);
    simStopRef.current = startAgentSimulation((evt) => onAgentEvent(evt, true), () => setSimRunning(false));
  }, [onAgentEvent]);

  const exitSimulation = useCallback(() => {
    simStopRef.current?.();
    simStopRef.current = null;
    setSimRunning(false);
    setMode("real");
    setAgentSnapshots(createInitialAgentSnapshots());
    setAgentEvents([]);
    eventsRef.current = [];
  }, []);

  useEffect(() => {
    if (!autoSimulate || autoStartedSimRef.current) return;
    autoStartedSimRef.current = true;
    startSimulation();
  }, [autoSimulate, startSimulation]);

  if (error) {
    return (
      <main className="min-h-screen bg-black text-red-300 flex flex-col items-center justify-center p-8">
        <h1 className="text-2xl font-bold mb-2">Generation failed</h1>
        <pre className="text-sm whitespace-pre-wrap">{error}</pre>
      </main>
    );
  }

  const renderSpec = spec ?? simulationFallbackSpec(worldId);

  return (
    <World3D
      spec={renderSpec}
      mode={mode}
      simRunning={simRunning}
      onStartSimulation={startSimulation}
      onExitSimulation={exitSimulation}
      agentSnapshots={agentSnapshots}
      agentEvents={agentEvents}
    />
  );
}

function simulationFallbackSpec(worldId: string): WorldSpec {
  return {
    worldId,
    prompt: "Simulation world",
    intent: { buildingType: "demo_lab", style: "playful", floors: 1, vibe: ["lively", "observability"], sizeHint: "medium" },
    geometry: {
      primitives: [
        { type: "floor", roomId: "sim_hub", position: [0, 0, 0], size: [22, 0.2, 14] },
        { type: "wall", roomId: "sim_hub", position: [0, 1.5, -7], size: [22, 3, 0.2] },
        { type: "wall", roomId: "sim_hub", position: [0, 1.5, 7], size: [22, 3, 0.2] },
        { type: "wall", roomId: "sim_hub", position: [-11, 1.5, 0], size: [0.2, 3, 14] },
        { type: "wall", roomId: "sim_hub", position: [11, 1.5, 0], size: [0.2, 3, 14] },
      ],
    },
    materials: { byRoom: { sim_hub: { wall: "#262f3a", floor: "concrete", ceiling: "#303640" } } },
    lighting: {
      byRoom: {
        sim_hub: [
          { type: "ambient", position: [0, 2.8, 0], color: "#b6e6ff", intensity: 0.45 },
          { type: "ceiling", position: [-4, 2.5, -2], color: "#e7f2ff", intensity: 0.55 },
          { type: "ceiling", position: [3, 2.5, 2], color: "#ffe3bc", intensity: 0.5 },
        ],
      },
    },
    furniture: [],
    products: {},
    navigation: { spawnPoint: [0, 1.7, 4], walkableMeshIds: [], stairColliders: [] },
    cost: { total: 0, byRoom: {} },
  };
}

"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import type { WorldSpec } from "@/lib/worldSpec";
import type { AgentWorldEvent, AgentWorldSnapshot, BuildMode } from "@/lib/agentWorld";
import { expandWallSegments } from "@/lib/wallSegments";
import Plot from "./Plot";
import Roof from "./Roof";
import Wall from "./Wall";
import FurnitureInstanced from "./FurnitureInstanced";
import PlayerControls from "./PlayerControls";
import CrosshairHUD from "./CrosshairHUD";
import StatusBar from "./StatusBar";
import ChatPanel from "./ChatPanel";
import AgentWorldOverlay from "./AgentWorldOverlay";
import AgentDetailPanel from "./AgentDetailPanel";

const MAX_POINT_LIGHTS = 4;

export default function World3D({
  spec,
  mode,
  simRunning,
  onStartSimulation,
  onExitSimulation,
  agentSnapshots,
  agentEvents,
}: {
  spec: WorldSpec;
  mode: BuildMode;
  simRunning: boolean;
  onStartSimulation: () => void;
  onExitSimulation: () => void;
  agentSnapshots: Record<string, AgentWorldSnapshot>;
  agentEvents: AgentWorldEvent[];
}) {
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [hoveredAgentKey, setHoveredAgentKey] = useState<string | null>(null);
  const [hoverPos, setHoverPos] = useState<{ x: number; y: number } | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code === "KeyT") setChatOpen((v) => !v);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const prims = spec.geometry?.primitives ?? [];

  const partitioned = useMemo(() => ({
    ground:   prims.filter((p) => p.type === "ground"),
    exterior: prims.filter((p) => p.type === "exterior_wall"),
    roof:     prims.filter((p) => p.type === "roof"),
    walls:    prims.filter((p) => p.type === "wall"),
    floors:   prims.filter((p) => p.type === "floor"),
    ceilings: prims.filter((p) => p.type === "ceiling"),
    stairs:   prims.filter((p) => p.type === "stair"),
  }), [prims]);

  const { ground, exterior, roof, walls, floors, ceilings, stairs } = partitioned;

  const colliders = useMemo(() => [
    ...exterior.flatMap(expandWallSegments),
    ...walls.flatMap(expandWallSegments),
  ], [exterior, walls]);

  const pickedLights = useMemo(() => {
    const all = Object.entries(spec.lighting?.byRoom ?? {}).flatMap(([rid, lights]) =>
      lights.map((l, i) => ({ rid, i, l }))
    );
    return all.slice(0, MAX_POINT_LIGHTS);
  }, [spec.lighting]);

  const matFloor = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.floor;
  const matWall  = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.wall ?? "#e7e1d5";
  const matCeil  = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.ceiling ?? "#ffffff";

  const spawn = spec.navigation?.spawnPoint ?? [50, 1.7, -47];
  const groundColor = spec.site?.plot?.groundColor ?? "#5a7c3a";
  const selectedAgent = selectedAgentKey ? agentSnapshots[selectedAgentKey] : null;
  const hoveredAgent = hoveredAgentKey ? agentSnapshots[hoveredAgentKey] : null;

  return (
    <div className="fixed inset-0">
      <Canvas camera={{ fov: 70, position: spawn as any, near: 0.05, far: 300 }}>
        <color attach="background" args={["#a8c8e8"]} />
        <ambientLight intensity={0.9} />
        <directionalLight position={[60, 80, 40]} intensity={1.0} />

        {pickedLights.map(({ rid, i, l }) => (
          <pointLight key={`${rid}-${i}`} position={l.position as any}
                      color={l.color} intensity={l.intensity} distance={12} />
        ))}

        <Suspense fallback={null}>
          {ground.map((p, i) => (
            <Plot key={`g${i}`} size={[p.size[0], p.size[2]]} color={groundColor} />
          ))}
          {floors.map((p, i) => (
            <mesh key={`f${i}`} position={p.position as any}>
              <boxGeometry args={p.size as any} />
              <meshLambertMaterial color={floorColor(matFloor(p.roomId))} />
            </mesh>
          ))}
          {ceilings.map((p, i) => (
            <mesh key={`c${i}`} position={p.position as any}>
              <boxGeometry args={p.size as any} />
              <meshLambertMaterial color={matCeil(p.roomId)} />
            </mesh>
          ))}
          {walls.map((p, i)    => <Wall key={`w${i}`} prim={p} color={matWall(p.roomId)} />)}
          {exterior.map((p, i) => <Wall key={`e${i}`} prim={p} color="#d8d4c6" />)}
          {roof.map((p, i)     => <Roof key={`r${i}`} prim={p} color="#3a3a3a" />)}
          {stairs.map((p, i) => (
            <mesh key={`s${i}`} position={p.position as any}
                  rotation={[0, p.rotation ?? 0, 0]}>
              <boxGeometry args={[p.size[0], 0.2, p.size[2]]} />
              <meshLambertMaterial color="#7c5a3a" />
            </mesh>
          ))}
          <FurnitureInstanced items={spec.furniture} />

          <AgentWorldOverlay
            snapshots={agentSnapshots}
            events={agentEvents}
            selectedAgentKey={selectedAgentKey}
            onSelect={(key) => {
              setSelectedAgentKey(key);
            }}
            onHover={(hover) => {
              if (!hover) {
                setHoveredAgentKey(null);
                setHoverPos(null);
                return;
              }
              setHoveredAgentKey(hover.agentKey);
              setHoverPos({ x: hover.x, y: hover.y });
            }}
          />
        </Suspense>

        <PlayerControls walls={colliders} spawn={spawn as any} />
      </Canvas>

      <CrosshairHUD />
      <StatusBar
        spec={spec}
        mode={mode}
        simRunning={simRunning}
        onStartSimulation={onStartSimulation}
        onExitSimulation={onExitSimulation}
      />

      {mode === "simulated" && (
        <div className="fixed left-1/2 top-4 z-20 -translate-x-1/2 rounded border border-violet-500 bg-violet-950/90 px-4 py-2 text-sm font-semibold text-violet-100">
          Simulated preview · no backend generation is running
        </div>
      )}

      {hoveredAgent && hoverPos && (
        <div
          className="pointer-events-none fixed z-30 w-64 rounded border border-zinc-700 bg-zinc-950/95 p-2 text-xs text-zinc-200 shadow-xl"
          style={{ left: hoverPos.x + 12, top: hoverPos.y + 12 }}
        >
          <div className="font-semibold text-cyan-300">{hoveredAgent.name}</div>
          <div className="text-zinc-300">{hoveredAgent.activityLabel}</div>
          <div className="text-zinc-400">{hoveredAgent.stateText}</div>
          <div className="text-zinc-500">
            {hoveredAgent.progress !== undefined ? `Progress ${hoveredAgent.progress}%` : "Progress unavailable"}
          </div>
        </div>
      )}

      {selectedAgent && (
        <AgentDetailPanel snapshot={selectedAgent} onClose={() => setSelectedAgentKey(null)} />
      )}

      {agentEvents.length > 0 && (
        <div className="fixed left-4 top-4 z-20 max-h-48 w-[min(420px,calc(100vw-2rem))] overflow-y-auto rounded border border-zinc-800 bg-black/70 p-3 text-xs text-zinc-300">
          <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-400">Agent Activity Feed</div>
          <div className="space-y-1">
            {agentEvents.slice(-6).reverse().map((evt) => (
              <div key={evt.id} className="rounded border border-zinc-800 px-2 py-1">
                <span className="text-zinc-500">{new Date(evt.ts).toLocaleTimeString()} </span>
                <span className="text-cyan-300">{evt.event.agent}</span>
                <span className="mx-1 text-zinc-500">·</span>
                <span>{evt.event.message || evt.event.state}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} worldId={spec.worldId} />
    </div>
  );
}

function floorColor(token?: string): string {
  const map: Record<string, string> = {
    oak_planks: "#a47a4f",
    marble_tile: "#e9e6df",
    concrete: "#9a9a9a",
    carpet_grey: "#7d7d7d",
    carpet_beige: "#c8b89c",
    tile_white: "#f1efe7",
    dark_wood: "#4b2e1a",
  };
  return map[token ?? ""] ?? "#9b8466";
}

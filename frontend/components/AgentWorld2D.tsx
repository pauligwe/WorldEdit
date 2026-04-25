"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { WorldSpec } from "@/lib/worldSpec";
import type { AgentWorldEvent, AgentWorldSnapshot } from "@/lib/agentWorld";
import Plot from "./Plot";
import FurnitureInstanced from "./FurnitureInstanced";
import AgentWorldOverlay from "./AgentWorldOverlay";
import AgentDetailPanel from "./AgentDetailPanel";

export default function AgentWorld2D({
  spec,
  agentSnapshots,
  agentEvents,
}: {
  spec: WorldSpec;
  agentSnapshots: Record<string, AgentWorldSnapshot>;
  agentEvents: AgentWorldEvent[];
}) {
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [hoveredAgentKey, setHoveredAgentKey] = useState<string | null>(null);
  const [hoverPos, setHoverPos] = useState<{ x: number; y: number } | null>(null);

  const prims = useMemo(() => spec.geometry?.primitives ?? [], [spec.geometry?.primitives]);
  const ground = useMemo(() => prims.filter((p) => p.type === "ground"), [prims]);
  const selectedAgent = selectedAgentKey ? agentSnapshots[selectedAgentKey] : null;
  const hoveredAgent = hoveredAgentKey ? agentSnapshots[hoveredAgentKey] : null;

  const cameraSetup = useMemo(() => {
    const fw = spec.site?.buildingFootprint?.[0];
    const fd = spec.site?.buildingFootprint?.[1];
    const ax = spec.site?.buildingAnchor?.[0];
    const ay = spec.site?.buildingAnchor?.[1];

    if (fw !== undefined && fd !== undefined && ax !== undefined && ay !== undefined) {
      const centerX = ax + fw / 2;
      const centerYP = ay + fd / 2;
      const maxDim = Math.max(fw, fd);
      return {
        target: [centerX, 0, -centerYP] as [number, number, number],
        position: [centerX, 120, -centerYP] as [number, number, number],
        zoom: Math.max(14, Math.min(54, 860 / (maxDim + 4))),
      };
    }

    return {
      target: [0, 0, 0] as [number, number, number],
      position: [0, 120, 0] as [number, number, number],
      zoom: 24,
    };
  }, [spec.site]);

  const matFloor = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.floor;
  const groundColor = spec.site?.plot?.groundColor ?? "#5a7c3a";

  return (
    <div className="fixed inset-0">
      <Canvas orthographic camera={{ zoom: cameraSetup.zoom, position: cameraSetup.position as any, near: 0.01, far: 600 }}>
        <TopDownCamera target={cameraSetup.target} />
        <color attach="background" args={["#ede1c8"]} />
        <Suspense fallback={null}>
          {ground.map((p, i) => (
            <Plot key={`g${i}`} size={[p.size[0], p.size[2]]} color={groundColor} />
          ))}
          <mesh position={[0, 0.014, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[26, 18]} />
            <meshBasicMaterial color={floorColor(matFloor())} opacity={0.24} transparent />
          </mesh>
          <FurnitureInstanced items={spec.furniture} />
          <AgentWorldOverlay
            snapshots={agentSnapshots}
            events={agentEvents}
            selectedAgentKey={selectedAgentKey}
            onSelect={(key) => setSelectedAgentKey(key)}
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
        <OrbitControls
          target={cameraSetup.target as any}
          enablePan
          enableZoom
          enableRotate={false}
          minZoom={12}
          maxZoom={72}
          screenSpacePanning
        />
      </Canvas>

      <div className="fixed left-1/2 top-4 z-20 -translate-x-1/2 rounded border border-cyan-500 bg-zinc-950/90 px-4 py-2 text-sm font-semibold text-cyan-100">
        Agents are building your world...
      </div>

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

      {selectedAgent && <AgentDetailPanel snapshot={selectedAgent} onClose={() => setSelectedAgentKey(null)} />}

      {agentEvents.length > 0 && (
        <div className="fixed left-4 top-4 z-20 max-h-48 w-[min(420px,calc(100vw-2rem))] overflow-y-auto rounded border border-zinc-800 bg-black/70 p-3 text-xs text-zinc-300">
          <div className="mb-2 text-[11px] uppercase tracking-wide text-zinc-400">Agent Activity Feed</div>
          <div className="space-y-1">
            {agentEvents.slice(-6).reverse().map((evt) => (
              <div key={evt.id} className="rounded border border-zinc-800 px-2 py-1">
                <span className="text-zinc-500">{new Date(evt.ts).toLocaleTimeString()} </span>
                <span className="text-cyan-300">{evt.event.agent}</span>
                <span className="mx-1 text-zinc-500">-</span>
                <span>{evt.event.message || evt.event.state}</span>
              </div>
            ))}
          </div>
        </div>
      )}
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

function TopDownCamera({ target }: { target: [number, number, number] }) {
  const { camera } = useThree();

  useEffect(() => {
    camera.up.set(0, 0, -1);
    camera.lookAt(target[0], target[1], target[2]);
  }, [camera, target]);

  return null;
}

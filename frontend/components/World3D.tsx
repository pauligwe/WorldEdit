"use client";
import { Suspense, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useThree } from "@react-three/fiber";
import type { WorldSpec, FurnitureItem } from "@/lib/worldSpec";
import { fetchProductColor } from "@/lib/api";
import type { AgentWorldEvent, AgentWorldSnapshot, BuildMode } from "@/lib/agentWorld";
import Wall from "./Wall";
import Furniture from "./Furniture";
import FurniturePanel from "./FurniturePanel";
import StatusBar from "./StatusBar";
import ChatPanel from "./ChatPanel";
import AgentWorldOverlay from "./AgentWorldOverlay";
import AgentDetailPanel from "./AgentDetailPanel";

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
  const [selected, setSelected] = useState<FurnitureItem | null>(null);
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [hoveredAgentKey, setHoveredAgentKey] = useState<string | null>(null);
  const [hoverPos, setHoverPos] = useState<{ x: number; y: number } | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [productColors, setProductColors] = useState<Record<string, string>>({});

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code === "KeyT") setChatOpen((v) => !v);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ids = spec.furniture
        .map((f) => f.selectedProductId)
        .filter((id): id is string => !!id && !productColors[id]);
      const unique = Array.from(new Set(ids));
      await Promise.all(unique.map(async (id) => {
        const p = spec.products[id];
        if (!p?.imageUrl) return;
        const color = await fetchProductColor(p.imageUrl, p.url);
        if (!cancelled && color) {
          setProductColors((prev) => ({ ...prev, [id]: color }));
        }
      }));
    })();
    return () => { cancelled = true; };
  }, [spec, productColors]);

  const prims = spec.geometry?.primitives ?? [];
  const walls = prims.filter((p) => p.type === "wall");
  const floors = prims.filter((p) => p.type === "floor");
  const ceilings = prims.filter((p) => p.type === "ceiling");
  const stairs = prims.filter((p) => p.type === "stair");

  const matFloor = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.floor;
  const matWall = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.wall ?? "#e7e1d5";
  const matCeil = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.ceiling ?? "#ffffff";

  const cameraPosition = [0, 16, 6] as [number, number, number];
  const selectedAgent = selectedAgentKey ? agentSnapshots[selectedAgentKey] : null;
  const hoveredAgent = hoveredAgentKey ? agentSnapshots[hoveredAgentKey] : null;

  return (
    <div className="fixed inset-0 bg-black">
      <Canvas camera={{ fov: 52, position: cameraPosition as any, near: 0.05, far: 240 }} shadows={false}>
        <SceneCamera />
        <ambientLight intensity={0.5} />
        <directionalLight position={[20, 30, 20]} intensity={0.6} />

        {Object.entries(spec.lighting?.byRoom ?? {}).flatMap(([rid, lights]) =>
          lights.map((l, i) => (
            <pointLight key={`${rid}-${i}`} position={l.position as any} color={l.color} intensity={l.intensity} distance={12} />
          ))
        )}

        <Suspense fallback={null}>
          {floors.map((p, i) => (
            <mesh key={`f${i}`} position={p.position as any}>
              <boxGeometry args={p.size as any} />
              <meshStandardMaterial color={floorColor(matFloor(p.roomId))} />
            </mesh>
          ))}
          {ceilings.map((p, i) => (
            <mesh key={`c${i}`} position={p.position as any}>
              <boxGeometry args={p.size as any} />
              <meshStandardMaterial color={matCeil(p.roomId)} />
            </mesh>
          ))}
          {walls.map((p, i) => (
            <Wall key={`w${i}`} prim={p} color={matWall(p.roomId)} />
          ))}
          {stairs.map((p, i) => (
            <mesh key={`s${i}`} position={p.position as any} rotation={[0, p.rotation ?? 0, 0]}>
              <boxGeometry args={[p.size[0], 0.2, p.size[2]]} />
              <meshStandardMaterial color="#7c5a3a" />
            </mesh>
          ))}
          {spec.furniture.map((f) => {
            const fetched = f.selectedProductId ? productColors[f.selectedProductId] : undefined;
            const tint = fetched ?? tintForProduct(spec, f);
            return (
              <Furniture
                key={f.id}
                item={f}
                tint={tint}
                onClick={() => {
                  setSelectedAgentKey(null);
                  setSelected(f);
                }}
              />
            );
          })}

          <AgentWorldOverlay
            snapshots={agentSnapshots}
            events={agentEvents}
            selectedAgentKey={selectedAgentKey}
            onSelect={(key) => {
              setSelected(null);
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

        <OrbitControls
          enablePan
          enableRotate={false}
          enableZoom
          minDistance={8}
          maxDistance={30}
          minPolarAngle={0.1}
          maxPolarAngle={Math.PI / 2.1}
          target={[0, 0, 0]}
        />
      </Canvas>

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

      {selected && (
        <FurniturePanel
          spec={spec}
          item={selected}
          onClose={() => setSelected(null)}
        />
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

function SceneCamera() {
  const { camera } = useThree();

  useEffect(() => {
    camera.position.set(0, 16, 6);
    camera.lookAt(0, 0, 0);
  }, [camera]);

  return null;
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

function tintForProduct(spec: WorldSpec, f: FurnitureItem): string | undefined {
  if (!f.selectedProductId) return undefined;
  const p = spec.products[f.selectedProductId];
  if (!p) return undefined;
  let h = 0; for (const c of p.name) h = (h * 31 + c.charCodeAt(0)) | 0;
  const hue = Math.abs(h) % 360;
  return `hsl(${hue}, 30%, 55%)`;
}

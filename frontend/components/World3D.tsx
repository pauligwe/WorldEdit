"use client";
import { Suspense, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import type { WorldSpec, FurnitureItem } from "@/lib/worldSpec";
import Wall from "./Wall";
import Furniture from "./Furniture";
import PlayerControls from "./PlayerControls";
import CrosshairHUD from "./CrosshairHUD";
import FurniturePanel from "./FurniturePanel";
import StatusBar from "./StatusBar";
import ChatPanel from "./ChatPanel";

export default function World3D({ spec }: { spec: WorldSpec }) {
  const [selected, setSelected] = useState<FurnitureItem | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code === "KeyT") setChatOpen((v) => !v);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const prims = spec.geometry?.primitives ?? [];
  const walls = prims.filter((p) => p.type === "wall");
  const floors = prims.filter((p) => p.type === "floor");
  const ceilings = prims.filter((p) => p.type === "ceiling");
  const stairs = prims.filter((p) => p.type === "stair");

  const matFloor = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.floor;
  const matWall = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.wall ?? "#e7e1d5";
  const matCeil = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.ceiling ?? "#ffffff";

  const spawn = spec.navigation?.spawnPoint ?? [0, 1.7, 0];

  return (
    <div className="fixed inset-0 bg-black">
      <Canvas camera={{ fov: 70, position: spawn as any, near: 0.05, far: 200 }} shadows={false}>
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
            const tint = tintForProduct(spec, f);
            return (
              <Furniture
                key={f.id}
                item={f}
                tint={tint}
                onClick={() => setSelected(f)}
              />
            );
          })}
        </Suspense>

        <PlayerControls walls={walls} spawn={spawn as any} />
      </Canvas>

      <CrosshairHUD />
      <StatusBar spec={spec} />

      {selected && (
        <FurniturePanel
          spec={spec}
          item={selected}
          onClose={() => setSelected(null)}
        />
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

function tintForProduct(spec: WorldSpec, f: FurnitureItem): string | undefined {
  if (!f.selectedProductId) return undefined;
  const p = spec.products[f.selectedProductId];
  if (!p) return undefined;
  let h = 0; for (const c of p.name) h = (h * 31 + c.charCodeAt(0)) | 0;
  const hue = Math.abs(h) % 360;
  return `hsl(${hue}, 30%, 55%)`;
}

"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import type { WorldSpec } from "@/lib/worldSpec";
import { expandWallSegments } from "@/lib/wallSegments";
import Plot from "./Plot";
import Roof from "./Roof";
import Wall from "./Wall";
import FurnitureInstanced from "./FurnitureInstanced";
import PlayerControls from "./PlayerControls";
import CrosshairHUD from "./CrosshairHUD";
import StatusBar from "./StatusBar";
import ChatPanel from "./ChatPanel";

const MAX_POINT_LIGHTS = 4;

export default function World3D({ spec }: { spec: WorldSpec }) {
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code === "KeyT") setChatOpen((v) => !v);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const prims = useMemo(() => spec.geometry?.primitives ?? [], [spec.geometry?.primitives]);

  const partitioned = useMemo(() => ({
    ground: prims.filter((p) => p.type === "ground"),
    exterior: prims.filter((p) => p.type === "exterior_wall"),
    roof:     prims.filter((p) => p.type === "roof"),
    walls: prims.filter((p) => p.type === "wall"),
    floors: prims.filter((p) => p.type === "floor"),
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

  const cameraSpawn = useMemo(() => {
    if (prims.length === 0) {
      return {
        spawn: (spec.navigation?.spawnPoint ?? [12, 1.7, 12]) as [number, number, number],
        lookAt: [0, 1.7, 0] as [number, number, number],
      };
    }

    let minX = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let minZ = Number.POSITIVE_INFINITY;
    let maxZ = Number.NEGATIVE_INFINITY;
    let maxY = 0;

    for (const p of prims) {
      const [px, py, pz] = p.position;
      const [sx, sy, sz] = p.size;
      minX = Math.min(minX, px - sx / 2);
      maxX = Math.max(maxX, px + sx / 2);
      minZ = Math.min(minZ, pz - sz / 2);
      maxZ = Math.max(maxZ, pz + sz / 2);
      maxY = Math.max(maxY, py + sy / 2);
    }

    const centerX = (minX + maxX) / 2;
    const centerZ = (minZ + maxZ) / 2;
    const depth = maxZ - minZ;
    const offset = Math.max(7, depth * 0.35);
    const eyeY = Math.max(1.7, Math.min(2.4, maxY * 0.25 + 1.2));

    return {
      spawn: [centerX, eyeY, maxZ + offset] as [number, number, number],
      lookAt: [centerX, eyeY, centerZ] as [number, number, number],
    };
  }, [prims, spec.navigation?.spawnPoint]);

  const groundColor = spec.site?.plot?.groundColor ?? "#5a7c3a";

  return (
    <div className="fixed inset-0">
      <Canvas camera={{ fov: 70, position: cameraSpawn.spawn as any, near: 0.05, far: 300 }}>
        <color attach="background" args={["#a8c8e8"]} />
        <ambientLight intensity={0.9} />
        <directionalLight position={[60, 80, 40]} intensity={1.0} />
        {pickedLights.map(({ rid, i, l }) => (
          <pointLight key={`${rid}-${i}`} position={l.position as any} color={l.color} intensity={l.intensity} distance={12} />
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
          {walls.map((p, i) => <Wall key={`w${i}`} prim={p} color={matWall(p.roomId)} />)}
          {exterior.map((p, i) => <Wall key={`e${i}`} prim={p} color="#d8d4c6" />)}
          {roof.map((p, i) => <Roof key={`r${i}`} prim={p} color="#3a3a3a" />)}
          {stairs.map((p, i) => (
            <mesh key={`s${i}`} position={p.position as any} rotation={[0, p.rotation ?? 0, 0]}>
              <boxGeometry args={[p.size[0], 0.2, p.size[2]]} />
              <meshLambertMaterial color="#7c5a3a" />
            </mesh>
          ))}
          <FurnitureInstanced items={spec.furniture} />
        </Suspense>

        <PlayerControls walls={colliders} spawn={cameraSpawn.spawn} lookAt={cameraSpawn.lookAt} />
      </Canvas>

      <CrosshairHUD />
      <StatusBar spec={spec} />
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

"use client";
import type { GeometryPrimitive } from "@/lib/worldSpec";
import { expandWallSegments } from "@/lib/wallSegments";

export default function Wall({ prim, color }: { prim: GeometryPrimitive; color: string }) {
  const segments = expandWallSegments(prim);
  return (
    <>
      {segments.map((s, idx) => (
        <mesh key={idx} position={s.position}>
          <boxGeometry args={s.size} />
          <meshLambertMaterial color={color} />
        </mesh>
      ))}
    </>
  );
}

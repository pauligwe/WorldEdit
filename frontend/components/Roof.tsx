"use client";
import type { GeometryPrimitive } from "@/lib/worldSpec";

export default function Roof({ prim, color }: { prim: GeometryPrimitive; color: string }) {
  return (
    <mesh position={prim.position}>
      <boxGeometry args={prim.size} />
      <meshLambertMaterial color={color} />
    </mesh>
  );
}

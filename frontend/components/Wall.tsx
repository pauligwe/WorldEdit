"use client";
import type { GeometryPrimitive } from "@/lib/worldSpec";

export default function Wall({ prim, color }: { prim: GeometryPrimitive; color: string }) {
  const [w, h, d] = prim.size;
  const isXAxis = w >= d;
  const length = isXAxis ? w : d;
  const thickness = isXAxis ? d : w;
  const holes = (prim.holes ?? []).slice().sort((a, b) => a.offset - b.offset);

  const segments: { offset: number; len: number; bottom: number; height: number }[] = [];
  let cursor = 0;
  for (const hole of holes) {
    const holeStart = hole.offset - hole.width / 2;
    const holeEnd = hole.offset + hole.width / 2;
    if (holeStart > cursor) {
      segments.push({ offset: cursor, len: holeStart - cursor, bottom: 0, height: h });
    }
    if (hole.bottom > 0) {
      segments.push({ offset: holeStart, len: hole.width, bottom: 0, height: hole.bottom });
    }
    const topOfHole = hole.bottom + hole.height;
    if (topOfHole < h) {
      segments.push({ offset: holeStart, len: hole.width, bottom: topOfHole, height: h - topOfHole });
    }
    cursor = Math.max(cursor, holeEnd);
  }
  if (cursor < length) {
    segments.push({ offset: cursor, len: length - cursor, bottom: 0, height: h });
  }
  if (segments.length === 0) {
    segments.push({ offset: 0, len: length, bottom: 0, height: h });
  }

  return (
    <group position={prim.position as [number, number, number]}>
      {segments.map((s, idx) => {
        const sx = isXAxis ? s.offset - length / 2 + s.len / 2 : 0;
        const sz = isXAxis ? 0 : s.offset - length / 2 + s.len / 2;
        const sy = -h / 2 + s.bottom + s.height / 2;
        const sizeX = isXAxis ? s.len : thickness;
        const sizeY = s.height;
        const sizeZ = isXAxis ? thickness : s.len;
        return (
          <mesh key={idx} position={[sx, sy, sz]}>
            <boxGeometry args={[sizeX, sizeY, sizeZ]} />
            <meshStandardMaterial color={color} />
          </mesh>
        );
      })}
    </group>
  );
}

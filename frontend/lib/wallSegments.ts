import type { GeometryPrimitive } from "./worldSpec";

export interface WallSegment {
  position: [number, number, number];
  size: [number, number, number];
}

/** Run the same hole-aware segmentation as Wall.tsx, but emit AABB
 *  primitives suitable for collision (and for rendering). The original
 *  `prim` is the unsegmented wall; the result is the list of solid sub-boxes. */
export function expandWallSegments(prim: GeometryPrimitive): GeometryPrimitive[] {
  const [w, h, d] = prim.size;
  const isXAxis = w >= d;
  const length = isXAxis ? w : d;
  const thickness = isXAxis ? d : w;
  const holes = (prim.holes ?? []).slice().sort((a, b) => a.offset - b.offset);

  const raw: { offset: number; len: number; bottom: number; height: number }[] = [];
  let cursor = 0;
  for (const hole of holes) {
    const holeStart = hole.offset - hole.width / 2;
    const holeEnd = hole.offset + hole.width / 2;
    if (holeStart > cursor) raw.push({ offset: cursor, len: holeStart - cursor, bottom: 0, height: h });
    if (hole.bottom > 0) raw.push({ offset: holeStart, len: hole.width, bottom: 0, height: hole.bottom });
    const topOfHole = hole.bottom + hole.height;
    if (topOfHole < h) raw.push({ offset: holeStart, len: hole.width, bottom: topOfHole, height: h - topOfHole });
    cursor = Math.max(cursor, holeEnd);
  }
  if (cursor < length) raw.push({ offset: cursor, len: length - cursor, bottom: 0, height: h });
  if (raw.length === 0) raw.push({ offset: 0, len: length, bottom: 0, height: h });

  const [cx, cy, cz] = prim.position;
  return raw.map(s => {
    const sxLocal = isXAxis ? s.offset - length / 2 + s.len / 2 : 0;
    const szLocal = isXAxis ? 0 : s.offset - length / 2 + s.len / 2;
    const syLocal = -h / 2 + s.bottom + s.height / 2;
    const sizeX = isXAxis ? s.len : thickness;
    const sizeY = s.height;
    const sizeZ = isXAxis ? thickness : s.len;
    return {
      ...prim,
      position: [cx + sxLocal, cy + syLocal, cz + szLocal] as [number, number, number],
      size: [sizeX, sizeY, sizeZ] as [number, number, number],
      holes: [],
    };
  });
}

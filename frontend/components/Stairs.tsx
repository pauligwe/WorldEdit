"use client";
import type { GeometryPrimitive } from "@/lib/worldSpec";

const STEP_COUNT = 12;

export default function Stairs({ prim }: { prim: GeometryPrimitive }) {
  const [w, h, d] = prim.size;
  const stepRise = h / STEP_COUNT;
  const stepRun = d / STEP_COUNT;

  // Local frame: stair "climbs" along +z (depth). Base origin sits at the
  // stair's bottom-south corner; we offset to the primitive's stored center.
  const steps = [];
  for (let i = 0; i < STEP_COUNT; i++) {
    const treadDepth = stepRun * (STEP_COUNT - i);
    const cy = stepRise * (i + 0.5);
    const cz = -d / 2 + stepRun * i + treadDepth / 2;
    steps.push(
      <mesh key={i} position={[0, cy, cz]}>
        <boxGeometry args={[w, stepRise, treadDepth]} />
        <meshLambertMaterial color="#8b6a44" />
      </mesh>,
    );
  }

  return (
    <group position={prim.position as [number, number, number]}
           rotation={[0, prim.rotation ?? 0, 0]}>
      {steps}
    </group>
  );
}

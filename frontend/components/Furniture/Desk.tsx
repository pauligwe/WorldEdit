"use client";

interface Props { size: [number, number, number]; color: string }

export default function Desk({ size, color }: Props) {
  const [w, h, d] = size;
  const topThickness = 0.04;
  const legSize = 0.06;
  const legY = (h - topThickness) / 2;
  return (
    <group>
      <mesh position={[0, h - topThickness / 2, 0]}>
        <boxGeometry args={[w, topThickness, d]} />
        <meshLambertMaterial color={color} />
      </mesh>
      {[
        [-w / 2 + legSize, legY, -d / 2 + legSize],
        [w / 2 - legSize, legY, -d / 2 + legSize],
        [-w / 2 + legSize, legY, d / 2 - legSize],
        [w / 2 - legSize, legY, d / 2 - legSize],
      ].map((p, i) => (
        <mesh key={i} position={p as [number, number, number]}>
          <boxGeometry args={[legSize, h - topThickness, legSize]} />
          <meshLambertMaterial color="#3a3a3a" />
        </mesh>
      ))}
    </group>
  );
}

"use client";

interface Props { size: [number, number]; color: string }

export default function Plot({ size, color }: Props) {
  return (
    <mesh position={[size[0] / 2, -0.025, -size[1] / 2]}>
      <boxGeometry args={[size[0], 0.05, size[1]]} />
      <meshLambertMaterial color={color} />
    </mesh>
  );
}

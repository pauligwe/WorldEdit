"use client";

interface Props { size: [number, number, number]; color: string }

export default function Whiteboard({ size }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial color="#f5f5f0" />
      </mesh>
      <mesh position={[0, h / 2, d / 2 + 0.005]}>
        <boxGeometry args={[w + 0.04, h + 0.04, 0.01]} />
        <meshStandardMaterial color="#a0a0a0" />
      </mesh>
    </group>
  );
}

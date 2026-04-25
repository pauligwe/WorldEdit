"use client";

interface Props { size: [number, number, number]; color: string }

export default function ReceptionDesk({ size, color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d * 0.7]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, h * 0.55, d * 0.4]}>
        <boxGeometry args={[w, h * 0.2, 0.08]} />
        <meshStandardMaterial color="#222" />
      </mesh>
    </group>
  );
}

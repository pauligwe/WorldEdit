"use client";

interface Props { size: [number, number, number]; color: string }

export default function OfficeChair({ size, color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, 0.05, 0]}>
        <cylinderGeometry args={[w * 0.5, w * 0.5, 0.1, 12]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
      <mesh position={[0, h * 0.32, 0]}>
        <cylinderGeometry args={[0.04, 0.04, h * 0.45, 8]} />
        <meshStandardMaterial color="#2a2a2a" />
      </mesh>
      <mesh position={[0, h * 0.55, 0]}>
        <boxGeometry args={[w * 0.85, 0.08, d * 0.85]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, h * 0.85, -d * 0.4]}>
        <boxGeometry args={[w * 0.85, h * 0.4, 0.08]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
}

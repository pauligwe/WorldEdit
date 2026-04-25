"use client";

interface Props { size: [number, number, number]; color: string }

export default function FilingCabinet({ size, color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {[0.25, 0.5, 0.75].map((frac, i) => (
        <mesh key={i} position={[0, h * frac, d / 2 + 0.001]}>
          <boxGeometry args={[w * 0.9, 0.01, 0.005]} />
          <meshStandardMaterial color="#1a1a1a" />
        </mesh>
      ))}
    </group>
  );
}

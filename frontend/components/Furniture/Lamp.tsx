export default function Lamp({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h] = size;
  return (
    <group>
      <mesh position={[0, h * 0.05, 0]}>
        <cylinderGeometry args={[w * 0.4, w * 0.4, h * 0.1, 16]} />
        <meshStandardMaterial color="#222" />
      </mesh>
      <mesh position={[0, h * 0.5, 0]}>
        <cylinderGeometry args={[w * 0.05, w * 0.05, h * 0.8, 8]} />
        <meshStandardMaterial color="#222" />
      </mesh>
      <mesh position={[0, h * 0.9, 0]}>
        <coneGeometry args={[w * 0.4, h * 0.2, 16, 1, true]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.4} />
      </mesh>
    </group>
  );
}

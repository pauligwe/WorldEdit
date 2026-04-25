export default function Bed({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h * 0.25, 0]}>
        <boxGeometry args={[w, h * 0.5, d]} />
        <meshStandardMaterial color="#3a2a1a" />
      </mesh>
      <mesh position={[0, h * 0.65, 0]}>
        <boxGeometry args={[w * 0.95, h * 0.3, d * 0.95]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, h * 0.85, -d * 0.4]}>
        <boxGeometry args={[w * 0.4, h * 0.15, d * 0.15]} />
        <meshStandardMaterial color="#f3f4f6" />
      </mesh>
    </group>
  );
}

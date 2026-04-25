export default function Couch({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h * 0.3, 0]}>
        <boxGeometry args={[w, h * 0.6, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, h * 0.7, -d * 0.4]}>
        <boxGeometry args={[w, h * 0.6, d * 0.2]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[-w * 0.45, h * 0.5, 0]}>
        <boxGeometry args={[w * 0.1, h * 0.6, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[w * 0.45, h * 0.5, 0]}>
        <boxGeometry args={[w * 0.1, h * 0.6, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
}

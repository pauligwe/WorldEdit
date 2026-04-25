export default function Chair({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h * 0.45, 0]}>
        <boxGeometry args={[w, h * 0.1, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, h * 0.75, -d * 0.45]}>
        <boxGeometry args={[w, h * 0.6, d * 0.1]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sz], i) => (
        <mesh key={i} position={[sx * (w * 0.4), h * 0.225, sz * (d * 0.4)]}>
          <boxGeometry args={[w * 0.08, h * 0.45, d * 0.08]} />
          <meshStandardMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

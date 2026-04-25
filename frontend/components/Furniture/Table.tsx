export default function Table({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h * 0.95, 0]}>
        <boxGeometry args={[w, h * 0.1, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sz], i) => (
        <mesh key={i} position={[sx * (w * 0.45), h * 0.45, sz * (d * 0.45)]}>
          <boxGeometry args={[w * 0.06, h * 0.9, d * 0.06]} />
          <meshStandardMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

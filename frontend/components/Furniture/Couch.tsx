export default function Couch({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  const frame = "#2a1f15";
  return (
    <group>
      {/* base */}
      <mesh position={[0, h * 0.18, 0]}>
        <boxGeometry args={[w, h * 0.35, d]} />
        <meshStandardMaterial color={frame} roughness={0.7} />
      </mesh>
      {/* seat cushions */}
      <mesh position={[-w * 0.24, h * 0.45, 0.02]}>
        <boxGeometry args={[w * 0.45, h * 0.18, d * 0.85]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      <mesh position={[w * 0.24, h * 0.45, 0.02]}>
        <boxGeometry args={[w * 0.45, h * 0.18, d * 0.85]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      {/* backrest */}
      <mesh position={[0, h * 0.7, -d * 0.4]}>
        <boxGeometry args={[w * 0.85, h * 0.5, d * 0.18]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      {/* armrests */}
      <mesh position={[-w * 0.45, h * 0.42, 0]}>
        <boxGeometry args={[w * 0.1, h * 0.55, d]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      <mesh position={[w * 0.45, h * 0.42, 0]}>
        <boxGeometry args={[w * 0.1, h * 0.55, d]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      {/* legs */}
      {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sz], i) => (
        <mesh key={i} position={[sx * (w * 0.45), h * 0.04, sz * (d * 0.45)]}>
          <boxGeometry args={[w * 0.04, h * 0.08, d * 0.04]} />
          <meshStandardMaterial color={frame} />
        </mesh>
      ))}
    </group>
  );
}

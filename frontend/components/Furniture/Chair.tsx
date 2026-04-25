export default function Chair({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  const frame = "#3a2a1a";
  return (
    <group>
      {/* seat cushion */}
      <mesh position={[0, h * 0.45, 0]}>
        <boxGeometry args={[w * 0.9, h * 0.12, d * 0.9]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      {/* seat frame plank under cushion */}
      <mesh position={[0, h * 0.38, 0]}>
        <boxGeometry args={[w * 0.95, h * 0.05, d * 0.95]} />
        <meshStandardMaterial color={frame} roughness={0.7} />
      </mesh>
      {/* backrest cushion */}
      <mesh position={[0, h * 0.78, -d * 0.4]}>
        <boxGeometry args={[w * 0.85, h * 0.55, d * 0.12]} />
        <meshStandardMaterial color={color} roughness={0.85} />
      </mesh>
      {/* backrest frame */}
      <mesh position={[0, h * 0.78, -d * 0.46]}>
        <boxGeometry args={[w * 0.92, h * 0.6, d * 0.04]} />
        <meshStandardMaterial color={frame} roughness={0.7} />
      </mesh>
      {/* armrests */}
      <mesh position={[-w * 0.45, h * 0.55, 0]}>
        <boxGeometry args={[w * 0.05, h * 0.05, d * 0.7]} />
        <meshStandardMaterial color={frame} roughness={0.7} />
      </mesh>
      <mesh position={[w * 0.45, h * 0.55, 0]}>
        <boxGeometry args={[w * 0.05, h * 0.05, d * 0.7]} />
        <meshStandardMaterial color={frame} roughness={0.7} />
      </mesh>
      {/* legs */}
      {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sz], i) => (
        <mesh key={i} position={[sx * (w * 0.42), h * 0.18, sz * (d * 0.42)]}>
          <boxGeometry args={[w * 0.06, h * 0.36, d * 0.06]} />
          <meshStandardMaterial color={frame} roughness={0.6} />
        </mesh>
      ))}
    </group>
  );
}

export default function Table({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  return (
    <group>
      {/* tabletop */}
      <mesh position={[0, h * 0.92, 0]}>
        <boxGeometry args={[w, h * 0.08, d]} />
        <meshLambertMaterial color={color} />
      </mesh>
      {/* apron skirt */}
      <mesh position={[0, h * 0.82, 0]}>
        <boxGeometry args={[w * 0.9, h * 0.08, d * 0.9]} />
        <meshLambertMaterial color={color} />
      </mesh>
      {/* legs */}
      {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sz], i) => (
        <mesh key={i} position={[sx * (w * 0.45), h * 0.4, sz * (d * 0.45)]}>
          <boxGeometry args={[w * 0.07, h * 0.78, d * 0.07]} />
          <meshLambertMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

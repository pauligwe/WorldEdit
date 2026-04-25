export default function Bed({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  const frame = "#3a2a1a";
  return (
    <group>
      {/* bedframe */}
      <mesh position={[0, h * 0.18, 0]}>
        <boxGeometry args={[w, h * 0.35, d]} />
        <meshLambertMaterial color={frame} />
      </mesh>
      {/* mattress */}
      <mesh position={[0, h * 0.5, 0]}>
        <boxGeometry args={[w * 0.95, h * 0.25, d * 0.95]} />
        <meshLambertMaterial color={color} />
      </mesh>
      {/* sheet/cover */}
      <mesh position={[0, h * 0.62, d * 0.18]}>
        <boxGeometry args={[w * 0.94, h * 0.04, d * 0.55]} />
        <meshLambertMaterial color="#f3f4f6" />
      </mesh>
      {/* pillows */}
      <mesh position={[-w * 0.22, h * 0.7, -d * 0.32]}>
        <boxGeometry args={[w * 0.36, h * 0.1, d * 0.18]} />
        <meshLambertMaterial color="#fafafa" />
      </mesh>
      <mesh position={[w * 0.22, h * 0.7, -d * 0.32]}>
        <boxGeometry args={[w * 0.36, h * 0.1, d * 0.18]} />
        <meshLambertMaterial color="#fafafa" />
      </mesh>
      {/* headboard */}
      <mesh position={[0, h * 0.95, -d * 0.5]}>
        <boxGeometry args={[w * 1.02, h * 0.6, d * 0.06]} />
        <meshLambertMaterial color={frame} />
      </mesh>
    </group>
  );
}

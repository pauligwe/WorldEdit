export default function Bookshelf({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  // wardrobe / cabinet / bookshelf with carcass + side panels + shelves + handles
  return (
    <group>
      {/* back panel */}
      <mesh position={[0, h * 0.5, -d * 0.4]}>
        <boxGeometry args={[w, h, d * 0.04]} />
        <meshStandardMaterial color={color} roughness={0.6} />
      </mesh>
      {/* bottom */}
      <mesh position={[0, h * 0.02, 0]}>
        <boxGeometry args={[w, h * 0.04, d * 0.85]} />
        <meshStandardMaterial color={color} roughness={0.55} />
      </mesh>
      {/* top */}
      <mesh position={[0, h * 0.98, 0]}>
        <boxGeometry args={[w, h * 0.04, d * 0.9]} />
        <meshStandardMaterial color={color} roughness={0.5} />
      </mesh>
      {/* side panels */}
      <mesh position={[-w * 0.48, h * 0.5, 0]}>
        <boxGeometry args={[w * 0.04, h, d * 0.85]} />
        <meshStandardMaterial color={color} roughness={0.55} />
      </mesh>
      <mesh position={[w * 0.48, h * 0.5, 0]}>
        <boxGeometry args={[w * 0.04, h, d * 0.85]} />
        <meshStandardMaterial color={color} roughness={0.55} />
      </mesh>
      {/* doors (split center) */}
      <mesh position={[-w * 0.235, h * 0.5, d * 0.42]}>
        <boxGeometry args={[w * 0.46, h * 0.92, d * 0.03]} />
        <meshStandardMaterial color={color} roughness={0.4} />
      </mesh>
      <mesh position={[w * 0.235, h * 0.5, d * 0.42]}>
        <boxGeometry args={[w * 0.46, h * 0.92, d * 0.03]} />
        <meshStandardMaterial color={color} roughness={0.4} />
      </mesh>
      {/* handles */}
      <mesh position={[-w * 0.04, h * 0.5, d * 0.45]}>
        <cylinderGeometry args={[0.012, 0.012, h * 0.18, 8]} />
        <meshStandardMaterial color="#cfcfcf" metalness={0.8} roughness={0.25} />
      </mesh>
      <mesh position={[w * 0.04, h * 0.5, d * 0.45]}>
        <cylinderGeometry args={[0.012, 0.012, h * 0.18, 8]} />
        <meshStandardMaterial color="#cfcfcf" metalness={0.8} roughness={0.25} />
      </mesh>
    </group>
  );
}

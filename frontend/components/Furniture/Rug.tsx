export default function Rug({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, , d] = size;
  return (
    <group>
      {/* main rug */}
      <mesh position={[0, 0.008, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[w, d]} />
        <meshStandardMaterial color={color} roughness={1} />
      </mesh>
      {/* darker border for depth */}
      <mesh position={[0, 0.005, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[w * 1.04, d * 1.04]} />
        <meshStandardMaterial color="#2a1d12" roughness={1} />
      </mesh>
    </group>
  );
}

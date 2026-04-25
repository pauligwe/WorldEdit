export default function Rug({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, , d] = size;
  return (
    <mesh position={[0, 0.005, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[w, d]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

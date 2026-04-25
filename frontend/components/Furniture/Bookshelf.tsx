export default function Bookshelf({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h * 0.5, 0]}>
        <boxGeometry args={[w, h, d * 0.2]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {[0.2, 0.4, 0.6, 0.8].map((y, i) => (
        <mesh key={i} position={[0, h * y, d * 0.05]}>
          <boxGeometry args={[w * 0.9, h * 0.02, d * 0.18]} />
          <meshStandardMaterial color="#7c3a1d" />
        </mesh>
      ))}
    </group>
  );
}

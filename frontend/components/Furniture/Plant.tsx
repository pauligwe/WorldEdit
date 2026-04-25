export default function Plant({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h] = size;
  return (
    <group>
      <mesh position={[0, h * 0.15, 0]}>
        <cylinderGeometry args={[w * 0.4, w * 0.3, h * 0.3, 12]} />
        <meshStandardMaterial color="#5b4636" />
      </mesh>
      <mesh position={[0, h * 0.65, 0]}>
        <sphereGeometry args={[w * 0.55, 16, 16]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
}

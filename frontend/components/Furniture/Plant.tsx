export default function Plant({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h] = size;
  const leaf = color || "#3f7a3a";
  // pot + soil + cluster of leaves
  return (
    <group>
      {/* pot */}
      <mesh position={[0, h * 0.15, 0]}>
        <cylinderGeometry args={[w * 0.42, w * 0.3, h * 0.3, 16]} />
        <meshLambertMaterial color="#6b4a2b" />
      </mesh>
      {/* soil */}
      <mesh position={[0, h * 0.31, 0]}>
        <cylinderGeometry args={[w * 0.4, w * 0.4, h * 0.02, 16]} />
        <meshLambertMaterial color="#3b2410" />
      </mesh>
      {/* leaf clusters */}
      <mesh position={[0, h * 0.7, 0]}>
        <sphereGeometry args={[w * 0.55, 14, 12]} />
        <meshLambertMaterial color={leaf} />
      </mesh>
      <mesh position={[w * 0.18, h * 0.85, w * 0.1]}>
        <sphereGeometry args={[w * 0.3, 12, 10]} />
        <meshLambertMaterial color={leaf} />
      </mesh>
      <mesh position={[-w * 0.18, h * 0.82, -w * 0.1]}>
        <sphereGeometry args={[w * 0.32, 12, 10]} />
        <meshLambertMaterial color={leaf} />
      </mesh>
      <mesh position={[0, h * 0.95, 0]}>
        <sphereGeometry args={[w * 0.25, 12, 10]} />
        <meshLambertMaterial color={leaf} />
      </mesh>
    </group>
  );
}

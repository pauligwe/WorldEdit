import * as THREE from "three";

export default function Lamp({ size, color }: { size: [number, number, number]; color: string }) {
  const [w, h] = size;
  const shadeColor = "#f5e6c4";
  return (
    <group>
      {/* base */}
      <mesh position={[0, h * 0.04, 0]}>
        <cylinderGeometry args={[w * 0.42, w * 0.45, h * 0.08, 24]} />
        <meshStandardMaterial color="#222" metalness={0.6} roughness={0.4} />
      </mesh>
      {/* pole */}
      <mesh position={[0, h * 0.5, 0]}>
        <cylinderGeometry args={[w * 0.04, w * 0.04, h * 0.8, 12]} />
        <meshStandardMaterial color="#222" metalness={0.55} roughness={0.4} />
      </mesh>
      {/* shade — wider top for table-lamp feel */}
      <mesh position={[0, h * 0.86, 0]}>
        <cylinderGeometry args={[w * 0.32, w * 0.42, h * 0.22, 24, 1, true]} />
        <meshStandardMaterial color={shadeColor} emissive={color} emissiveIntensity={0.6} side={THREE.DoubleSide} />
      </mesh>
      {/* shade top cap */}
      <mesh position={[0, h * 0.97, 0]}>
        <cylinderGeometry args={[w * 0.32, w * 0.32, h * 0.01, 24]} />
        <meshStandardMaterial color={shadeColor} />
      </mesh>
    </group>
  );
}

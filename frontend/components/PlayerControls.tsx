"use client";
import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { PointerLockControls } from "@react-three/drei";
import * as THREE from "three";
import type { GeometryPrimitive } from "@/lib/worldSpec";

interface Props { walls: GeometryPrimitive[]; spawn: [number, number, number]; }

const SPEED = 4.0;
const SPRINT = 7.5;
const PLAYER_RADIUS = 0.3;

export default function PlayerControls({ walls, spawn }: Props) {
  const { camera } = useThree();
  const pressed = useRef<Record<string, boolean>>({});
  const initialized = useRef(false);

  useEffect(() => {
    if (!initialized.current) {
      camera.position.set(spawn[0], spawn[1], spawn[2]);
      initialized.current = true;
    }
    function down(e: KeyboardEvent) { pressed.current[e.code] = true; }
    function up(e: KeyboardEvent) { pressed.current[e.code] = false; }
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [camera, spawn]);

  useFrame((_, delta) => {
    const k = pressed.current;
    const speed = (k["ShiftLeft"] || k["ShiftRight"]) ? SPRINT : SPEED;
    const dir = new THREE.Vector3();
    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0;
    forward.normalize();
    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

    if (k["KeyW"]) dir.add(forward);
    if (k["KeyS"]) dir.sub(forward);
    if (k["KeyD"]) dir.add(right);
    if (k["KeyA"]) dir.sub(right);
    if (dir.lengthSq() === 0) return;
    dir.normalize().multiplyScalar(speed * delta);

    const next = camera.position.clone().add(dir);
    if (!collides(next, walls)) {
      camera.position.copy(next);
    } else {
      const nx = camera.position.clone(); nx.x += dir.x;
      if (!collides(nx, walls)) camera.position.copy(nx);
      const nz = camera.position.clone(); nz.z += dir.z;
      if (!collides(nz, walls)) camera.position.copy(nz);
    }
  });

  return <PointerLockControls />;
}

function collides(p: THREE.Vector3, walls: GeometryPrimitive[]): boolean {
  for (const w of walls) {
    const [cx, cy, cz] = w.position;
    const [sx, sy, sz] = w.size;
    const dx = Math.abs(p.x - cx) - (sx / 2 + PLAYER_RADIUS);
    const dz = Math.abs(p.z - cz) - (sz / 2 + PLAYER_RADIUS);
    const dy = Math.abs(p.y - cy) - sy / 2;
    if (dx < 0 && dz < 0 && dy < 0) return true;
  }
  return false;
}

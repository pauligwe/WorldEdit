"use client";
import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { PointerLockControls } from "@react-three/drei";
import * as THREE from "three";
import type { GeometryPrimitive } from "@/lib/worldSpec";

interface Props { walls: GeometryPrimitive[]; spawn: [number, number, number]; enabled?: boolean; }

const SPEED = 6.0;
const SPRINT = 14.0;

export default function PlayerControls({ walls: _walls, spawn, enabled = true }: Props) {
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
    const sprinting = k["ShiftLeft"] || k["ShiftRight"];
    const speed = sprinting ? SPRINT : SPEED;
    const dir = new THREE.Vector3();
    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0;
    if (forward.lengthSq() > 0) forward.normalize();
    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

    if (k["KeyW"]) dir.add(forward);
    if (k["KeyS"]) dir.sub(forward);
    if (k["KeyD"]) dir.add(right);
    if (k["KeyA"]) dir.sub(right);
    if (k["Space"]) dir.y += 1;
    if (sprinting && k["KeyC"]) dir.y -= 1; // optional crouch with sprint
    if (k["ControlLeft"] || k["ControlRight"]) dir.y -= 1;

    if (dir.lengthSq() === 0) return;
    dir.normalize().multiplyScalar(speed * delta);
    camera.position.add(dir);
  });

  // selector="#splat-lock-target" — drei's default attaches the click-to-lock
  // listener to `document`, which means clicking ANY UI element (sidebar
  // button, modal, etc.) re-grabs the lock. Scoping it to the canvas means
  // only clicks on empty canvas area lock — UI overlays at higher z-index
  // swallow their own clicks first. The `enabled` prop is unused here, kept
  // in case we want to gate movement separately later.
  void enabled;
  return <PointerLockControls selector="#splat-lock-target" />;
}

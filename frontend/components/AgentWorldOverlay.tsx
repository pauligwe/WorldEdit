"use client";

import { useMemo, useRef } from "react";
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import type { Group, Mesh } from "three";
import type { AgentWorldEvent, AgentWorldSnapshot } from "@/lib/agentWorld";

type HoverPayload = {
  agentKey: string;
  x: number;
  y: number;
} | null;

interface Props {
  snapshots: Record<string, AgentWorldSnapshot>;
  events: AgentWorldEvent[];
  onHover: (hover: HoverPayload) => void;
  onSelect: (agentKey: string) => void;
  selectedAgentKey: string | null;
}

export default function AgentWorldOverlay({ snapshots, events, onHover, onSelect, selectedAgentKey }: Props) {
  const sorted = useMemo(
    () => Object.values(snapshots).sort((a, b) => a.station[0] - b.station[0]),
    [snapshots],
  );
  const doneOrder = useMemo(() => {
    const done = events
      .filter((e) => e.event.state === "done" && !e.event.agent.startsWith("__"))
      .map((e) => e.event.agent);
    return Array.from(new Set(done));
  }, [events]);

  return (
    <group>
      <mesh position={[-10.2, 0.04, -3.4]}>
        <cylinderGeometry args={[0.9, 0.9, 0.08, 32]} />
        <meshStandardMaterial color="#1f6542" emissive="#0f3b27" emissiveIntensity={0.8} />
      </mesh>
      <mesh position={[-10.2, 0.22, -3.4]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.84, 0.07, 10, 36]} />
        <meshStandardMaterial color="#7df0b6" emissive="#35c682" emissiveIntensity={1} />
      </mesh>

      <mesh position={[10.2, 0.04, 5.8]}>
        <cylinderGeometry args={[0.9, 0.9, 0.08, 32]} />
        <meshStandardMaterial color="#6e3140" emissive="#3a1620" emissiveIntensity={0.8} />
      </mesh>
      <mesh position={[10.2, 0.22, 5.8]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.84, 0.07, 10, 36]} />
        <meshStandardMaterial color="#ff8ea8" emissive="#df4c73" emissiveIntensity={1} />
      </mesh>
      <mesh position={[0, 0.05, -6]}>
        <boxGeometry args={[9, 0.12, 2.2]} />
        <meshStandardMaterial color="#243342" emissive="#0a1018" />
      </mesh>
      <mesh position={[-1.6, 0.05, -1.3]}>
        <boxGeometry args={[8.5, 0.12, 2.2]} />
        <meshStandardMaterial color="#2a3344" emissive="#0a1018" />
      </mesh>
      <mesh position={[1.8, 0.05, 3.6]}>
        <boxGeometry args={[15, 0.12, 2.2]} />
        <meshStandardMaterial color="#31283c" emissive="#120a18" />
      </mesh>
      {sorted.map((snapshot, idx) => (
        <Avatar
          key={snapshot.key}
          snapshot={snapshot}
          idx={idx}
          doneIndex={doneOrder.indexOf(snapshot.key)}
          selected={selectedAgentKey === snapshot.key}
          onHover={onHover}
          onSelect={onSelect}
        />
      ))}
    </group>
  );
}

function Avatar({
  snapshot,
  idx,
  doneIndex,
  selected,
  onHover,
  onSelect,
}: {
  snapshot: AgentWorldSnapshot;
  idx: number;
  doneIndex: number;
  selected: boolean;
  onHover: (hover: HoverPayload) => void;
  onSelect: (agentKey: string) => void;
}) {
  const rigRef = useRef<Group>(null);
  const bodyRef = useRef<Mesh>(null);
  const leftArmRef = useRef<Mesh>(null);
  const rightArmRef = useRef<Mesh>(null);
  const leftLegRef = useRef<Mesh>(null);
  const rightLegRef = useRef<Mesh>(null);
  const station = snapshot.station;
  const entrance: [number, number, number] = [-10.2, 0.16, -3.4];
  const exitBase: [number, number, number] = [10.2, 0.16, 5.8];
  const prevStatusRef = useRef<AgentWorldSnapshot["status"]>("idle");
  const runStartRef = useRef<[number, number, number]>(entrance);
  const doneStartRef = useRef<[number, number, number]>(station);
  const lastPosRef = useRef<[number, number, number]>(entrance);

  useFrame(({ clock }) => {
    const rig = rigRef.current;
    const body = bodyRef.current;
    if (!body || !rig) return;
    const t = clock.getElapsedTime();
    const statusChanged = prevStatusRef.current !== snapshot.status;
    if (statusChanged) {
      const currentPos: [number, number, number] = [rig.position.x, rig.position.y, rig.position.z];
      if (snapshot.status === "running") {
        runStartRef.current = currentPos;
      }
      if (snapshot.status === "done") {
        doneStartRef.current = currentPos;
      }
      prevStatusRef.current = snapshot.status;
    }

    const walk = snapshot.visualState === "walking";
    const active = snapshot.visualState === "working" || snapshot.visualState === "chatting";
    const bob = walk ? 0.08 : active ? 0.05 : 0.025;
    body.position.y = 0.72 + Math.sin(t * 2 + idx) * bob;

    const swing = walk ? Math.sin(t * 6 + idx) * 0.45 : active ? Math.sin(t * 3 + idx) * 0.15 : 0;
    if (leftArmRef.current) leftArmRef.current.rotation.x = swing;
    if (rightArmRef.current) rightArmRef.current.rotation.x = -swing;
    if (leftLegRef.current) leftLegRef.current.rotation.x = -swing * 0.6;
    if (rightLegRef.current) rightLegRef.current.rotation.x = swing * 0.6;

    const p = resolvePosition(snapshot, station, runStartRef.current, doneStartRef.current, entrance, exitBase, doneIndex);
    rig.position.x = p[0];
    rig.position.y = p[1];
    rig.position.z = p[2];
    lastPosRef.current = p;

    if (snapshot.status === "running") {
      rig.rotation.y = Math.atan2(station[0] - runStartRef.current[0], station[2] - runStartRef.current[2]);
    } else if (snapshot.status === "done") {
      const exitSpot = resolveExitSpot(exitBase, doneIndex, idx);
      rig.rotation.y = Math.atan2(exitSpot[0] - doneStartRef.current[0], exitSpot[2] - doneStartRef.current[2]);
    } else {
      rig.rotation.y = 0;
    }

    rig.visible = shouldBeVisible(snapshot);
  });

  const palette = avatarPalette(snapshot.visualState);

  function setHover(e: ThreeEvent<PointerEvent>) {
    onHover({ agentKey: snapshot.key, x: e.clientX, y: e.clientY });
  }

  return (
    <group ref={rigRef} position={entrance}>
      <mesh position={[0, 0.08, 0]}>
        <cylinderGeometry args={[0.44, 0.5, 0.06, 24]} />
        <meshStandardMaterial color={selected ? "#f5d26e" : "#2e3540"} />
      </mesh>
      <mesh
        ref={bodyRef}
        position={[0, 0.72, 0]}
        onPointerOver={setHover}
        onPointerMove={setHover}
        onPointerOut={() => onHover(null)}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(snapshot.key);
        }}
      >
        <capsuleGeometry args={[0.2, 0.5, 8, 16]} />
        <meshStandardMaterial color={palette.shirt} emissive={selected ? "#3a2a0d" : palette.shirt} emissiveIntensity={selected ? 0.25 : 0.08} />
      </mesh>
      <mesh position={[0, 1.43, 0]}>
        <sphereGeometry args={[0.2, 20, 20]} />
        <meshStandardMaterial color={palette.skin} />
      </mesh>

      <mesh position={[0, 1.62, 0]}>
        <sphereGeometry args={[0.21, 20, 20, 0, Math.PI * 2, 0, Math.PI * 0.55]} />
        <meshStandardMaterial color={palette.hair} />
      </mesh>

      <mesh position={[-0.065, 1.45, 0.18]}>
        <sphereGeometry args={[0.02, 8, 8]} />
        <meshStandardMaterial color="#1b1b1b" />
      </mesh>
      <mesh position={[0.065, 1.45, 0.18]}>
        <sphereGeometry args={[0.02, 8, 8]} />
        <meshStandardMaterial color="#1b1b1b" />
      </mesh>
      <mesh position={[0, 1.35, 0.19]}>
        <boxGeometry args={[0.08, 0.01, 0.01]} />
        <meshStandardMaterial color="#8b4f4f" />
      </mesh>

      <mesh ref={leftArmRef} position={[-0.24, 0.8, 0]}>
        <capsuleGeometry args={[0.05, 0.24, 6, 10]} />
        <meshStandardMaterial color={palette.shirt} />
      </mesh>
      <mesh ref={rightArmRef} position={[0.24, 0.8, 0]}>
        <capsuleGeometry args={[0.05, 0.24, 6, 10]} />
        <meshStandardMaterial color={palette.shirt} />
      </mesh>
      <mesh ref={leftLegRef} position={[-0.09, 0.33, 0]}>
        <capsuleGeometry args={[0.05, 0.28, 6, 10]} />
        <meshStandardMaterial color={palette.pants} />
      </mesh>
      <mesh ref={rightLegRef} position={[0.09, 0.33, 0]}>
        <capsuleGeometry args={[0.05, 0.28, 6, 10]} />
        <meshStandardMaterial color={palette.pants} />
      </mesh>

      <mesh position={[0, 1.84, 0]}>
        <sphereGeometry args={[0.06, 12, 12]} />
        <meshStandardMaterial color={selected ? "#ffd96b" : "#8fd3ff"} emissive={selected ? "#ffd96b" : "#8fd3ff"} emissiveIntensity={0.8} />
      </mesh>
    </group>
  );
}

function resolvePosition(
  snapshot: AgentWorldSnapshot,
  station: [number, number, number],
  runStart: [number, number, number],
  doneStart: [number, number, number],
  entrance: [number, number, number],
  exitBase: [number, number, number],
  doneIndex: number,
): [number, number, number] {
  if (!snapshot.lastUpdateAt) return entrance;
  const elapsed = Date.now() - snapshot.lastUpdateAt;

  if (snapshot.status === "running") {
    const t = clamp(elapsed / 1600, 0, 1);
    return lerp3(runStart, station, easeInOut(t));
  }

  if (snapshot.status === "done") {
    const exitSpot = resolveExitSpot(exitBase, doneIndex, 0);
    const t = clamp(elapsed / 1200, 0, 1);
    return lerp3(doneStart, exitSpot, easeInOut(t));
  }

  if (snapshot.status === "error") {
    return [station[0], station[1], station[2] + 0.55];
  }

  return entrance;
}

function resolveExitSpot(
  exitBase: [number, number, number],
  doneIndex: number,
  fallbackSeed: number,
): [number, number, number] {
  const idx = doneIndex >= 0 ? doneIndex : fallbackSeed;
  const row = Math.floor(idx / 3);
  const col = idx % 3;
  return [exitBase[0] + row * 0.4, exitBase[1], exitBase[2] - col * 0.4];
}

function shouldBeVisible(snapshot: AgentWorldSnapshot): boolean {
  if (!snapshot.lastUpdateAt) return false;
  const elapsed = Date.now() - snapshot.lastUpdateAt;
  if (snapshot.status === "idle") return false;
  if (snapshot.status === "done" && elapsed > 1250) return false;
  return true;
}

function lerp3(a: [number, number, number], b: [number, number, number], t: number): [number, number, number] {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

function clamp(v: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, v));
}

function easeInOut(t: number): number {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

function avatarPalette(state: AgentWorldSnapshot["visualState"]): { shirt: string; pants: string; skin: string; hair: string } {
  switch (state) {
    case "walking":
      return { shirt: "#5ca5ff", pants: "#2f4e73", skin: "#f0dcc9", hair: "#2f2b29" };
    case "working":
      return { shirt: "#42cb98", pants: "#275343", skin: "#f4dfc7", hair: "#2f2b29" };
    case "chatting":
      return { shirt: "#a184ff", pants: "#3b3166", skin: "#edd5be", hair: "#3a3128" };
    case "done":
      return { shirt: "#59bf63", pants: "#2e5331", skin: "#f2dcc4", hair: "#2f2b29" };
    case "error":
      return { shirt: "#ef5f5f", pants: "#5e2a2a", skin: "#efd2bd", hair: "#2f2b29" };
    case "idle":
    default:
      return { shirt: "#8a94a3", pants: "#3f4650", skin: "#ebd2b9", hair: "#2f2b29" };
  }
}

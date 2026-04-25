"use client";

import { useMemo, useRef } from "react";
import { Text } from "@react-three/drei";
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import type { Group } from "three";
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
      <mesh position={[0, 0.012, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[24, 16]} />
        <meshBasicMaterial color="#131824" opacity={0.78} transparent />
      </mesh>
      <BoxFrame width={24} height={16} y={0.018} color="#67e8f9" />
      <mesh position={[-10.2, 0.02, -3.4]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.62, 28]} />
        <meshBasicMaterial color="#34d399" />
      </mesh>
      <mesh position={[10.2, 0.02, 5.8]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.62, 28]} />
        <meshBasicMaterial color="#fb7185" />
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

function BoxFrame({ width, height, y, color }: { width: number; height: number; y: number; color: string }) {
  const t = 0.18;
  const hw = width / 2;
  const hh = height / 2;
  return (
    <group>
      <mesh position={[0, y, -hh]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, t]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh position={[0, y, hh]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, t]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh position={[-hw, y, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[t, height]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh position={[hw, y, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[t, height]} />
        <meshBasicMaterial color={color} />
      </mesh>
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
  const station = snapshot.station;
  const entrance: [number, number, number] = [-10.2, 0.06, -3.4];
  const exitBase: [number, number, number] = [10.2, 0.06, 5.8];
  const prevStatusRef = useRef<AgentWorldSnapshot["status"]>("idle");
  const runStartRef = useRef<[number, number, number]>(entrance);
  const doneStartRef = useRef<[number, number, number]>(station);

  useFrame(() => {
    const rig = rigRef.current;
    if (!rig) return;
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

    const p = resolvePosition(snapshot, station, runStartRef.current, doneStartRef.current, entrance, exitBase, doneIndex);
    rig.position.x = p[0];
    rig.position.y = p[1];
    rig.position.z = p[2];
    rig.visible = shouldBeVisible(snapshot);
  });

  const colors = iconColors(snapshot.visualState);

  function setHover(e: ThreeEvent<PointerEvent>) {
    onHover({ agentKey: snapshot.key, x: e.clientX, y: e.clientY });
  }

  return (
    <group ref={rigRef} position={entrance}>
      <group scale={[2, 2, 2]}>
        <mesh
          position={[0, 0.06, 0]}
          rotation={[-Math.PI / 2, 0, 0]}
          onPointerOver={setHover}
          onPointerMove={setHover}
          onPointerOut={() => onHover(null)}
          onClick={(e) => {
            e.stopPropagation();
            onSelect(snapshot.key);
          }}
        >
          <circleGeometry args={[selected ? 0.72 : 0.64, 30]} />
          <meshBasicMaterial color={selected ? "#f4d35e" : colors.fill} />
        </mesh>
        <mesh position={[0, 0.062, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.46, 24]} />
          <meshBasicMaterial color="#111827" />
        </mesh>
        <mesh position={[0, 0.064, 0.02]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.45, 0.18]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
        <mesh position={[-0.075, 0.065, 0.02]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.034, 16]} />
          <meshBasicMaterial color="#111827" />
        </mesh>
        <mesh position={[0.075, 0.065, 0.02]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.034, 16]} />
          <meshBasicMaterial color="#111827" />
        </mesh>
        <mesh position={[0, 0.064, -0.055]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.25, 0.12]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
        <mesh position={[0, 0.066, 0.13]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.024, 0.15]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
        <mesh position={[0, 0.066, 0.18]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.04, 16]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
        <mesh position={[0, 0.066, 0.18]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.08, 0.1, 24, 1, 0.35, Math.PI - 0.7]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
        <mesh position={[0, 0.066, 0.18]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.14, 0.165, 24, 1, 0.35, Math.PI - 0.7]} />
          <meshBasicMaterial color="#f8fafc" />
        </mesh>
        <mesh position={[0, 0.067, 1.45]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[3.2, 0.62]} />
          <meshBasicMaterial color="#0b1220" opacity={0.88} transparent />
        </mesh>
        <Text
          position={[0, 0.068, 1.45]}
          rotation={[-Math.PI / 2, 0, 0]}
          fontSize={0.3}
          color="#f8fbff"
          anchorX="center"
          anchorY="middle"
          maxWidth={2.9}
        >
          {snapshot.name}
        </Text>
      </group>
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
    return [station[0], 0.06, station[2] + 0.55];
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

function iconColors(state: AgentWorldSnapshot["visualState"]): { fill: string; text: string } {
  switch (state) {
    case "walking":
      return { fill: "#4b95ff", text: "#ffffff" };
    case "working":
      return { fill: "#2fba7f", text: "#0b1a0f" };
    case "chatting":
      return { fill: "#9064f4", text: "#ffffff" };
    case "done":
      return { fill: "#4caf50", text: "#eaffea" };
    case "error":
      return { fill: "#e15353", text: "#ffecec" };
    case "idle":
    default:
      return { fill: "#6f7c8d", text: "#e7eef9" };
  }
}

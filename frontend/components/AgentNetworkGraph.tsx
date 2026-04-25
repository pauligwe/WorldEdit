"use client";
import { useEffect, useRef, useState } from "react";
import { AGENTS } from "@/lib/agentManifest";
import type { AgentResults } from "@/lib/agentResults";

const W = 380;
const H = 360;
const ROWS = 6;
const COLS = 5;
const PADDING = 24;
const COL_W = (W - PADDING * 2) / (COLS - 1);
const ROW_H = (H - PADDING * 2) / (ROWS - 1);

const FETCH_BLUE = "#4a90ff";
const TRACE = "#333";
const NODE_BG = "#fff";

interface Node {
  id: string;
  label: string;
  x: number;
  y: number;
}

const CAPTURE_NODE: Node = {
  id: "__capture__",
  label: "CAPTURE",
  x: PADDING + 2 * COL_W,
  y: PADDING + 0 * ROW_H,
};

const NODES: Node[] = [
  CAPTURE_NODE,
  ...AGENTS.map((a) => ({
    id: a.id,
    label: a.label.toUpperCase(),
    x: PADDING + a.col * COL_W,
    y: PADDING + a.row * ROW_H,
  })),
];

const NODES_BY_ID = Object.fromEntries(NODES.map((n) => [n.id, n]));

interface Edge {
  from: string;
  to: string;
}

const EDGES: Edge[] = [
  ...AGENTS.filter((a) => a.tier === 0).map((a) => ({ from: "__capture__", to: a.id })),
  ...AGENTS.flatMap((a) => a.dependencies.map((d) => ({ from: d, to: a.id }))),
];

function tracePath(a: Node, b: Node): string {
  const midX = b.x;
  const midY = a.y;
  return `M ${a.x} ${a.y} L ${midX} ${midY} L ${b.x} ${b.y}`;
}

const SCRIPT_DURATION_MS = 12_000;
function nodeLightTime(id: string): number {
  if (id === "__capture__") return 400;
  const a = AGENTS.find((x) => x.id === id)!;
  const tier = a.tier;
  const rowOrder = AGENTS.filter((x) => x.tier === tier).indexOf(a);
  return 1500 + tier * 1800 + rowOrder * 200;
}

function edgeLightTime(e: Edge): number {
  return Math.max(nodeLightTime(e.from), nodeLightTime(e.to));
}

export default function AgentNetworkGraph({ results }: { results: AgentResults | null }) {
  const [now, setNow] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    let raf: number;
    function tick(t: number) {
      if (startRef.current == null) startRef.current = t;
      setNow(t - startRef.current);
      if (t - startRef.current < SCRIPT_DURATION_MS + 500) {
        raf = requestAnimationFrame(tick);
      }
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const litNodes = new Set<string>();
  for (const n of NODES) {
    if (now >= nodeLightTime(n.id)) litNodes.add(n.id);
  }
  const activeEdges = EDGES.filter((e) => {
    const t = edgeLightTime(e);
    return now >= t - 600 && now <= t + 400;
  });

  return (
    <div className="border border-outline-variant rounded bg-[#fafafa] p-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <defs>
          <pattern id="grid-bg" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#eee" strokeWidth="0.5" />
          </pattern>
          <filter id="glow"><feGaussianBlur stdDeviation="2" /></filter>
        </defs>
        <rect width={W} height={H} fill="url(#grid-bg)" />

        {EDGES.map((e, i) => {
          const a = NODES_BY_ID[e.from];
          const b = NODES_BY_ID[e.to];
          const lit = litNodes.has(e.from) && litNodes.has(e.to);
          const active = activeEdges.includes(e);
          return (
            <g key={i}>
              <path d={tracePath(a, b)} fill="none"
                    stroke={active ? FETCH_BLUE : (lit ? TRACE : "#ccc")}
                    strokeWidth={active ? 2 : 1}
                    style={active ? { filter: "url(#glow)" } : undefined} />
              {active && (
                <circle r="2.5" fill={FETCH_BLUE}>
                  <animateMotion dur="0.6s" repeatCount="1" path={tracePath(a, b)} />
                </circle>
              )}
            </g>
          );
        })}

        {NODES.map((n) => {
          const lit = litNodes.has(n.id);
          const fill = lit ? (n.id === "__capture__" ? FETCH_BLUE : NODE_BG) : "#f0f0f0";
          const stroke = lit ? TRACE : "#ccc";
          return (
            <g key={n.id}>
              <rect x={n.x - 8} y={n.y - 8} width={16} height={16}
                    fill={fill} stroke={stroke} strokeWidth={1.5} />
              <text x={n.x} y={n.y - 12} textAnchor="middle"
                    fontFamily="monospace" fontSize="6.5" fill="#666">
                {n.label.slice(0, 14)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

"use client";
import { useEffect, useRef, useState } from "react";
import { AGENTS } from "@/lib/agentManifest";
import type { AgentResults } from "@/lib/agentResults";

// SVG canvas: wide enough to fit full labels on the leftmost (col 0) and
// rightmost (col 4) columns. PADDING_X gives ~50px on each side for the
// outer column labels to breathe.
const W = 460;
const H = 380;
const ROWS = 6;
const COLS = 5;
const PADDING_X = 60;
const PADDING_Y = 30;
const COL_W = (W - PADDING_X * 2) / (COLS - 1);
const ROW_H = (H - PADDING_Y * 2) / (ROWS - 1);

const FETCH_BLUE = "#4a90ff";
const TRACE = "#333";
const NODE_BG = "#fff";

// ---- Scripted animation timeline ----
// 5 tiers × 4s = 20s total. Each tier:
//   - Inbound edges fill from 0 → 1.0 over `EDGE_FILL_MS`
//   - Tier nodes light up the moment their edges hit 1.0
//   - Then a brief settle before the next tier kicks off
const STAGE_MS = 4000;          // per-tier wall-clock budget
const EDGE_FILL_MS = 3400;      // edge fill duration within a stage
const NODE_LIGHTUP_MS = 350;    // node fade-in once edge lands
const TIER_COUNT = 5;
const TOTAL_MS = STAGE_MS * TIER_COUNT;

interface Node {
  id: string;
  label: string;
  tier: number;
  x: number;
  y: number;
}

const CAPTURE_NODE: Node = {
  id: "__capture__",
  label: "CAPTURE",
  tier: -1,
  x: PADDING_X + 2 * COL_W,
  y: PADDING_Y + 0 * ROW_H,
};

const NODES: Node[] = [
  CAPTURE_NODE,
  ...AGENTS.map((a) => ({
    id: a.id,
    label: a.label.toUpperCase(),
    tier: a.tier,
    x: PADDING_X + a.col * COL_W,
    y: PADDING_Y + a.row * ROW_H,
  })),
];

const NODES_BY_ID = Object.fromEntries(NODES.map((n) => [n.id, n]));

interface Edge {
  from: string;
  to: string;
  tier: number;
}

const EDGES: Edge[] = [
  ...AGENTS.filter((a) => a.tier === 0).map((a) => ({ from: "__capture__", to: a.id, tier: 0 as number })),
  ...AGENTS.flatMap((a) => a.dependencies.map((d) => ({ from: d, to: a.id, tier: a.tier as number }))),
];

const ARROW_INSET = 12;

function tracePath(a: Node, b: Node): string {
  // Orthogonal L-shape: vertical segment from a, then horizontal into b.
  const midX = b.x;
  const midY = a.y;
  const dx = b.x - midX;
  const dy = b.y - midY;
  let endX = b.x;
  let endY = b.y;
  if (Math.abs(dy) > 0.001) {
    endY = b.y - Math.sign(dy) * ARROW_INSET;
  } else if (Math.abs(dx) > 0.001) {
    endX = b.x - Math.sign(dx) * ARROW_INSET;
  } else {
    endX = b.x - Math.sign(b.x - a.x || 1) * ARROW_INSET;
  }
  return `M ${a.x} ${a.y} L ${midX} ${midY} L ${endX} ${endY}`;
}

function edgeFillFrac(t: number, tier: number): number {
  const stageStart = tier * STAGE_MS;
  if (t < stageStart) return 0;
  const elapsed = t - stageStart;
  if (elapsed >= EDGE_FILL_MS) return 1;
  // Smooth ease-out so the bar accelerates in then settles
  const x = elapsed / EDGE_FILL_MS;
  return 1 - Math.pow(1 - x, 2);
}

function nodeLitFrac(t: number, tier: number): number {
  if (tier < 0) {
    // Capture: fades in at t=0
    return Math.min(1, Math.max(0, t / NODE_LIGHTUP_MS));
  }
  // Agent nodes: light up the moment their inbound edges fill (end of stage)
  const lightStart = tier * STAGE_MS + EDGE_FILL_MS;
  if (t < lightStart) return 0;
  return Math.min(1, (t - lightStart) / NODE_LIGHTUP_MS);
}

export default function AgentNetworkGraph({
  onNodeClick,
}: {
  results?: AgentResults | null;
  onNodeClick?: (agentId: string) => void;
}) {
  // Wall clock since component mount. Animation is purely scripted —
  // results data is no longer used for timing (it drives card content
  // in the sidebar but the network graph is decoupled).
  const startTsRef = useRef<number>(0);
  const [now, setNow] = useState(0);

  useEffect(() => {
    startTsRef.current = performance.now();
    let raf = 0;
    let running = true;
    function tick() {
      if (!running) return;
      const t = performance.now() - startTsRef.current;
      setNow(t);
      // Keep ticking through the full scripted runtime + a small tail
      // so the final settle frame paints correctly.
      if (t < TOTAL_MS + 500) {
        raf = requestAnimationFrame(tick);
      }
    }
    raf = requestAnimationFrame(tick);
    return () => {
      running = false;
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="border border-outline-variant rounded bg-[#fafafa] p-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <defs>
          <pattern id="grid-bg" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#eee" strokeWidth="0.5" />
          </pattern>
          <filter id="glow"><feGaussianBlur stdDeviation="2" /></filter>
          <marker id="arrow-trace" viewBox="0 0 10 10" refX="8" refY="5"
                  markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill={TRACE} />
          </marker>
          <marker id="arrow-dim" viewBox="0 0 10 10" refX="8" refY="5"
                  markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ccc" />
          </marker>
          <marker id="arrow-active" viewBox="0 0 10 10" refX="8" refY="5"
                  markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill={FETCH_BLUE} />
          </marker>
        </defs>
        <rect width={W} height={H} fill="url(#grid-bg)" />

        {/* Render finished edges first so the dark trace paints UNDER any
            running blue edge that shares the same routing path. */}
        {[...EDGES]
          .map((e, i) => {
            const fill = edgeFillFrac(now, e.tier);
            return { e, i, fill, complete: fill >= 1 };
          })
          .sort((a, b) => Number(b.complete) - Number(a.complete))
          .map(({ e, i, fill, complete }) => {
            const a = NODES_BY_ID[e.from];
            const b = NODES_BY_ID[e.to];
            return (
              <EdgePath
                key={i}
                a={a}
                b={b}
                fillFrac={fill}
                filling={fill > 0 && !complete}
                fullyDone={complete}
              />
            );
          })}

        {NODES.map((n) => {
          const lit = nodeLitFrac(now, n.tier);
          const isCapture = n.id === "__capture__";
          // Lit node: white fill (or blue for capture) with dark stroke.
          // Unlit node: light grey fill with dim stroke.
          const fill = lit > 0
            ? (isCapture ? FETCH_BLUE : NODE_BG)
            : "#f0f0f0";
          const stroke = lit > 0 ? TRACE : "#ccc";
          const clickable = !isCapture && onNodeClick;

          return (
            <g
              key={n.id}
              onClick={clickable ? () => onNodeClick(n.id) : undefined}
              style={clickable ? { cursor: "pointer" } : undefined}
            >
              <rect
                x={n.x - 9}
                y={n.y - 9}
                width={18}
                height={18}
                rx={3}
                fill={fill}
                stroke={stroke}
                strokeWidth={1.5}
              />
              {/* Inner lit dot — only shows on agent nodes once lit */}
              {!isCapture && lit > 0 && (
                <circle cx={n.x} cy={n.y} r={3.5 * lit} fill={FETCH_BLUE} opacity={lit} />
              )}
              {clickable && (
                <rect x={n.x - 14} y={n.y - 14} width={28} height={28}
                      fill="transparent" />
              )}
              <text
                x={n.x}
                y={n.y - 14}
                textAnchor="middle"
                fontFamily="var(--font-geist-sans), system-ui, sans-serif"
                fontSize="7"
                fill={lit > 0 ? "#222" : "#888"}
                fontWeight={500}
                letterSpacing="0.04em"
                style={{ pointerEvents: "none" }}
              >
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// An edge has a permanent dim base. Once it's filling, a blue overlay sized
// by stroke-dasharray draws only `fillFrac` of the path length. When fully
// done it flips to a dark trace color.
function EdgePath({
  a, b, fillFrac, filling, fullyDone,
}: {
  a: Node;
  b: Node;
  fillFrac: number;
  filling: boolean;
  fullyDone: boolean;
}) {
  const pathRef = useRef<SVGPathElement | null>(null);
  const [len, setLen] = useState<number | null>(null);
  const d = tracePath(a, b);

  useEffect(() => {
    if (pathRef.current) {
      setLen(pathRef.current.getTotalLength());
    }
  }, [d]);

  const fillColor = fullyDone ? TRACE : FETCH_BLUE;
  const fillStrokeWidth = fullyDone ? 1.25 : 2;
  const showArrow = fullyDone || fillFrac > 0.95;

  return (
    <g>
      {/* dim base — always rendered */}
      <path
        d={d}
        fill="none"
        stroke="#ddd"
        strokeWidth={1}
        markerEnd={showArrow ? undefined : "url(#arrow-dim)"}
      />
      {/* fill overlay — sized by dasharray. Only render once we have length. */}
      {len != null && fillFrac > 0 && (
        <path
          d={d}
          fill="none"
          stroke={fillColor}
          strokeWidth={fillStrokeWidth}
          strokeDasharray={`${len * fillFrac} ${len}`}
          markerEnd={showArrow ? `url(#arrow-${fullyDone ? "trace" : "active"})` : undefined}
          style={filling ? { filter: "url(#glow)" } : undefined}
        />
      )}
      {/* hidden measuring path so we always have a length even when fillFrac is 0 */}
      {len == null && (
        <path ref={pathRef} d={d} fill="none" stroke="transparent" />
      )}
    </g>
  );
}

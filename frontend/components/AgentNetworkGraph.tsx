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

// How long an inbound edge takes to fill, end-to-end, when an agent is
// "running" (parents satisfied, agent not yet done). This is purely a
// visualization estimate — the real Gemini call takes a variable amount of
// time, so we cap the fill at PROGRESS_CAP until done arrives, then snap.
// Tuned for our pipeline: most Gemini calls + jitter take ~10-25s.
const EDGE_FILL_MS = 18000;
// Cap the synthetic progress so the bar can't reach near-completion before
// the agent actually finishes. Lower cap = more visible "still running" gap.
const PROGRESS_CAP = 0.7;
// On done, smoothly animate from current fillFrac to 1.0 over this many ms
// before flipping the edge to its final dark-trace state, so the blue bar
// finishes its travel rather than vanishing.
const DONE_FINISH_MS = 600;

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

const PARENTS_OF: Record<string, string[]> = (() => {
  const m: Record<string, string[]> = {};
  for (const e of EDGES) {
    (m[e.to] ??= []).push(e.from);
  }
  return m;
})();

// Trim a bit off the destination so the arrowhead doesn't overlap the node
// rectangle (which is 16x16, so half-extent 8 + a few px of breathing room).
const ARROW_INSET = 10;

function tracePath(a: Node, b: Node): string {
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

export default function AgentNetworkGraph({
  results,
  onNodeClick,
}: {
  results: AgentResults | null;
  onNodeClick?: (agentId: string) => void;
}) {
  // For each node: when all its parents finished (so the agent is "running"
  // from the viz's perspective). For capture, this is wall-time of first
  // results. For agents, this is max(parent.doneAt). We use this to drive
  // edge fill animation.
  const startedAtRef = useRef<Record<string, number>>({});
  // For each node: when it actually reported done. Used to snap edge to 100%.
  const doneAtRef = useRef<Record<string, number>>({});
  const [, force] = useState(0);

  // Capture is "started and done" the moment we have any results in flight.
  if (results) {
    if (startedAtRef.current["__capture__"] == null) {
      startedAtRef.current["__capture__"] = performance.now();
      doneAtRef.current["__capture__"] = performance.now();
    }
  }

  // Update started/done timestamps from the latest results.
  if (results) {
    const nowTs = performance.now();
    for (const a of AGENTS) {
      const entry = results.agents[a.id];
      // An agent has "started" once all its parents are done.
      if (startedAtRef.current[a.id] == null) {
        const parents = PARENTS_OF[a.id] ?? [];
        const allParentsDone = parents.every((p) => doneAtRef.current[p] != null);
        if (allParentsDone) {
          // Start time = max(parent doneAt). This way fast agents whose parents
          // just finished start their bar from 0 right now, while agents whose
          // parents finished long ago effectively start "in the past" and their
          // bar is already partially filled.
          const start = parents.reduce(
            (acc, p) => Math.max(acc, doneAtRef.current[p] ?? nowTs),
            nowTs,
          );
          startedAtRef.current[a.id] = start;
        }
      }
      // Mark done when status flips.
      if (entry?.status === "done" && doneAtRef.current[a.id] == null) {
        doneAtRef.current[a.id] = performance.now();
      }
    }
  }

  // RAF loop: keep ticking while any agent is mid-fill (started but not done)
  // OR mid-finish (done but DONE_FINISH_MS hasn't elapsed yet).
  useEffect(() => {
    let raf = 0;
    let running = true;
    function tick() {
      if (!running) return;
      const nowT = performance.now();
      const anyAnimating = AGENTS.some((a) => {
        const s = startedAtRef.current[a.id];
        const d = doneAtRef.current[a.id];
        if (s != null && d == null) return true; // still filling
        if (d != null && nowT - d < DONE_FINISH_MS) return true; // finishing
        return false;
      });
      force((n) => n + 1);
      if (anyAnimating) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => {
      running = false;
      cancelAnimationFrame(raf);
    };
  }, [results]);

  const now = performance.now();

  // Per-agent progress fraction in [0, 1]:
  // - 0 if not yet started (parents still running)
  // - capped at PROGRESS_CAP while running
  // - on done, smoothly ramps from cap → 1.0 over DONE_FINISH_MS
  function progressFor(id: string): number {
    if (id === "__capture__") return 1;
    const d = doneAtRef.current[id];
    const s = startedAtRef.current[id];
    if (d != null) {
      const sinceDone = now - d;
      if (sinceDone >= DONE_FINISH_MS) return 1;
      // Ramp from current running fraction to 1 over DONE_FINISH_MS.
      const runningFrac = s != null
        ? Math.min(PROGRESS_CAP, (d - s) / EDGE_FILL_MS)
        : 0;
      const t = sinceDone / DONE_FINISH_MS;
      return runningFrac + (1 - runningFrac) * t;
    }
    if (s == null) return 0;
    const elapsed = now - s;
    if (elapsed <= 0) return 0;
    return Math.min(PROGRESS_CAP, elapsed / EDGE_FILL_MS);
  }

  // An agent is "fully complete" (edge can flip to dark TRACE) only after the
  // finish animation has played.
  function isFullyComplete(id: string): boolean {
    if (id === "__capture__") return true;
    const d = doneAtRef.current[id];
    return d != null && now - d >= DONE_FINISH_MS;
  }

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

        {/* Render in-flight edges first, fully-complete ones last, so the
            dark trace of finished edges paints over any blue running edge that
            shares the same routing. */}
        {[...EDGES]
          .map((e, i) => ({ e, i, complete: isFullyComplete(e.to) && doneAtRef.current[e.from] != null }))
          .sort((a, b) => Number(a.complete) - Number(b.complete))
          .map(({ e, i, complete }) => {
            const a = NODES_BY_ID[e.from];
            const b = NODES_BY_ID[e.to];
            const childProgress = progressFor(e.to);
            const parentDone = doneAtRef.current[e.from] != null;
            const fillFrac = parentDone ? childProgress : 0;
            const childDone = doneAtRef.current[e.to] != null;
            const filling = parentDone && !childDone && fillFrac > 0;
            return (
              <EdgePath
                key={i}
                a={a}
                b={b}
                fillFrac={fillFrac}
                filling={filling}
                fullyDone={complete}
              />
            );
          })}

        {NODES.map((n) => {
          const done = doneAtRef.current[n.id] != null;
          const fill = done ? (n.id === "__capture__" ? FETCH_BLUE : NODE_BG) : "#f0f0f0";
          const stroke = done ? TRACE : "#ccc";
          const clickable = n.id !== "__capture__" && onNodeClick;
          return (
            <g
              key={n.id}
              onClick={clickable ? () => onNodeClick(n.id) : undefined}
              style={clickable ? { cursor: "pointer" } : undefined}
            >
              <rect x={n.x - 8} y={n.y - 8} width={16} height={16}
                    fill={fill} stroke={stroke} strokeWidth={1.5} />
              {clickable && (
                <rect x={n.x - 12} y={n.y - 12} width={24} height={24}
                      fill="transparent" />
              )}
              <text x={n.x} y={n.y - 12} textAnchor="middle"
                    fontFamily="var(--font-geist-sans), system-ui, sans-serif" fontSize="6.5" fill="#666"
                    style={{ pointerEvents: "none" }}>
                {n.label.slice(0, 14)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// An edge with a dim base and a colored "fill" overlay sized by stroke-dasharray
// to render only `fillFrac` of the path's length. We measure path length via a
// ref since the polyline geometry varies per edge.
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

  // Color: fully-done edges are dark trace; in-flight edges are blue.
  const fillColor = fullyDone ? TRACE : FETCH_BLUE;
  const fillStrokeWidth = fullyDone ? 1 : 2;
  const showArrow = fullyDone || fillFrac >= PROGRESS_CAP - 0.001;

  return (
    <g>
      {/* dim base — always rendered */}
      <path
        d={d}
        fill="none"
        stroke="#ccc"
        strokeWidth={1}
        markerEnd={showArrow ? undefined : "url(#arrow-dim)"}
      />
      {/* fill overlay — sized by dasharray. Only render once we have length. */}
      {len != null && fillFrac > 0 && (
        <path
          ref={pathRef}
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

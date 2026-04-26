"use client";
import { useEffect, useState } from "react";
import { AGENTS, AGENTS_BY_ID, CATEGORIES } from "@/lib/agentManifest";
import { asiOneAgentChatUrl } from "@/lib/agentAddresses";
import { fetchAgentResults, type AgentEntry, type AgentResults } from "@/lib/agentResults";
import { renderAgentCard } from "./agent-cards";
import AgentNetworkGraph from "./AgentNetworkGraph";
import AgentDetailModal from "./AgentDetailModal";
import ExportPanel from "./ExportPanel";

export const AGENT_SIDEBAR_WIDTH = 440;

export default function AgentSidebar({
  worldId,
  worldTitle,
  thumbnailUrl,
  open,
  onOpenChange,
}: {
  worldId: string;
  worldTitle: string;
  thumbnailUrl?: string;
  open: boolean;
  onOpenChange: (next: boolean) => void;
}) {
  const [results, setResults] = useState<AgentResults | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  // All sections collapsed by default — user expands what they want to see.
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Poll the agents.json file directly every 2s. Stop polling once we have all
  // 19 agents reported. We don't trust /api/analyze/status alone because the
  // bridge state can be transient (e.g. server restart loses _analyze_state),
  // and the file is the canonical source.
  useEffect(() => {
    let cancelled = false;
    let interval: any;
    async function tick() {
      const r = await fetchAgentResults(worldId).catch(() => null);
      if (cancelled) return;
      if (r) {
        setResults(r);
        if (Object.keys(r.agents).length >= AGENTS.length) {
          clearInterval(interval);
        }
      }
    }
    tick();
    interval = setInterval(tick, 2000);
    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [worldId]);

  const doneCount = results ? Object.values(results.agents).filter((e) => e.status === "done").length : 0;
  const selectedEntry: AgentEntry | undefined = selectedAgentId ? results?.agents[selectedAgentId] : undefined;
  const selectedDef = selectedAgentId ? AGENTS_BY_ID[selectedAgentId] : undefined;

  return (
    <>
      <button
        onPointerDown={(e) => {
          // Stop the canvas's pointerlock listener from firing on this click.
          e.stopPropagation();
          if (document.pointerLockElement) document.exitPointerLock();
        }}
        onClick={(e) => {
          e.stopPropagation();
          onOpenChange(!open);
        }}
        className="fixed top-4 right-4 z-30 text-xs font-sans bg-white text-on-surface px-3 py-1.5 rounded shadow-soft border border-outline-variant hover:bg-zinc-50"
        style={open ? { right: AGENT_SIDEBAR_WIDTH + 16 } : undefined}
      >
        {open ? "× Close" : "Agents"}
      </button>
      <div
        className={
          "fixed top-0 right-0 h-full bg-white border-l border-outline-variant shadow-2xl z-20 overflow-y-auto transition-transform duration-300 " +
          (open ? "translate-x-0" : "translate-x-full")
        }
        style={{ width: AGENT_SIDEBAR_WIDTH }}
      >
        <div className="p-6 space-y-6">
          <div>
            <h2 className="label-caps tracking-[0.18em] text-base">AGENT SWARM</h2>
            <div className="text-xs text-on-surface-variant mt-1 font-sans">
              {results ? `${doneCount} / ${AGENTS.length} done` : "running…"}
            </div>
          </div>

          {open && (
            <AgentNetworkGraph
              results={results}
              onNodeClick={(id) => {
                const def = AGENTS_BY_ID[id];
                if (!def) return;
                const entry = results?.agents[id];
                // Always open an ASI:One chat targeted at this agent. If the
                // agent has finished and we have its output, prefill the
                // chat with that analysis; otherwise send a generic kickoff
                // so the user still lands in a live conversation.
                const output =
                  entry?.status === "done" ? entry.output : undefined;
                const url = asiOneAgentChatUrl(id, def.label, output);
                if (url) window.open(url, "_blank", "noopener,noreferrer");
              }}
            />
          )}

          <section>
            <button
              type="button"
              onClick={() =>
                setExpanded((prev) => ({ ...prev, __export: !prev.__export }))
              }
              className="w-full flex items-center justify-between mb-3 group"
            >
              <div className="flex items-center gap-2">
                <span
                  className="text-on-surface-variant text-xs font-sans transition-transform"
                  style={{ transform: expanded.__export ? "rotate(90deg)" : "none" }}
                >
                  ▶
                </span>
                <h3 className="label-caps text-on-surface-variant text-xs">EXPORT</h3>
              </div>
              <span className="text-[10px] font-sans text-on-surface-variant">
                {results ? "ready" : "—"}
              </span>
            </button>
            {expanded.__export && (
              <ExportPanel
                results={results}
                worldId={worldId}
                worldTitle={worldTitle}
                thumbnailUrl={thumbnailUrl}
              />
            )}
          </section>

          {CATEGORIES.map((cat) => {
            const agentsInCat = AGENTS.filter((a) => a.category === cat.name);
            const catDone = agentsInCat.filter(
              (a) => results?.agents[a.id]?.status === "done",
            ).length;
            const isOpen = !!expanded[cat.name];
            return (
              <section key={cat.name}>
                <button
                  type="button"
                  onClick={() =>
                    setExpanded((prev) => ({ ...prev, [cat.name]: !prev[cat.name] }))
                  }
                  className="w-full flex items-center justify-between mb-3 group"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="text-on-surface-variant text-xs font-sans transition-transform"
                      style={{ transform: isOpen ? "rotate(90deg)" : "none" }}
                    >
                      ▶
                    </span>
                    <h3 className="label-caps text-on-surface-variant text-xs">{cat.name}</h3>
                  </div>
                  <span className="text-[10px] font-sans text-on-surface-variant">
                    {catDone} / {agentsInCat.length}
                  </span>
                </button>
                {isOpen && (
                  <div className="space-y-3">
                    {agentsInCat.map((a) => {
                      const entry = results?.agents[a.id];
                      return (
                        <button
                          key={a.id}
                          onClick={() => setSelectedAgentId(a.id)}
                          className="w-full text-left border border-outline-variant rounded p-3 bg-surface hover:bg-zinc-50 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="text-sm font-medium">{a.label}</div>
                            <StatusBadge status={entry?.status ?? "pending"} />
                          </div>
                          {entry ? renderAgentCard(entry) : <PendingPlaceholder />}
                        </button>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      </div>

      {selectedAgentId && selectedDef && (
        <AgentDetailModal
          agentDef={selectedDef}
          entry={selectedEntry}
          onClose={() => setSelectedAgentId(null)}
        />
      )}
    </>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "done" ? "bg-green-50 text-green-700 border-green-200" :
    status === "error" ? "bg-red-50 text-red-700 border-red-200" :
    status === "skipped" ? "bg-zinc-50 text-zinc-500 border-zinc-200" :
    "bg-zinc-100 text-zinc-500 border-zinc-200";
  return <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${cls}`}>{status}</span>;
}

function PendingPlaceholder() {
  return <div className="h-4 bg-surface-container rounded animate-pulse" />;
}

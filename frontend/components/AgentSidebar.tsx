"use client";
import { useEffect, useState } from "react";
import { AGENTS, CATEGORIES } from "@/lib/agentManifest";
import { fetchAgentResults, pollAnalyzeStatus, type AgentResults } from "@/lib/agentResults";
import { renderAgentCard } from "./agent-cards";
import AgentNetworkGraph from "./AgentNetworkGraph";

export default function AgentSidebar({ worldId }: { worldId: string }) {
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<AgentResults | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let interval: any;
    async function load() {
      setLoading(true);
      const r = await fetchAgentResults(worldId).catch(() => null);
      if (cancelled) return;
      if (r) {
        setResults(r);
        setLoading(false);
        return;
      }
      interval = setInterval(async () => {
        const state = await pollAnalyzeStatus(worldId).catch(() => "unknown");
        if (state === "done") {
          const r2 = await fetchAgentResults(worldId).catch(() => null);
          if (r2) {
            setResults(r2);
            setLoading(false);
            clearInterval(interval);
          }
        }
      }, 2000);
    }
    load();
    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [worldId]);

  return (
    <>
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed top-4 right-4 z-20 text-xs font-mono bg-white/90 text-on-surface px-3 py-1.5 rounded shadow-soft border border-outline-variant hover:bg-white"
      >
        {open ? "× close" : "agents"}
      </button>
      <div
        className={
          "fixed top-0 right-0 h-full w-[420px] bg-white/98 border-l border-outline-variant z-10 overflow-y-auto transition-transform duration-300 " +
          (open ? "translate-x-0" : "translate-x-full")
        }
      >
        <div className="p-6 space-y-6">
          <div>
            <h2 className="label-caps tracking-[0.18em] text-base">AGENT SWARM</h2>
            <div className="text-xs text-on-surface-variant mt-1 font-mono">
              {results ? `${Object.keys(results.agents).length} / 19` : loading ? "running…" : "queued"}
            </div>
          </div>

          {open && <AgentNetworkGraph results={results} />}

          {CATEGORIES.map((cat) => {
            const agentsInCat = AGENTS.filter((a) => a.category === cat.name);
            return (
              <section key={cat.name}>
                <h3 className="label-caps text-on-surface-variant text-xs mb-3">{cat.name}</h3>
                <div className="space-y-3">
                  {agentsInCat.map((a) => {
                    const entry = results?.agents[a.id];
                    return (
                      <div key={a.id} className="border border-outline-variant rounded p-3 bg-surface">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium">{a.label}</div>
                          <StatusBadge status={entry?.status ?? "pending"} />
                        </div>
                        {entry ? renderAgentCard(entry) : <PendingPlaceholder />}
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
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

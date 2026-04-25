"use client";

import type { AgentWorldSnapshot } from "@/lib/agentWorld";

export default function AgentDetailPanel({
  snapshot,
  onClose,
}: {
  snapshot: AgentWorldSnapshot;
  onClose: () => void;
}) {
  return (
    <aside className="fixed top-4 right-4 z-30 w-[360px] max-w-[calc(100vw-2rem)] rounded-lg border border-zinc-700 bg-zinc-950/95 p-4 text-zinc-200 shadow-xl backdrop-blur">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-cyan-300">{snapshot.name}</h2>
          <p className="text-xs text-zinc-400">{snapshot.description}</p>
        </div>
        <button onClick={onClose} className="rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-300">
          close
        </button>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
        <Stat label="State" value={snapshot.visualState} />
        <Stat label="Status" value={snapshot.status} />
        <Stat label="Phase" value={snapshot.phase.replace("-", " ")} />
        <Stat label="Progress" value={snapshot.progress !== undefined ? `${snapshot.progress}%` : "n/a"} />
      </div>

      <section className="mb-3 rounded border border-zinc-800 bg-zinc-900/60 p-3">
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-400">Current Activity</h3>
        <p className="text-sm">{snapshot.activityLabel}</p>
        <p className="mt-1 text-xs text-zinc-400">{snapshot.stateText}</p>
        {snapshot.error ? <p className="mt-2 text-xs text-red-300">Error: {snapshot.error}</p> : null}
      </section>

      <section className="mb-2 rounded border border-zinc-800 bg-zinc-900/60 p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">Recent Events</h3>
        <div className="max-h-36 space-y-2 overflow-y-auto pr-1">
          {snapshot.recentEvents.length === 0 ? (
            <p className="text-xs text-zinc-500">No events yet.</p>
          ) : (
            snapshot.recentEvents.map((evt) => (
              <div key={evt.id} className="rounded border border-zinc-800 p-2">
                <div className="text-[11px] text-zinc-400">{new Date(evt.ts).toLocaleTimeString()}</div>
                <div className="text-xs text-zinc-200">{evt.event.state}</div>
                <div className="text-xs text-zinc-400">{evt.event.message || "status update"}</div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="rounded border border-zinc-800 bg-zinc-900/60 p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">Metadata</h3>
        <p className="text-xs text-zinc-400">
          {snapshot.metadata && Object.keys(snapshot.metadata).length > 0
            ? JSON.stringify(snapshot.metadata)
            : "No additional metadata available."}
        </p>
      </section>
    </aside>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-zinc-800 bg-zinc-900/70 p-2">
      <div className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="text-xs text-zinc-200">{value}</div>
    </div>
  );
}

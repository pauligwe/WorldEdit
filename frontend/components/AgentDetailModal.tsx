"use client";
import { useEffect, useState } from "react";
import type { AgentDef } from "@/lib/agentManifest";
import type { AgentEntry } from "@/lib/agentResults";

type View = "narrative" | "json";

export default function AgentDetailModal({
  agentDef,
  entry,
  onClose,
}: {
  agentDef: AgentDef;
  entry?: AgentEntry;
  onClose: () => void;
}) {
  const [view, setView] = useState<View>("narrative");

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const status = entry?.status ?? "pending";
  const narrative = (entry?.output as any)?.narrative;
  const structured = entry?.output;

  return (
    <div
      className="fixed inset-0 z-40 bg-black/50 flex items-center justify-center p-6"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-outline-variant flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-on-surface-variant">
              {agentDef.category} · Tier {agentDef.tier}
            </div>
            <h2 className="text-lg font-medium mt-0.5">{agentDef.label}</h2>
          </div>
          <div className="flex items-center gap-3">
            <StatusPill status={status} />
            <button
              onClick={onClose}
              className="text-on-surface-variant hover:text-on-surface text-2xl leading-none"
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>

        <div className="px-6 py-3 border-b border-outline-variant flex items-center gap-2">
          <ToggleButton active={view === "narrative"} onClick={() => setView("narrative")}>
            Natural language
          </ToggleButton>
          <ToggleButton active={view === "json"} onClick={() => setView("json")}>
            Structured (JSON)
          </ToggleButton>
          {entry?.duration_ms != null && (
            <div className="ml-auto text-xs font-sans text-on-surface-variant">
              {entry.duration_ms}ms
            </div>
          )}
        </div>

        <div className="px-6 py-5 overflow-y-auto flex-1">
          {status === "pending" && (
            <p className="text-sm text-on-surface-variant italic">Agent still running…</p>
          )}
          {status === "skipped" && (
            <p className="text-sm text-on-surface-variant italic">
              Skipped — {entry?.reason ?? "upstream failed"}
            </p>
          )}
          {status === "error" && (
            <p className="text-sm text-red-600">Error: {entry?.error_message ?? "unknown"}</p>
          )}
          {status === "done" && view === "narrative" && (
            typeof narrative === "string" && narrative.trim().length > 0 ? (
              <p className="text-base leading-relaxed text-on-surface">{narrative}</p>
            ) : (
              <p className="text-sm text-on-surface-variant italic">No narrative available.</p>
            )
          )}
          {status === "done" && view === "json" && (
            <pre className="text-xs font-mono whitespace-pre-wrap break-words text-on-surface bg-zinc-50 p-4 rounded border border-outline-variant">
              {JSON.stringify(structured, null, 2)}
            </pre>
          )}
        </div>

        {agentDef.dependencies.length > 0 && (
          <div className="px-6 py-3 border-t border-outline-variant text-xs text-on-surface-variant">
            <span className="font-medium">Inputs:</span>{" "}
            {agentDef.dependencies.join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const cls =
    status === "done" ? "bg-green-50 text-green-700 border-green-200" :
    status === "error" ? "bg-red-50 text-red-700 border-red-200" :
    status === "skipped" ? "bg-zinc-50 text-zinc-500 border-zinc-200" :
    "bg-zinc-100 text-zinc-500 border-zinc-200";
  return (
    <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${cls}`}>
      {status}
    </span>
  );
}

function ToggleButton({
  active, onClick, children,
}: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={
        "text-xs font-medium px-3 py-1 rounded border transition-colors " +
        (active
          ? "bg-primary text-on-primary border-primary"
          : "bg-white text-on-surface border-outline-variant hover:bg-zinc-50")
      }
    >
      {children}
    </button>
  );
}

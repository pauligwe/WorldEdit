import type { AgentEntry } from "@/lib/agentResults";

export default function TextCard({ entry }: { entry: AgentEntry }) {
  if (entry.status !== "done") return <FallbackCard entry={entry} />;
  const out = entry.output ?? {};
  if (typeof out.summary === "string") {
    return (
      <div className="space-y-2">
        <p className="text-sm leading-relaxed text-on-surface">{out.summary}</p>
        {Array.isArray(out.tags) && out.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {out.tags.map((t: string) => (
              <span key={t} className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-surface-container border border-outline-variant text-on-surface-variant">{t}</span>
            ))}
          </div>
        )}
      </div>
    );
  }
  return (
    <pre className="text-xs font-mono whitespace-pre-wrap break-words text-on-surface-variant">
      {JSON.stringify(out, null, 2)}
    </pre>
  );
}

export function FallbackCard({ entry }: { entry: AgentEntry }) {
  if (entry.status === "skipped") {
    return <p className="text-xs text-on-surface-variant italic">Skipped — {entry.reason ?? "upstream failed"}</p>;
  }
  return <p className="text-xs text-red-600">Error: {entry.error_message ?? "unknown"}</p>;
}

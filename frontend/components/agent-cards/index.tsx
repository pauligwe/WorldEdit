import type { AgentEntry } from "@/lib/agentResults";

// Every agent's structured output ends with a `narrative: str` field — a 1-2
// sentence prose summary the agent writes about its own findings. We display
// that uniformly so users get readable text instead of JSON. Structured data
// is preserved server-side for downstream agents but not shown to the user.
export function renderAgentCard(entry: AgentEntry) {
  if (entry.status === "skipped") {
    return <p className="text-xs text-on-surface-variant italic">Skipped — {entry.reason ?? "upstream failed"}</p>;
  }
  if (entry.status === "error") {
    return <p className="text-xs text-red-600">Error: {entry.error_message ?? "unknown"}</p>;
  }
  const narrative = (entry.output as any)?.narrative;
  if (typeof narrative === "string" && narrative.trim().length > 0) {
    return <p className="text-sm leading-relaxed text-on-surface">{narrative}</p>;
  }
  return <p className="text-xs text-on-surface-variant italic">No summary available.</p>;
}

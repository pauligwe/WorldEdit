export type AgentStatus = "done" | "error" | "skipped";

export interface AgentEntry {
  status: AgentStatus;
  duration_ms: number;
  display: "text" | "list" | "swatches" | "map" | "products" | "thumbnails";
  output?: any;
  error_message?: string;
  reason?: string;
}

export interface AgentResults {
  world_id: string;
  generated_at: string;
  schema_version: number;
  agents: Record<string, AgentEntry>;
}

export async function fetchAgentResults(worldId: string): Promise<AgentResults | null> {
  const url = `/worlds/${worldId}.agents.json`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`agents.json fetch failed: ${res.status}`);
  return await res.json();
}

export async function pollAnalyzeStatus(
  worldId: string,
  apiBase: string = "http://localhost:8000",
): Promise<"queued" | "running" | "done" | "error" | "unknown"> {
  const res = await fetch(`${apiBase}/api/analyze/${worldId}/status`);
  if (!res.ok) return "unknown";
  const j = await res.json();
  return j.state;
}

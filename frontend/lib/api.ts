import type { WorldSpec } from "./worldSpec";

const BRIDGE = process.env.NEXT_PUBLIC_BRIDGE_URL ?? "http://localhost:8000";

export async function generate(prompt: string): Promise<{ worldId: string }> {
  const r = await fetch(`${BRIDGE}/api/generate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!r.ok) throw new Error(`generate: ${r.status}`);
  return r.json();
}

export async function edit(worldId: string, edit: string): Promise<{ worldId: string }> {
  const r = await fetch(`${BRIDGE}/api/edit`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ worldId, edit }),
  });
  if (!r.ok) throw new Error(`edit: ${r.status}`);
  return r.json();
}

export async function getWorld(worldId: string): Promise<WorldSpec> {
  const r = await fetch(`${BRIDGE}/api/world/${worldId}`);
  if (!r.ok) throw new Error(`world: ${r.status}`);
  return r.json();
}

export type StatusEvent = { agent: string; state: "running" | "done" | "error"; message: string; data?: any };

export function openStatusSocket(worldId: string, onEvent: (e: StatusEvent) => void, onClose?: () => void): () => void {
  const wsUrl = BRIDGE.replace(/^http/, "ws") + `/ws/build/${worldId}`;
  let ws: WebSocket | null = new WebSocket(wsUrl);
  let closed = false;
  ws.onmessage = (m) => {
    try { onEvent(JSON.parse(m.data)); } catch {}
  };
  ws.onclose = () => { if (!closed) onClose?.(); };
  ws.onerror = () => { if (!closed) onClose?.(); };
  return () => { closed = true; ws?.close(); ws = null; };
}

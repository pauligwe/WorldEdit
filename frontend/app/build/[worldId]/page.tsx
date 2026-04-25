"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import AgentActivityPanel, { AgentState } from "@/components/AgentActivityPanel";
import { openStatusSocket, getWorld } from "@/lib/api";
import type { WorldSpec } from "@/lib/worldSpec";

const World3D = dynamic(() => import("@/components/World3D"), { ssr: false });

export default function BuildPage() {
  const params = useParams<{ worldId: string }>();
  const worldId = params.worldId;
  const [states, setStates] = useState<Record<string, AgentState>>({});
  const [messages, setMessages] = useState<Record<string, string>>({});
  const [spec, setSpec] = useState<WorldSpec | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let close: (() => void) | null = null;
    (async () => {
      try {
        const existing = await getWorld(worldId);
        if (cancelled) return;
        if (existing && existing.cost && existing.navigation) {
          setSpec(existing);
          return;
        }
      } catch {}
      if (cancelled) return;
      close = openStatusSocket(worldId, async (e) => {
        if (e.agent === "__final__") {
          const ws = await getWorld(worldId);
          setSpec(ws);
          return;
        }
        if (e.agent === "__pipeline__" && e.state === "error") {
          setError(e.message);
          return;
        }
        if (e.agent.startsWith("__")) return;
        setStates((s) => ({ ...s, [e.agent]: e.state as AgentState }));
        if (e.message) setMessages((m) => ({ ...m, [e.agent]: e.message }));
      });
    })();
    return () => { cancelled = true; close?.(); };
  }, [worldId]);

  if (error) {
    return (
      <main className="min-h-screen bg-black text-red-300 flex flex-col items-center justify-center p-8">
        <h1 className="text-2xl font-bold mb-2">Generation failed</h1>
        <pre className="text-sm whitespace-pre-wrap">{error}</pre>
      </main>
    );
  }

  if (!spec) {
    return (
      <main className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8">
        <h1 className="text-3xl font-black mb-8 bg-gradient-to-r from-cyan-300 to-violet-400 bg-clip-text text-transparent">building...</h1>
        <AgentActivityPanel states={states} messages={messages} />
      </main>
    );
  }

  return <World3D spec={spec} />;
}

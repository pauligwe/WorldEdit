"use client";
import type { WorldSpec } from "@/lib/worldSpec";
import type { BuildMode } from "@/lib/agentWorld";

export default function StatusBar({
  spec,
  mode,
  simRunning,
  onStartSimulation,
  onExitSimulation,
}: {
  spec: WorldSpec;
  mode: BuildMode;
  simRunning: boolean;
  onStartSimulation: () => void;
  onExitSimulation: () => void;
}) {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 flex flex-wrap items-center justify-between gap-3 bg-black/70 p-2 text-xs font-mono text-zinc-300">
      <span>{spec.intent?.style} · {spec.intent?.floors} floors · {spec.furniture.length} items</span>
      <span>${(spec.cost?.total ?? 0).toFixed(0)}</span>
      <div className="flex items-center gap-2">
        {mode === "simulated" ? (
          <>
            <span className="rounded border border-violet-400 bg-violet-900/60 px-2 py-1 text-violet-200">SIMULATED MODE</span>
            <button onClick={onExitSimulation} className="rounded border border-zinc-600 px-2 py-1 hover:border-zinc-400">
              Exit simulation
            </button>
          </>
        ) : (
          <button onClick={onStartSimulation} className="rounded border border-violet-500 bg-violet-950 px-2 py-1 text-violet-200 hover:bg-violet-900">
            {simRunning ? "Restart simulation" : "Simulate"}
          </button>
        )}
        <span>WASD · mouse · click furniture · T chat</span>
      </div>
    </div>
  );
}

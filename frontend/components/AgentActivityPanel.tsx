"use client";

const AGENTS = [
  { name: "intent_parser", row: 1 },
  { name: "blueprint_architect", row: 2 },
  { name: "compliance_critic", row: 3 },
  { name: "geometry_builder", row: 4 },
  { name: "lighting_designer", row: 4 },
  { name: "material_stylist", row: 4 },
  { name: "furniture_planner", row: 5 },
  { name: "placement_validator", row: 6 },
  { name: "product_scout", row: 7 },
  { name: "style_matcher", row: 8 },
  { name: "pricing_estimator", row: 9 },
  { name: "navigation_planner", row: 10 },
  { name: "chat_edit_coordinator", row: 11 },
] as const;

export type AgentState = "idle" | "running" | "done" | "error";

const STATE_STYLES: Record<AgentState, string> = {
  idle: "bg-zinc-900 border-zinc-700 text-zinc-500",
  running: "bg-cyan-950 border-cyan-400 text-cyan-300 animate-pulse",
  done: "bg-emerald-950 border-emerald-400 text-emerald-300",
  error: "bg-red-950 border-red-400 text-red-300",
};

interface Props {
  states: Record<string, AgentState>;
  messages: Record<string, string>;
}

export default function AgentActivityPanel({ states, messages }: Props) {
  const rows: Record<number, typeof AGENTS[number][]> = {};
  for (const a of AGENTS) (rows[a.row] ??= []).push(a);

  return (
    <div className="flex flex-col gap-2 items-center">
      {Object.keys(rows).map(Number).sort((a, b) => a - b).map((row) => (
        <div key={row} className="flex flex-row gap-2">
          {rows[row].map((a) => {
            const s: AgentState = states[a.name] ?? "idle";
            return (
              <div
                key={a.name}
                className={`px-3 py-2 rounded border text-sm font-mono w-56 ${STATE_STYLES[s]}`}
              >
                <div className="font-bold">{a.name}</div>
                <div className="text-xs opacity-70 truncate">{messages[a.name] ?? s}</div>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

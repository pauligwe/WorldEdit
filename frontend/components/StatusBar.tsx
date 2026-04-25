"use client";
import type { WorldSpec } from "@/lib/worldSpec";

export default function StatusBar({ spec }: { spec: WorldSpec }) {
  return (
    <div className="fixed bottom-0 left-0 right-0 p-2 bg-black/60 text-zinc-300 text-xs flex justify-between font-sans">
      <span>{spec.intent?.style} · {spec.intent?.floors} floors · {spec.furniture.length} items</span>
      <span>${(spec.cost?.total ?? 0).toFixed(0)}</span>
      <span>WASD · mouse · click furniture · T chat</span>
    </div>
  );
}

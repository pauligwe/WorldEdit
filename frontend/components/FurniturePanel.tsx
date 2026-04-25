"use client";
import { useState } from "react";
import type { WorldSpec, FurnitureItem } from "@/lib/worldSpec";
import { selectProduct, proxiedImage } from "@/lib/api";

export default function FurniturePanel({ spec, item, onClose }: { spec: WorldSpec; item: FurnitureItem; onClose: () => void; }) {
  const [selectedId, setSelectedId] = useState(item.selectedProductId);
  const alts = item.alternates.map((id) => ({ id, p: spec.products[id] })).filter((x) => x.p);

  return (
    <div className="fixed top-0 right-0 h-full w-96 max-w-full bg-zinc-950 border-l border-zinc-800 p-4 flex flex-col gap-3 z-20 overflow-y-auto overflow-x-hidden box-border">
      <div className="flex justify-between items-center gap-2">
        <h2 className="font-bold text-violet-300 truncate">{item.type}</h2>
        <button onClick={onClose} className="text-zinc-400 shrink-0">close</button>
      </div>
      <p className="text-zinc-400 text-xs">{alts.length} options</p>
      {alts.map(({ id, p }) => (
        <button
          key={id}
          onClick={async () => { setSelectedId(id); await selectProduct(spec.worldId, item.id, id); item.selectedProductId = id; }}
          className={`block w-full text-left bg-zinc-900 border rounded p-2 hover:border-violet-400 overflow-hidden ${selectedId === id ? "border-violet-400" : "border-zinc-800"}`}
        >
          <img
            src={p.imageUrl ? proxiedImage(p.imageUrl, p.url) : ""}
            alt=""
            className="block w-full h-32 object-cover rounded mb-2 bg-zinc-800"
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
          />
          <div className="font-bold text-sm break-words">{p.name}</div>
          <div className="text-zinc-400 text-xs truncate">{p.vendor} · {p.price ? `$${p.price}` : "—"}</div>
          {p.url && <a href={p.url} target="_blank" rel="noopener" className="text-cyan-400 text-xs">View</a>}
        </button>
      ))}
    </div>
  );
}

"use client";
import { useState } from "react";
import { edit } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ChatPanel({ open, onClose, worldId }: { open: boolean; onClose: () => void; worldId: string; }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  if (!open) return null;
  return (
    <div className="fixed top-0 left-0 h-full w-96 bg-zinc-950 border-r border-zinc-800 p-4 flex flex-col gap-3 z-20">
      <div className="flex justify-between items-center">
        <h2 className="font-bold text-cyan-300">Edit</h2>
        <button onClick={onClose} className="text-zinc-400">close</button>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="flex-1 bg-zinc-900 border border-zinc-700 rounded p-2 text-white text-sm"
        placeholder="e.g. make the kitchen bigger and add a fireplace"
        disabled={busy}
      />
      <button
        disabled={busy || !text.trim()}
        onClick={async () => {
          setBusy(true);
          try {
            const { worldId: newId } = await edit(worldId, text);
            router.push(`/build/${newId}`);
          } finally { setBusy(false); }
        }}
        className="bg-cyan-500 disabled:bg-zinc-700 text-black font-bold rounded p-2"
      >Apply</button>
    </div>
  );
}

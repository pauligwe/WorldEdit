"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { generate } from "@/lib/api";

export default function PromptForm() {
  const [prompt, setPrompt] = useState("A two-story modern beach house with an open kitchen, three bedrooms, and a reading nook");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const { worldId } = await generate(prompt);
      router.push(`/build/${worldId}`);
    } catch (err) {
      alert(`Error: ${err}`);
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="w-full max-w-2xl flex flex-col gap-4">
      <textarea
        className="w-full h-32 p-4 rounded-lg bg-zinc-900 border border-zinc-700 text-white text-lg focus:outline-none focus:border-cyan-400"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        disabled={busy}
        placeholder="Describe a building..."
      />
      <button
        type="submit"
        disabled={busy || prompt.trim().length === 0}
        className="px-6 py-3 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:bg-zinc-700 text-black font-bold text-lg transition"
      >
        {busy ? "Building..." : "Generate"}
      </button>
    </form>
  );
}

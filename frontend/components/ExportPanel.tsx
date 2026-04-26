"use client";
import { useMemo } from "react";
import type { AgentResults } from "@/lib/agentResults";
import { buildWorldBibleMarkdown } from "@/lib/exports/worldBible";
import { buildPaletteAse } from "@/lib/exports/paletteAse";
import { buildPropsCsv } from "@/lib/exports/propsCsv";

interface Props {
  results: AgentResults | null;
  worldId: string;
  worldTitle: string;
  thumbnailUrl?: string;
}

export default function ExportPanel({ results, worldId, worldTitle, thumbnailUrl }: Props) {
  const palette: string[] = useMemo(() => {
    const out = (results?.agents.mood_palette?.output as any)?.palette;
    return Array.isArray(out) ? out.filter((x) => typeof x === "string") : [];
  }, [results]);

  const propItems: any[] = useMemo(() => {
    const items = (results?.agents.prop_shopping?.output as any)?.items;
    return Array.isArray(items) ? items : [];
  }, [results]);

  if (!results) {
    return (
      <p className="text-xs text-on-surface-variant italic">
        Exports become available once the swarm finishes analyzing this world.
      </p>
    );
  }

  function downloadBible() {
    const md = buildWorldBibleMarkdown(results!, { worldTitle, thumbnailUrl });
    saveBlob(new Blob([md], { type: "text/markdown;charset=utf-8" }), `${worldId}-world-bible.md`);
  }

  function downloadJson() {
    const json = JSON.stringify(results, null, 2);
    saveBlob(new Blob([json], { type: "application/json" }), `${worldId}.json`);
  }

  function downloadAse() {
    if (palette.length === 0) return;
    const bytes = buildPaletteAse(palette, `${worldTitle} — Conjure`);
    const ab = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
    saveBlob(new Blob([ab], { type: "application/octet-stream" }), `${worldId}-palette.ase`);
  }

  function downloadCsv() {
    if (propItems.length === 0) return;
    const csv = buildPropsCsv(propItems);
    saveBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), `${worldId}-props.csv`);
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-on-surface-variant leading-relaxed">
        One-click export of everything the swarm produced — for game devs, filmmakers,
        writers, designers, or any agent that needs grounded context about this place.
      </p>
      <div className="grid grid-cols-1 gap-2">
        <ExportButton
          title="World Bible"
          subtitle="Readable Markdown — palette, props, story, shots, hazards"
          ext=".md"
          onClick={downloadBible}
        />
        <ExportButton
          title="Structured Output"
          subtitle="Full agent results as JSON — for downstream tools or other agents"
          ext=".json"
          onClick={downloadJson}
        />
        <ExportButton
          title="Color Palette"
          subtitle={
            palette.length > 0
              ? "Adobe Swatch Exchange — opens in Photoshop, Illustrator, Affinity"
              : "Waiting on Mood & Palette agent"
          }
          ext=".ase"
          onClick={downloadAse}
          disabled={palette.length === 0}
          accent={palette.slice(0, 5)}
        />
        <ExportButton
          title="Prop Shopping List"
          subtitle={
            propItems.length > 0
              ? `${propItems.length} props with vendor links and price estimates`
              : "Waiting on Prop Shopping agent"
          }
          ext=".csv"
          onClick={downloadCsv}
          disabled={propItems.length === 0}
        />
      </div>
    </div>
  );
}

function ExportButton({
  title,
  subtitle,
  ext,
  onClick,
  disabled,
  accent,
}: {
  title: string;
  subtitle: string;
  ext: string;
  onClick: () => void;
  disabled?: boolean;
  accent?: string[];
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="w-full text-left border border-outline-variant rounded p-3 bg-surface hover:bg-zinc-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-medium text-on-surface truncate">{title}</div>
          <div className="text-[11px] text-on-surface-variant mt-0.5 leading-snug">{subtitle}</div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {accent && accent.length > 0 && (
            <div className="flex gap-0.5">
              {accent.map((hex, i) => (
                <span
                  key={i}
                  className="w-3 h-3 rounded-sm border border-outline-variant"
                  style={{ background: hex }}
                />
              ))}
            </div>
          )}
          <span className="text-[10px] font-mono uppercase tracking-wider text-on-surface-variant px-1.5 py-0.5 rounded border border-outline-variant">
            {ext}
          </span>
        </div>
      </div>
    </button>
  );
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

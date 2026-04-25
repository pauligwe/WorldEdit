"use client";
import { useRef, useState } from "react";

export default function PromptBar() {
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || submitting) return;
    // No real submit yet — simulate a brief working state, then reset.
    setSubmitting(true);
    setTimeout(() => setSubmitting(false), 1800);
  }

  return (
    <form
      onSubmit={onSubmit}
      className="w-full max-w-3xl bg-surface-lowest border border-outline-variant rounded-xl shadow-soft flex items-center gap-3 px-4 py-3"
    >
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        className="shrink-0 w-9 h-9 rounded grid place-items-center text-on-surface-variant hover:bg-surface-low"
        aria-label="Attach image"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="9" cy="9" r="2" />
          <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
        </svg>
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => setImage(e.target.files?.[0] ?? null)}
      />

      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe a world to step into…"
        className="flex-1 bg-transparent outline-none text-base placeholder:text-outline"
        disabled={submitting}
      />

      {image && (
        <span className="text-xs text-on-surface-variant truncate max-w-[10rem]">
          {image.name}
        </span>
      )}

      <button
        type="submit"
        disabled={!prompt.trim() || submitting}
        className="shrink-0 w-10 h-10 rounded bg-primary text-on-primary grid place-items-center disabled:opacity-30 hover:opacity-90 transition-opacity"
        aria-label="Submit"
      >
        {submitting ? (
          <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="9" opacity="0.25" />
            <path d="M21 12a9 9 0 0 1-9 9" />
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 19V5" />
            <path d="m5 12 7-7 7 7" />
          </svg>
        )}
      </button>
    </form>
  );
}

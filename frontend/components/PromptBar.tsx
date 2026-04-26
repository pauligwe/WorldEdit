"use client";
import { useState } from "react";
import { CldUploadWidget, CldImage } from "next-cloudinary";
import {
  CLOUDINARY_UPLOAD_PRESET,
  CLOUDINARY_FOLDER,
  isCloudinaryConfigured,
} from "@/lib/cloudinary";
import { asiOneCoordinatorChatUrl } from "@/lib/agentAddresses";

interface UploadedImage {
  publicId: string;
  url: string;
  originalFilename: string;
}

export default function PromptBar() {
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<UploadedImage | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const uploadEnabled = isCloudinaryConfigured && Boolean(CLOUDINARY_UPLOAD_PRESET);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || submitting) return;
    setSubmitting(true);
    // Open ASI:One in a new tab routed at the Conjure-Coordinator with the
    // user's prompt. The Coordinator then issues a Stripe RequestPayment and,
    // on CommitPayment, runs the 10-stage pre-gen pipeline.
    const url = asiOneCoordinatorChatUrl(prompt);
    window.open(url, "_blank", "noopener,noreferrer");
    // Quick visual reset so the user can submit again if the popup was blocked.
    setTimeout(() => setSubmitting(false), 1200);
  }

  return (
    <form
      onSubmit={onSubmit}
      className="w-full max-w-3xl bg-surface-lowest border border-outline-variant rounded-xl shadow-soft flex items-center gap-3 px-4 py-3"
    >
      {uploadEnabled ? (
        <CldUploadWidget
          uploadPreset={CLOUDINARY_UPLOAD_PRESET}
          options={{ folder: `${CLOUDINARY_FOLDER}/prompts`, sources: ["local", "url", "camera"], multiple: false }}
          onSuccess={(result) => {
            const info = (result as { info?: { public_id?: string; secure_url?: string; original_filename?: string } }).info;
            if (info?.public_id && info.secure_url) {
              setImage({
                publicId: info.public_id,
                url: info.secure_url,
                originalFilename: info.original_filename ?? "image",
              });
            }
          }}
        >
          {({ open }) => (
            <button
              type="button"
              onClick={() => open()}
              className="shrink-0 w-9 h-9 rounded grid place-items-center text-on-surface-variant hover:bg-surface-low"
              aria-label="Attach image via Cloudinary"
              title="Attach image (uploads to Cloudinary)"
            >
              <AttachIcon />
            </button>
          )}
        </CldUploadWidget>
      ) : (
        <button
          type="button"
          disabled
          className="shrink-0 w-9 h-9 rounded grid place-items-center text-on-surface-variant opacity-40"
          aria-label="Attach image (Cloudinary not configured)"
          title="Cloudinary not configured — set NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME and NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET"
        >
          <AttachIcon />
        </button>
      )}

      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe a world to step into…"
        className="flex-1 bg-transparent outline-none text-base placeholder:text-outline"
        disabled={submitting}
      />

      {image && (
        <div className="flex items-center gap-2 max-w-[14rem]">
          <CldImage
            src={image.publicId}
            width={40}
            height={40}
            alt={image.originalFilename}
            crop="thumb"
            gravity="auto"
            className="w-7 h-7 rounded object-cover border border-outline-variant"
          />
          <span className="text-xs text-on-surface-variant truncate">{image.originalFilename}</span>
          <button
            type="button"
            onClick={() => setImage(null)}
            className="text-xs text-outline hover:text-on-surface"
            aria-label="Remove attached image"
          >
            ×
          </button>
        </div>
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

function AttachIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
    </svg>
  );
}

import { CldImage } from "next-cloudinary";
import type { AgentEntry } from "@/lib/agentResults";
import { isCloudinaryConfigured } from "@/lib/cloudinary";
import { FallbackCard } from "./TextCard";

interface MediaItem {
  url: string;
  label?: string;
  caption?: string;
}

function pickMediaArray(out: any): MediaItem[] {
  if (!out || typeof out !== "object") return [];
  const candidates = ["products", "thumbnails", "shots", "items", "media", "images"];
  for (const k of candidates) {
    const v = out[k];
    if (Array.isArray(v) && v.length > 0) {
      return v
        .map((it) => normalize(it))
        .filter((it): it is MediaItem => it !== null);
    }
  }
  return [];
}

function normalize(it: unknown): MediaItem | null {
  if (typeof it === "string") {
    return /^https?:\/\//.test(it) ? { url: it } : null;
  }
  if (it && typeof it === "object") {
    const obj = it as Record<string, any>;
    const url = obj.image_url ?? obj.image ?? obj.url ?? obj.thumbnail ?? obj.src;
    if (typeof url !== "string" || !/^https?:\/\//.test(url)) return null;
    return {
      url,
      label: obj.name ?? obj.title ?? obj.label,
      caption: obj.description ?? obj.caption ?? obj.note ?? obj.price,
    };
  }
  return null;
}

export default function MediaGalleryCard({
  entry,
  variant = "products",
}: {
  entry: AgentEntry;
  /** "products" applies background removal for catalog-style images. "thumbnails" applies smart crop. */
  variant?: "products" | "thumbnails";
}) {
  if (entry.status !== "done") return <FallbackCard entry={entry} />;
  const items = pickMediaArray(entry.output);
  if (items.length === 0) return null;

  const cloudinary = isCloudinaryConfigured;
  const visible = items.slice(0, 4);

  return (
    <div className="grid grid-cols-2 gap-2 mt-2">
      {visible.map((item, i) => (
        <div key={i} className="space-y-1">
          <div className="aspect-square rounded overflow-hidden bg-surface-container border border-outline-variant relative">
            {cloudinary ? (
              <CldImage
                src={item.url}
                deliveryType="fetch"
                width={160}
                height={160}
                alt={item.label ?? `agent media ${i + 1}`}
                crop={variant === "products" ? "pad" : "fill"}
                gravity={variant === "products" ? "center" : "auto"}
                background="white"
                removeBackground={variant === "products"}
                className="w-full h-full object-contain"
                sizes="160px"
              />
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={item.url}
                alt={item.label ?? `agent media ${i + 1}`}
                className="w-full h-full object-cover"
              />
            )}
          </div>
          {(item.label || item.caption) && (
            <div className="px-0.5">
              {item.label && (
                <div className="text-[11px] font-medium text-on-surface truncate">{item.label}</div>
              )}
              {item.caption && (
                <div className="text-[10px] text-on-surface-variant truncate">{item.caption}</div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

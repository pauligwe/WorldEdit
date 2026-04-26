import type { AgentEntry } from "@/lib/agentResults";
import MediaGalleryCard from "./MediaGalleryCard";

// Every agent's structured output ends with a `narrative: str` field — a 1-2
// sentence prose summary the agent writes about its own findings. Agents
// whose output includes media URLs (Prop Shopping, Shot List) also get a
// small Cloudinary-powered gallery underneath: products use AI background
// removal for catalog-style images; thumbnails use smart auto-cropping.
export function renderAgentCard(entry: AgentEntry) {
  if (entry.status === "skipped") {
    return <p className="text-xs text-on-surface-variant italic">Skipped — {entry.reason ?? "upstream failed"}</p>;
  }
  if (entry.status === "error") {
    return <p className="text-xs text-red-600">Error: {entry.error_message ?? "unknown"}</p>;
  }
  const narrative = (entry.output as any)?.narrative;
  const display = entry.display;
  const showGallery = display === "products" || display === "thumbnails";
  const variant = display === "thumbnails" ? "thumbnails" : "products";

  return (
    <div className="space-y-2">
      {typeof narrative === "string" && narrative.trim().length > 0 ? (
        <p className="text-sm leading-relaxed text-on-surface">{narrative}</p>
      ) : (
        <p className="text-xs text-on-surface-variant italic">No summary available.</p>
      )}
      {showGallery && <MediaGalleryCard entry={entry} variant={variant} />}
    </div>
  );
}

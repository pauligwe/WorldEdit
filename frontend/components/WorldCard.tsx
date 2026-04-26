"use client";
import Link from "next/link";
import { CldImage } from "next-cloudinary";
import type { WorldDef } from "@/lib/worlds";
import { isCloudinaryConfigured } from "@/lib/cloudinary";

function formatRelative(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffDays = Math.max(0, Math.floor((now - then) / 86400_000));
  if (diffDays === 0) return "Created today";
  if (diffDays === 1) return "Created yesterday";
  if (diffDays < 30) return `Created ${diffDays} days ago`;
  return `Created ${new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
}

export default function WorldCard({ world }: { world: WorldDef }) {
  const slug = world.title.toUpperCase();
  const useCloudinary = isCloudinaryConfigured && Boolean(world.cloudinaryId);

  return (
    <Link
      href={`/world/${world.id}`}
      className="shrink-0 w-72 group block"
    >
      <div className="aspect-[16/10] rounded-md overflow-hidden bg-surface-container border border-outline-variant relative">
        {useCloudinary ? (
          <CldImage
            src={world.cloudinaryId!}
            width={576}
            height={360}
            alt={world.title}
            sizes="(max-width: 768px) 80vw, 288px"
            crop="fill"
            gravity="auto"
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />
        ) : world.thumbnail ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={world.thumbnail}
            alt={world.title}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
          />
        ) : (
          <div className="w-full h-full grid place-items-center text-on-surface-variant text-xs">
            no preview
          </div>
        )}
      </div>
      <div className="mt-3">
        <div className="label-caps text-on-surface">{slug}</div>
        <div className="text-sm text-on-surface-variant mt-1">{formatRelative(world.createdAt)}</div>
      </div>
    </Link>
  );
}

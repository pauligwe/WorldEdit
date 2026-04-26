import Link from "next/link";
import SplatScene from "@/components/SplatScene";
import { WORLDS } from "@/lib/worlds";

export default function WorldPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { capture?: string; reset?: string };
}) {
  const world = WORLDS[params.id];
  if (!world) {
    return (
      <main className="min-h-screen bg-surface text-on-surface flex flex-col items-center justify-center">
        <p className="text-on-surface-variant">No world with id <code>{params.id}</code></p>
        <Link href="/" className="underline mt-4">go back</Link>
      </main>
    );
  }

  // Always re-run the swarm on every page load so the demo shows the full
  // agent animation every time. The query params are kept for backwards
  // compatibility but are no longer needed in normal use.
  const captureMode = { id: world.id, force: true, reset: true };

  return (
    <>
      <SplatScene
        splatUrl={world.splat}
        spawn={world.spawn}
        yaw={world.yaw}
        pitch={world.pitch}
        thumbnailUrl={world.thumbnail}
        captureMode={captureMode}
      />
      <div className="fixed top-4 left-4 z-10 pointer-events-auto">
        <Link
          href="/"
          className="text-xs font-sans bg-white/90 text-on-surface px-3 py-1.5 rounded shadow-soft hover:bg-white border border-outline-variant"
        >
          ← {world.title}
        </Link>
      </div>
    </>
  );
}

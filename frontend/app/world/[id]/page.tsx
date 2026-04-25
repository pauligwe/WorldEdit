import Link from "next/link";
import SplatScene from "@/components/SplatScene";
import { WORLDS } from "@/lib/worlds";

export default function WorldPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { capture?: string };
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

  // Auto-capture is on by default — the scene decides whether to actually fire
  // (skips if a thumbnail already exists at world.thumbnail). `?capture=1`
  // forces a re-capture even if the thumbnail is already there.
  const captureMode = { id: world.id, force: searchParams.capture === "1" };

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
          className="text-xs font-mono bg-white/90 text-on-surface px-3 py-1.5 rounded shadow-soft hover:bg-white border border-outline-variant"
        >
          ← {world.title}
        </Link>
      </div>
    </>
  );
}

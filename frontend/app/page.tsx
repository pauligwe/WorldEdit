import PromptBar from "@/components/PromptBar";
import WorldCard from "@/components/WorldCard";
import { WORLD_LIST } from "@/lib/worlds";

export default function Home() {
  return (
    <main className="min-h-screen bg-surface text-on-surface flex flex-col">
      <header className="flex items-center justify-between px-10 py-8">
        <div className="font-bold uppercase text-xl leading-none">CONJURE</div>
        <div className="font-bold uppercase text-xl leading-none">FETCH.AI</div>
      </header>

      <section className="flex-1 flex flex-col items-center justify-center px-6 -mt-8">
        <h1 className="text-6xl md:text-7xl font-semibold tracking-[-0.03em] leading-[0.95] text-center">
          Imagine a World
        </h1>
        <p className="mt-5 text-center text-on-surface-variant text-lg md:text-xl tracking-tight">
          Conjure with Fetch.AI
        </p>
        <div className="mt-12 w-full flex justify-center">
          <PromptBar />
        </div>
      </section>

      <section className="border-t border-outline-variant bg-surface-lowest">
        <div className="px-10 pt-10 pb-2 flex items-center justify-between">
          <h2 className="label-caps text-on-surface-variant text-sm">
            Recent Generations
          </h2>
          <button className="text-sm text-on-surface hover:underline">
            View All Worlds
          </button>
        </div>
        <div className="px-10 pb-12 pt-6 overflow-x-auto">
          <div className="flex gap-6 min-w-max">
            {WORLD_LIST.map((w) => (
              <WorldCard key={w.id} world={w} />
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

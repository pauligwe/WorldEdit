import PromptForm from "@/components/PromptForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8">
      <div className="absolute top-6 right-6 text-xs text-zinc-500">powered by Fetch.ai Agentverse</div>
      <h1 className="text-6xl font-black mb-4 bg-gradient-to-r from-cyan-300 to-violet-400 bg-clip-text text-transparent">World Build</h1>
      <p className="text-zinc-400 mb-8 text-lg">Describe a building. Walk inside it.</p>
      <PromptForm />
    </main>
  );
}

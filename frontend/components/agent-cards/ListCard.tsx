import type { AgentEntry } from "@/lib/agentResults";
import { FallbackCard } from "./TextCard";

export default function ListCard({ entry }: { entry: AgentEntry }) {
  if (entry.status !== "done") return <FallbackCard entry={entry} />;
  const out = entry.output ?? {};

  const arrayKey = Object.keys(out).find((k) => Array.isArray(out[k]));
  if (!arrayKey) {
    return (
      <pre className="text-xs font-mono whitespace-pre-wrap break-words text-on-surface-variant">
        {JSON.stringify(out, null, 2)}
      </pre>
    );
  }
  const items = out[arrayKey] as any[];

  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="text-sm text-on-surface">
          {typeof item === "string" ? (
            item
          ) : (
            <ItemRow item={item} />
          )}
        </li>
      ))}
    </ul>
  );
}

function ItemRow({ item }: { item: Record<string, any> }) {
  const keys = Object.keys(item);
  const primary = keys.find((k) => ["name", "title", "type", "region", "category"].includes(k)) ?? keys[0];
  const secondary = keys.find((k) => k !== primary && typeof item[k] === "string");
  return (
    <div>
      <div className="font-medium">{String(item[primary])}</div>
      {secondary && <div className="text-xs text-on-surface-variant">{String(item[secondary])}</div>}
    </div>
  );
}

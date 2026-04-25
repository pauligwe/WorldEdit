import TextCard from "./TextCard";
import ListCard from "./ListCard";
import type { AgentEntry } from "@/lib/agentResults";

export function renderAgentCard(entry: AgentEntry) {
  switch (entry.display) {
    case "list":
      return <ListCard entry={entry} />;
    case "swatches":
    case "map":
    case "products":
    case "thumbnails":
      return <TextCard entry={entry} />;
    case "text":
    default:
      return <TextCard entry={entry} />;
  }
}

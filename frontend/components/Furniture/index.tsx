"use client";
import { useState } from "react";
import type { FurnitureItem } from "@/lib/worldSpec";
import Couch from "./Couch";
import Bed from "./Bed";
import Table from "./Table";
import Chair from "./Chair";
import Lamp from "./Lamp";
import Rug from "./Rug";
import Bookshelf from "./Bookshelf";
import Plant from "./Plant";

interface Props { item: FurnitureItem; tint?: string; onClick?: () => void; }

const REGISTRY: Record<string, React.ComponentType<any>> = {
  couch: Couch,
  sofa: Couch,
  bed: Bed,
  table: Table,
  desk: Table,
  chair: Chair,
  lamp: Lamp,
  rug: Rug,
  bookshelf: Bookshelf,
  wardrobe: Bookshelf,
  nightstand: Table,
  tv: Table,
  plant: Plant,
};

export default function Furniture({ item, tint, onClick }: Props) {
  const [hover, setHover] = useState(false);
  const Comp = REGISTRY[item.type] ?? Table;
  const finalTint = tint ?? item.tint ?? defaultTint(item.type);
  return (
    <group
      position={item.position}
      rotation={[0, item.rotation ?? 0, 0]}
      onClick={(e) => { e.stopPropagation(); onClick?.(); }}
      onPointerOver={(e) => { e.stopPropagation(); setHover(true); document.body.style.cursor = "pointer"; }}
      onPointerOut={() => { setHover(false); document.body.style.cursor = "default"; }}
    >
      <Comp size={item.size} color={hover ? "#ffffff" : finalTint} />
    </group>
  );
}

function defaultTint(type: string): string {
  switch (type) {
    case "couch": case "sofa": return "#6b7280";
    case "bed": return "#9ca3af";
    case "table": case "desk": case "nightstand": case "tv": return "#a16207";
    case "chair": return "#4b5563";
    case "lamp": return "#fef3c7";
    case "rug": return "#92400e";
    case "bookshelf": case "wardrobe": return "#451a03";
    case "plant": return "#16a34a";
    default: return "#6b7280";
  }
}

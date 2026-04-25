"use client";
import type { FurnitureItem } from "@/lib/worldSpec";
import Couch from "./Couch";
import Bed from "./Bed";
import Table from "./Table";
import Chair from "./Chair";
import Lamp from "./Lamp";
import Rug from "./Rug";
import Bookshelf from "./Bookshelf";
import Plant from "./Plant";
import Desk from "./Desk";
import OfficeChair from "./OfficeChair";
import ConferenceTable from "./ConferenceTable";
import ReceptionDesk from "./ReceptionDesk";
import Whiteboard from "./Whiteboard";
import FilingCabinet from "./FilingCabinet";

interface Props { item: FurnitureItem; tint?: string }

const REGISTRY: Record<string, React.ComponentType<any>> = {
  couch: Couch, sofa: Couch, bed: Bed,
  table: Table, nightstand: Table, tv: Table,
  chair: Chair, lamp: Lamp, rug: Rug,
  bookshelf: Bookshelf, wardrobe: Bookshelf, plant: Plant,
  desk: Desk,
  office_chair: OfficeChair,
  conference_table: ConferenceTable,
  reception_desk: ReceptionDesk,
  whiteboard: Whiteboard,
  filing_cabinet: FilingCabinet,
};

export default function Furniture({ item, tint }: Props) {
  const Comp = REGISTRY[item.type] ?? Table;
  const finalTint = tint ?? defaultTint(item.type);
  return (
    <group position={item.position} rotation={[0, item.rotation ?? 0, 0]}>
      <Comp size={item.size} color={finalTint} />
    </group>
  );
}

function defaultTint(type: string): string {
  switch (type) {
    case "couch": case "sofa": return "#6b7280";
    case "bed": return "#9ca3af";
    case "table": case "desk": case "nightstand": case "tv": return "#a16207";
    case "chair": return "#4b5563";
    case "office_chair": return "#1f2937";
    case "conference_table": return "#3a2e1d";
    case "reception_desk": return "#5e3a1e";
    case "whiteboard": return "#f5f5f0";
    case "filing_cabinet": return "#374151";
    case "lamp": return "#fef3c7";
    case "rug": return "#92400e";
    case "bookshelf": case "wardrobe": return "#451a03";
    case "plant": return "#16a34a";
    default: return "#6b7280";
  }
}

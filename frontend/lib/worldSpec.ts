export type Wall = "north" | "south" | "east" | "west";

export interface Door { wall: Wall; offset: number; width: number; }
export interface Window { wall: Wall; offset: number; width: number; height: number; sill: number; }

export interface Room {
  id: string; type: string;
  x: number; y: number; width: number; depth: number;
  doors: Door[]; windows: Window[];
}

export interface Stairs { id: string; x: number; y: number; width: number; depth: number; direction: Wall; toLevel: number; }
export interface Floor { level: number; ceilingHeight: number; rooms: Room[]; stairs: Stairs[]; }
export interface Blueprint { gridSize: number; floors: Floor[]; }

export interface GeometryPrimitive {
  type: "floor" | "wall" | "ceiling" | "stair";
  roomId?: string;
  wall?: Wall;
  position: [number, number, number];
  size: [number, number, number];
  rotation?: number;
  holes?: { offset: number; width: number; height: number; bottom: number }[];
}
export interface Geometry { primitives: GeometryPrimitive[]; }

export interface Light { type: "ceiling" | "lamp" | "ambient"; position: [number, number, number]; color: string; intensity: number; }
export interface Lighting { byRoom: Record<string, Light[]>; }

export interface RoomMaterial { wall: string; floor: string; ceiling: string; }
export interface Materials { byRoom: Record<string, RoomMaterial>; }

export interface FurnitureItem {
  id: string; roomId: string; type: string; subtype?: string;
  position: [number, number, number]; rotation: number; size: [number, number, number];
  selectedProductId?: string; alternates: string[]; tint?: string;
}

export interface Product { name: string; price?: number; imageUrl?: string; vendor?: string; url?: string; fitsTypes: string[]; }

export interface Navigation { spawnPoint: [number, number, number]; walkableMeshIds: string[]; stairColliders: string[]; }
export interface Cost { total: number; byRoom: Record<string, number>; }

export interface Intent { buildingType: string; style: string; floors: number; vibe: string[]; sizeHint: string; }

export interface WorldSpec {
  worldId: string;
  prompt: string;
  intent?: Intent;
  blueprint?: Blueprint;
  geometry?: Geometry;
  lighting?: Lighting;
  materials?: Materials;
  furniture: FurnitureItem[];
  products: Record<string, Product>;
  navigation?: Navigation;
  cost?: Cost;
}

export interface WorldDef {
  id: string;
  title: string;
  splat: string;
  thumbnail?: string;
  spawn: [number, number, number];
  yaw: number;
  pitch: number;
  createdAt: string;
}

export const WORLDS: Record<string, WorldDef> = {
  cabin: {
    id: "cabin",
    title: "Rustic Woodland Cabin",
    splat: "/worlds/cabin.spz",
    thumbnail: "/worlds/cabin.jpg",
    spawn: [0.61, 2.07, 0.38],
    yaw: 0.1 + Math.PI,
    pitch: 0.002,
    createdAt: "2026-04-25",
  },
  office: {
    id: "office",
    title: "Modern Downtown Office Building",
    splat: "/worlds/office.spz",
    thumbnail: "/worlds/office.jpg",
    spawn: [0.72, 25.80, 7.77],
    yaw: 3.080,
    pitch: -0.090,
    createdAt: "2026-04-25",
  },
  living_room: {
    id: "living_room",
    title: "Cozy Living Room Interior",
    splat: "/worlds/living_room.spz",
    thumbnail: "/worlds/living_room.jpg",
    spawn: [0, 1.7, 0],
    yaw: Math.PI,
    pitch: 0,
    createdAt: "2026-04-25",
  },
};

export const WORLD_LIST = Object.values(WORLDS);

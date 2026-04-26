export interface WorldDef {
  id: string;
  title: string;
  splat: string;
  thumbnail?: string;
  /** Cloudinary public_id; when set, the card renders via CldImage (auto format/quality/responsive). */
  cloudinaryId?: string;
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
    cloudinaryId: "conjure/worlds/cabin",
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
    cloudinaryId: "conjure/worlds/office",
    spawn: [0.72, 25.80, 7.77],
    yaw: 3.080,
    pitch: -0.090,
    createdAt: "2026-04-25",
  },
  minecraft_valley: {
    id: "minecraft_valley",
    title: "Minecraft Valley Waterfall Oasis",
    splat: "/worlds/minecraft_valley.spz",
    thumbnail: "/worlds/minecraft_valley.jpg",
    cloudinaryId: "conjure/worlds/minecraft_valley",
    spawn: [0, 1.7, 0],
    yaw: Math.PI,
    pitch: 0,
    createdAt: "2026-04-25",
  },
  serene_living_room: {
    id: "serene_living_room",
    title: "Serene Living Room Countryside View",
    splat: "/worlds/serene_living_room.spz",
    thumbnail: "/worlds/serene_living_room.jpg",
    cloudinaryId: "conjure/worlds/serene_living_room",
    spawn: [0, 1.7, 0],
    yaw: Math.PI,
    pitch: 0,
    createdAt: "2026-04-25",
  },
  grecian_city: {
    id: "grecian_city",
    title: "White Grecian City Landscape",
    splat: "/worlds/grecian_city.spz",
    thumbnail: "/worlds/grecian_city.jpg",
    cloudinaryId: "conjure/worlds/grecian_city",
    spawn: [0, 1.7, 0],
    yaw: Math.PI,
    pitch: 0,
    createdAt: "2026-04-25",
  },
  coffee_shop: {
    id: "coffee_shop",
    title: "Modern Loft Coffee Shop",
    splat: "/worlds/coffee_shop.spz",
    thumbnail: "/worlds/coffee_shop.jpg",
    spawn: [0, 1.7, 0],
    yaw: Math.PI,
    pitch: 0,
    createdAt: "2026-04-26",
  },
  living_room: {
    id: "living_room",
    title: "Cozy Living Room Interior",
    splat: "/worlds/living_room.spz",
    thumbnail: "/worlds/living_room.jpg",
    cloudinaryId: "conjure/worlds/living_room",
    spawn: [0, 1.7, 0],
    yaw: Math.PI,
    pitch: 0,
    createdAt: "2026-04-26",
  },
};

export const WORLD_LIST = Object.values(WORLDS);

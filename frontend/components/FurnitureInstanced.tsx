"use client";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { Instances, Instance } from "@react-three/drei";
import type { FurnitureItem } from "@/lib/worldSpec";

// ---------------------------------------------------------------------------
// Default tints (mirror Furniture/index.tsx)
// ---------------------------------------------------------------------------
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

// Type aliases used in the registry. Types map to their canonical key (e.g. sofa -> couch).
const TYPE_ALIAS: Record<string, string> = {
  sofa: "couch",
  nightstand: "table",
  tv: "table",
  wardrobe: "bookshelf",
};

function canonicalType(type: string): string {
  return TYPE_ALIAS[type] ?? type;
}

// ---------------------------------------------------------------------------
// Geometry kinds. Each kind describes a UNIT-SHAPE base geometry used as the
// shared geometry inside one <Instances> group; per-instance scale handles
// final dimensions.
// ---------------------------------------------------------------------------
type GeomSpec =
  // unit-cube box, scale per axis
  | { kind: "box" }
  // unit-cylinder with given top/bottom radii (in unit frame), unit height,
  // segment count, and open flag. Per-instance scale: x === z (uniform radial),
  // y is height.
  | { kind: "cylinder"; radiusTop: number; radiusBottom: number; radialSegments: number; open?: boolean }
  // unit-sphere, scale uniformly via x=y=z=radius.
  | { kind: "sphere"; widthSegments: number; heightSegments: number }
  // pre-rotated horizontal plane (unit, lying in XZ plane). scale [w, 1, d].
  | { kind: "flatPlane" };

type MatSpec = {
  // 'tint' means use the default tint of the type at runtime (the tint is the
  // SAME for all instances of the same type, so it's safe to bake in).
  // string is a literal hex color.
  color: string | "tint";
  roughness?: number;
  metalness?: number;
  emissive?: string | "tint";
  emissiveIntensity?: number;
  doubleSide?: boolean;
};

type SubPart = {
  geom: GeomSpec;
  mat: MatSpec;
  // Compute per-item localPos and localScale (local frame, before parent Y rotation).
  // size = [w, h, d] of the FurnitureItem.
  compute: (
    w: number,
    h: number,
    d: number
  ) => { lx: number; ly: number; lz: number; sx: number; sy: number; sz: number };
};

// ---------------------------------------------------------------------------
// Per-type sub-part registry. Proportions match the existing per-component
// files in components/Furniture/.
// ---------------------------------------------------------------------------
const SUBPARTS: Record<string, SubPart[]> = {
  // ---------------------- Office furniture ----------------------
  desk: (() => {
    const topThickness = 0.04;
    const legSize = 0.06;
    const top: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint" },
      compute: (w, h, d) => ({
        lx: 0, ly: h - topThickness / 2, lz: 0,
        sx: w, sy: topThickness, sz: d,
      }),
    };
    const legCorners: Array<[number, number]> = [
      [-1, -1], [1, -1], [-1, 1], [1, 1],
    ];
    const legs: SubPart[] = legCorners.map(([sx, sz]) => ({
      geom: { kind: "box" },
      mat: { color: "#3a3a3a" },
      compute: (w, h, d) => ({
        lx: sx * (w / 2 - legSize), ly: (h - topThickness) / 2, lz: sz * (d / 2 - legSize),
        sx: legSize, sy: h - topThickness, sz: legSize,
      }),
    }));
    return [top, ...legs];
  })(),

  office_chair: [
    // base disk
    {
      geom: { kind: "cylinder", radiusTop: 0.5, radiusBottom: 0.5, radialSegments: 12 },
      mat: { color: "#1a1a1a" },
      compute: (w, _h, _d) => ({ lx: 0, ly: 0.05, lz: 0, sx: w, sy: 0.1, sz: w }),
    },
    // post
    {
      geom: { kind: "cylinder", radiusTop: 1, radiusBottom: 1, radialSegments: 8 },
      mat: { color: "#2a2a2a" },
      compute: (_w, h, _d) => ({ lx: 0, ly: h * 0.32, lz: 0, sx: 0.04, sy: h * 0.45, sz: 0.04 }),
    },
    // seat
    {
      geom: { kind: "box" },
      mat: { color: "tint" },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.55, lz: 0, sx: w * 0.85, sy: 0.08, sz: d * 0.85 }),
    },
    // backrest
    {
      geom: { kind: "box" },
      mat: { color: "tint" },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.85, lz: -d * 0.4, sx: w * 0.85, sy: h * 0.4, sz: 0.08 }),
    },
  ],

  conference_table: (() => {
    const topThickness = 0.05;
    const legSize = 0.08;
    const top: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint" },
      compute: (w, h, d) => ({
        lx: 0, ly: h - topThickness / 2, lz: 0,
        sx: w, sy: topThickness, sz: d,
      }),
    };
    const legCorners: Array<[number, number]> = [
      [-1, -1], [1, -1], [-1, 1], [1, 1],
    ];
    const legs: SubPart[] = legCorners.map(([sx, sz]) => ({
      geom: { kind: "box" },
      mat: { color: "#222" },
      compute: (w, h, d) => ({
        lx: sx * (w / 2 - legSize), ly: (h - topThickness) / 2, lz: sz * (d / 2 - legSize),
        sx: legSize, sy: h - topThickness, sz: legSize,
      }),
    }));
    return [top, ...legs];
  })(),

  reception_desk: [
    // main body
    {
      geom: { kind: "box" },
      mat: { color: "tint" },
      compute: (w, h, d) => ({ lx: 0, ly: h / 2, lz: 0, sx: w, sy: h, sz: d * 0.7 }),
    },
    // counter top trim
    {
      geom: { kind: "box" },
      mat: { color: "#222" },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.55, lz: d * 0.4, sx: w, sy: h * 0.2, sz: 0.08 }),
    },
  ],

  whiteboard: [
    // board (color hardcoded in the original component to "#f5f5f0")
    {
      geom: { kind: "box" },
      mat: { color: "#f5f5f0" },
      compute: (w, h, d) => ({ lx: 0, ly: h / 2, lz: 0, sx: w, sy: h, sz: d }),
    },
    // frame
    {
      geom: { kind: "box" },
      mat: { color: "#a0a0a0" },
      compute: (w, h, d) => ({ lx: 0, ly: h / 2, lz: d / 2 + 0.005, sx: w + 0.04, sy: h + 0.04, sz: 0.01 }),
    },
  ],

  filing_cabinet: (() => {
    const body: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint" },
      compute: (w, h, d) => ({ lx: 0, ly: h / 2, lz: 0, sx: w, sy: h, sz: d }),
    };
    const handles: SubPart[] = [0.25, 0.5, 0.75].map((frac) => ({
      geom: { kind: "box" },
      mat: { color: "#1a1a1a" },
      compute: (w, h, d) => ({ lx: 0, ly: h * frac, lz: d / 2 + 0.001, sx: w * 0.9, sy: 0.01, sz: 0.005 }),
    }));
    return [body, ...handles];
  })(),

  // ---------------------- Residential furniture ----------------------
  couch: (() => {
    const FRAME = "#2a1f15";
    const base: SubPart = {
      geom: { kind: "box" },
      mat: { color: FRAME, roughness: 0.7 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.18, lz: 0, sx: w, sy: h * 0.35, sz: d }),
    };
    const cushionL: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: -w * 0.24, ly: h * 0.45, lz: 0.02, sx: w * 0.45, sy: h * 0.18, sz: d * 0.85 }),
    };
    const cushionR: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: w * 0.24, ly: h * 0.45, lz: 0.02, sx: w * 0.45, sy: h * 0.18, sz: d * 0.85 }),
    };
    const backrest: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.7, lz: -d * 0.4, sx: w * 0.85, sy: h * 0.5, sz: d * 0.18 }),
    };
    const armL: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: -w * 0.45, ly: h * 0.42, lz: 0, sx: w * 0.1, sy: h * 0.55, sz: d }),
    };
    const armR: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: w * 0.45, ly: h * 0.42, lz: 0, sx: w * 0.1, sy: h * 0.55, sz: d }),
    };
    const legCorners: Array<[number, number]> = [
      [-1, -1], [1, -1], [-1, 1], [1, 1],
    ];
    const legs: SubPart[] = legCorners.map(([sx, sz]) => ({
      geom: { kind: "box" },
      mat: { color: FRAME },
      compute: (w, h, d) => ({
        lx: sx * (w * 0.45), ly: h * 0.04, lz: sz * (d * 0.45),
        sx: w * 0.04, sy: h * 0.08, sz: d * 0.04,
      }),
    }));
    return [base, cushionL, cushionR, backrest, armL, armR, ...legs];
  })(),

  bed: [
    // bedframe
    {
      geom: { kind: "box" },
      mat: { color: "#3a2a1a", roughness: 0.65 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.18, lz: 0, sx: w, sy: h * 0.35, sz: d }),
    },
    // mattress
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.95 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.5, lz: 0, sx: w * 0.95, sy: h * 0.25, sz: d * 0.95 }),
    },
    // sheet/cover
    {
      geom: { kind: "box" },
      mat: { color: "#f3f4f6", roughness: 0.9 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.62, lz: d * 0.18, sx: w * 0.94, sy: h * 0.04, sz: d * 0.55 }),
    },
    // pillow L
    {
      geom: { kind: "box" },
      mat: { color: "#fafafa", roughness: 0.95 },
      compute: (w, h, d) => ({ lx: -w * 0.22, ly: h * 0.7, lz: -d * 0.32, sx: w * 0.36, sy: h * 0.1, sz: d * 0.18 }),
    },
    // pillow R
    {
      geom: { kind: "box" },
      mat: { color: "#fafafa", roughness: 0.95 },
      compute: (w, h, d) => ({ lx: w * 0.22, ly: h * 0.7, lz: -d * 0.32, sx: w * 0.36, sy: h * 0.1, sz: d * 0.18 }),
    },
    // headboard
    {
      geom: { kind: "box" },
      mat: { color: "#3a2a1a", roughness: 0.55 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.95, lz: -d * 0.5, sx: w * 1.02, sy: h * 0.6, sz: d * 0.06 }),
    },
  ],

  table: (() => {
    const top: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.5, metalness: 0.05 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.92, lz: 0, sx: w, sy: h * 0.08, sz: d }),
    };
    const apron: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.7 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.82, lz: 0, sx: w * 0.9, sy: h * 0.08, sz: d * 0.9 }),
    };
    const legCorners: Array<[number, number]> = [
      [-1, -1], [1, -1], [-1, 1], [1, 1],
    ];
    const legs: SubPart[] = legCorners.map(([sx, sz]) => ({
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.6 },
      compute: (w, h, d) => ({
        lx: sx * (w * 0.45), ly: h * 0.4, lz: sz * (d * 0.45),
        sx: w * 0.07, sy: h * 0.78, sz: d * 0.07,
      }),
    }));
    return [top, apron, ...legs];
  })(),

  chair: (() => {
    const FRAME = "#3a2a1a";
    const seatCushion: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.45, lz: 0, sx: w * 0.9, sy: h * 0.12, sz: d * 0.9 }),
    };
    const seatPlank: SubPart = {
      geom: { kind: "box" },
      mat: { color: FRAME, roughness: 0.7 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.38, lz: 0, sx: w * 0.95, sy: h * 0.05, sz: d * 0.95 }),
    };
    const backCushion: SubPart = {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.85 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.78, lz: -d * 0.4, sx: w * 0.85, sy: h * 0.55, sz: d * 0.12 }),
    };
    const backFrame: SubPart = {
      geom: { kind: "box" },
      mat: { color: FRAME, roughness: 0.7 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.78, lz: -d * 0.46, sx: w * 0.92, sy: h * 0.6, sz: d * 0.04 }),
    };
    const armL: SubPart = {
      geom: { kind: "box" },
      mat: { color: FRAME, roughness: 0.7 },
      compute: (w, h, d) => ({ lx: -w * 0.45, ly: h * 0.55, lz: 0, sx: w * 0.05, sy: h * 0.05, sz: d * 0.7 }),
    };
    const armR: SubPart = {
      geom: { kind: "box" },
      mat: { color: FRAME, roughness: 0.7 },
      compute: (w, h, d) => ({ lx: w * 0.45, ly: h * 0.55, lz: 0, sx: w * 0.05, sy: h * 0.05, sz: d * 0.7 }),
    };
    const legCorners: Array<[number, number]> = [
      [-1, -1], [1, -1], [-1, 1], [1, 1],
    ];
    const legs: SubPart[] = legCorners.map(([sx, sz]) => ({
      geom: { kind: "box" },
      mat: { color: FRAME, roughness: 0.6 },
      compute: (w, h, d) => ({
        lx: sx * (w * 0.42), ly: h * 0.18, lz: sz * (d * 0.42),
        sx: w * 0.06, sy: h * 0.36, sz: d * 0.06,
      }),
    }));
    return [seatCushion, seatPlank, backCushion, backFrame, armL, armR, ...legs];
  })(),

  lamp: [
    // base (truncated cone, top=0.42, bottom=0.45)
    {
      geom: { kind: "cylinder", radiusTop: 0.42, radiusBottom: 0.45, radialSegments: 24 },
      mat: { color: "#222", roughness: 0.4, metalness: 0.6 },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.04, lz: 0, sx: w, sy: h * 0.08, sz: w }),
    },
    // pole (uniform radius 0.04 absolute)
    {
      geom: { kind: "cylinder", radiusTop: 1, radiusBottom: 1, radialSegments: 12 },
      mat: { color: "#222", roughness: 0.4, metalness: 0.55 },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.5, lz: 0, sx: w * 0.04, sy: h * 0.8, sz: w * 0.04 }),
    },
    // shade (truncated cone, open, top=0.32, bottom=0.42), emits tint as glow
    {
      geom: { kind: "cylinder", radiusTop: 0.32, radiusBottom: 0.42, radialSegments: 24, open: true },
      mat: {
        color: "#f5e6c4",
        emissive: "tint",
        emissiveIntensity: 0.6,
        doubleSide: true,
      },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.86, lz: 0, sx: w, sy: h * 0.22, sz: w }),
    },
    // shade top cap (uniform radius 0.32 in unit frame)
    {
      geom: { kind: "cylinder", radiusTop: 0.32, radiusBottom: 0.32, radialSegments: 24 },
      mat: { color: "#f5e6c4" },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.97, lz: 0, sx: w, sy: h * 0.01, sz: w }),
    },
  ],

  rug: [
    // main rug (flat plane)
    {
      geom: { kind: "flatPlane" },
      mat: { color: "tint", roughness: 1 },
      compute: (w, _h, d) => ({ lx: 0, ly: 0.008, lz: 0, sx: w, sy: 1, sz: d }),
    },
    // darker border underneath
    {
      geom: { kind: "flatPlane" },
      mat: { color: "#2a1d12", roughness: 1 },
      compute: (w, _h, d) => ({ lx: 0, ly: 0.005, lz: 0, sx: w * 1.04, sy: 1, sz: d * 1.04 }),
    },
  ],

  bookshelf: [
    // back panel
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.6 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.5, lz: -d * 0.4, sx: w, sy: h, sz: d * 0.04 }),
    },
    // bottom
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.55 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.02, lz: 0, sx: w, sy: h * 0.04, sz: d * 0.85 }),
    },
    // top
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.5 },
      compute: (w, h, d) => ({ lx: 0, ly: h * 0.98, lz: 0, sx: w, sy: h * 0.04, sz: d * 0.9 }),
    },
    // side panel L
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.55 },
      compute: (w, h, d) => ({ lx: -w * 0.48, ly: h * 0.5, lz: 0, sx: w * 0.04, sy: h, sz: d * 0.85 }),
    },
    // side panel R
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.55 },
      compute: (w, h, d) => ({ lx: w * 0.48, ly: h * 0.5, lz: 0, sx: w * 0.04, sy: h, sz: d * 0.85 }),
    },
    // door L
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.4 },
      compute: (w, h, d) => ({ lx: -w * 0.235, ly: h * 0.5, lz: d * 0.42, sx: w * 0.46, sy: h * 0.92, sz: d * 0.03 }),
    },
    // door R
    {
      geom: { kind: "box" },
      mat: { color: "tint", roughness: 0.4 },
      compute: (w, h, d) => ({ lx: w * 0.235, ly: h * 0.5, lz: d * 0.42, sx: w * 0.46, sy: h * 0.92, sz: d * 0.03 }),
    },
    // handle L
    {
      geom: { kind: "cylinder", radiusTop: 1, radiusBottom: 1, radialSegments: 8 },
      mat: { color: "#cfcfcf", roughness: 0.25, metalness: 0.8 },
      compute: (w, h, d) => ({ lx: -w * 0.04, ly: h * 0.5, lz: d * 0.45, sx: 0.012, sy: h * 0.18, sz: 0.012 }),
    },
    // handle R
    {
      geom: { kind: "cylinder", radiusTop: 1, radiusBottom: 1, radialSegments: 8 },
      mat: { color: "#cfcfcf", roughness: 0.25, metalness: 0.8 },
      compute: (w, h, d) => ({ lx: w * 0.04, ly: h * 0.5, lz: d * 0.45, sx: 0.012, sy: h * 0.18, sz: 0.012 }),
    },
  ],

  plant: [
    // pot (truncated cone, top=0.42, bottom=0.3)
    {
      geom: { kind: "cylinder", radiusTop: 0.42, radiusBottom: 0.3, radialSegments: 16 },
      mat: { color: "#6b4a2b", roughness: 0.85 },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.15, lz: 0, sx: w, sy: h * 0.3, sz: w }),
    },
    // soil (uniform radius 0.4)
    {
      geom: { kind: "cylinder", radiusTop: 0.4, radiusBottom: 0.4, radialSegments: 16 },
      mat: { color: "#3b2410", roughness: 1 },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.31, lz: 0, sx: w, sy: h * 0.02, sz: w }),
    },
    // leaf cluster main
    {
      geom: { kind: "sphere", widthSegments: 14, heightSegments: 12 },
      mat: { color: "tint", roughness: 0.95 },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.7, lz: 0, sx: w * 0.55, sy: w * 0.55, sz: w * 0.55 }),
    },
    // leaf cluster offset 1
    {
      geom: { kind: "sphere", widthSegments: 12, heightSegments: 10 },
      mat: { color: "tint", roughness: 0.95 },
      compute: (w, h, _d) => ({ lx: w * 0.18, ly: h * 0.85, lz: w * 0.1, sx: w * 0.3, sy: w * 0.3, sz: w * 0.3 }),
    },
    // leaf cluster offset 2
    {
      geom: { kind: "sphere", widthSegments: 12, heightSegments: 10 },
      mat: { color: "tint", roughness: 0.95 },
      compute: (w, h, _d) => ({ lx: -w * 0.18, ly: h * 0.82, lz: -w * 0.1, sx: w * 0.32, sy: w * 0.32, sz: w * 0.32 }),
    },
    // leaf cluster top
    {
      geom: { kind: "sphere", widthSegments: 12, heightSegments: 10 },
      mat: { color: "tint", roughness: 0.95 },
      compute: (w, h, _d) => ({ lx: 0, ly: h * 0.95, lz: 0, sx: w * 0.25, sy: w * 0.25, sz: w * 0.25 }),
    },
  ],
};

// ---------------------------------------------------------------------------
// Fallback for unknown types: instance them as a simple box at item.size,
// centered at half-height (matches Table-ish footprint).
// ---------------------------------------------------------------------------
const FALLBACK_SUBPARTS: SubPart[] = [
  {
    geom: { kind: "box" },
    mat: { color: "tint" },
    compute: (w, h, d) => ({ lx: 0, ly: h / 2, lz: 0, sx: w, sy: h, sz: d }),
  },
];

// ---------------------------------------------------------------------------
// Geometry construction
// ---------------------------------------------------------------------------
function makeGeometry(g: GeomSpec): THREE.BufferGeometry {
  switch (g.kind) {
    case "box":
      return new THREE.BoxGeometry(1, 1, 1);
    case "cylinder":
      return new THREE.CylinderGeometry(
        g.radiusTop, g.radiusBottom, 1, g.radialSegments, 1, !!g.open
      );
    case "sphere":
      return new THREE.SphereGeometry(1, g.widthSegments, g.heightSegments);
    case "flatPlane": {
      const geom = new THREE.PlaneGeometry(1, 1);
      geom.rotateX(-Math.PI / 2);
      return geom;
    }
  }
}

// ---------------------------------------------------------------------------
// FurnitureInstanced component
// ---------------------------------------------------------------------------
export interface FurnitureInstancedProps {
  items: FurnitureItem[];
}

type ResolvedInstance = {
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
};

type ResolvedGroup = {
  // Stable key for React reconciliation across renders.
  key: string;
  type: string;
  subPartIndex: number;
  geomSpec: GeomSpec;
  matSpec: MatSpec;
  // Final resolved hex color for this group's material (string).
  resolvedColor: string;
  resolvedEmissive?: string;
  instances: ResolvedInstance[];
};

export default function FurnitureInstanced({ items }: FurnitureInstancedProps) {
  const groups: ResolvedGroup[] = useMemo(() => {
    // Bucket: type -> subPartIndex -> ResolvedGroup
    const byKey = new Map<string, ResolvedGroup>();

    for (const item of items) {
      const t = canonicalType(item.type);
      const parts = SUBPARTS[t] ?? FALLBACK_SUBPARTS;
      const tint = defaultTint(t);
      const [w, h, d] = item.size;
      const itemRot = item.rotation ?? 0;
      const cosR = Math.cos(itemRot);
      const sinR = Math.sin(itemRot);
      const [ix, iy, iz] = item.position;

      for (let idx = 0; idx < parts.length; idx++) {
        const part = parts[idx];
        const groupKey = `${t}::${idx}`;
        let group = byKey.get(groupKey);
        if (!group) {
          const resolvedColor = part.mat.color === "tint" ? tint : part.mat.color;
          const resolvedEmissive = part.mat.emissive === "tint"
            ? tint
            : part.mat.emissive;
          group = {
            key: groupKey,
            type: t,
            subPartIndex: idx,
            geomSpec: part.geom,
            matSpec: part.mat,
            resolvedColor,
            resolvedEmissive,
            instances: [],
          };
          byKey.set(groupKey, group);
        }

        const { lx, ly, lz, sx, sy, sz } = part.compute(w, h, d);
        // Rotate local (lx, lz) about Y by itemRot.
        const wx = ix + cosR * lx + sinR * lz;
        const wz = iz + -sinR * lx + cosR * lz;
        const wy = iy + ly;
        group.instances.push({
          position: [wx, wy, wz],
          rotation: [0, itemRot, 0],
          scale: [sx, sy, sz],
        });
      }
    }

    return Array.from(byKey.values());
  }, [items]);

  // Build geometries (keyed by group.key) and dispose them on unmount or change.
  const geomCacheRef = useRef<Map<string, THREE.BufferGeometry>>(new Map());
  const geometries: Record<string, THREE.BufferGeometry> = useMemo(() => {
    const cache = geomCacheRef.current;
    const out: Record<string, THREE.BufferGeometry> = {};
    const seen = new Set<string>();
    for (const g of groups) {
      const cacheKey = g.key + ":" + JSON.stringify(g.geomSpec);
      seen.add(cacheKey);
      let geom = cache.get(cacheKey);
      if (!geom) {
        geom = makeGeometry(g.geomSpec);
        cache.set(cacheKey, geom);
      }
      out[g.key] = geom;
    }
    // Dispose any cached geometries no longer in use.
    const stale: string[] = [];
    cache.forEach((geom, k) => {
      if (!seen.has(k)) {
        geom.dispose();
        stale.push(k);
      }
    });
    for (const k of stale) cache.delete(k);
    return out;
  }, [groups]);

  // Final cleanup on unmount.
  useEffect(() => {
    const cache = geomCacheRef.current;
    return () => {
      cache.forEach((geom) => geom.dispose());
      cache.clear();
    };
  }, []);

  return (
    <group>
      {groups.map((g) => {
        const geom = geometries[g.key];
        // Generous fixed cap so the underlying buffer is large enough across
        // re-renders. drei allocates this once at mount and cannot grow it.
        const LIMIT = 2048;
        return (
          <Instances
            key={g.key}
            limit={LIMIT}
            range={g.instances.length}
            castShadow={false}
            receiveShadow={false}
          >
            <primitive object={geom} attach="geometry" />
            <meshStandardMaterial
              color={g.resolvedColor}
              roughness={g.matSpec.roughness}
              metalness={g.matSpec.metalness}
              emissive={g.resolvedEmissive}
              emissiveIntensity={g.matSpec.emissiveIntensity}
              side={g.matSpec.doubleSide ? THREE.DoubleSide : THREE.FrontSide}
            />
            {g.instances.map((inst, i) => (
              <Instance
                key={i}
                position={inst.position}
                rotation={inst.rotation}
                scale={inst.scale}
              />
            ))}
          </Instances>
        );
      })}
    </group>
  );
}

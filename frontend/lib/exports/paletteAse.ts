// Encodes a list of hex colors into Adobe Swatch Exchange (.ase) format.
// Spec reference: https://www.selapa.net/swatches/colors/fileformats.php#adobe_ase
//
// File layout:
//   "ASEF" magic, version u16+u16, u32 block count
//   For each block: u16 type (0xC001 group start, 0x0001 color, 0xC002 group end)
//                   u32 length, payload
//   Color payload: u16 nameLen, UTF-16BE name + 0x0000 terminator,
//                  4-byte color model "RGB ", 3 × float32 (R,G,B in 0-1),
//                  u16 color type (0=global, 1=spot, 2=normal)

export function buildPaletteAse(palette: string[], groupName = "Conjure Palette"): Uint8Array {
  const colors = palette
    .map((h) => parseHex(h))
    .filter((c): c is { hex: string; r: number; g: number; b: number } => c !== null);

  // 1 group-start + 1 block per color + 1 group-end
  const blockCount = colors.length + 2;

  const chunks: Uint8Array[] = [];
  // header
  chunks.push(asciiBytes("ASEF"));
  chunks.push(u16(1), u16(0)); // version 1.0
  chunks.push(u32(blockCount));

  // group start
  const groupNameBytes = utf16beNullTerminated(groupName);
  const groupPayload = concat(u16(groupNameBytes.length / 2 - 1), groupNameBytes); // length excludes terminator? we follow common ASE files: include the full string + terminator, with length being the count of UTF-16 units excluding terminator.
  chunks.push(u16(0xc001));
  chunks.push(u32(groupPayload.length));
  chunks.push(groupPayload);

  // colors
  for (const c of colors) {
    const nameBytes = utf16beNullTerminated(c.hex);
    const nameLenUnits = nameBytes.length / 2 - 1;
    const payload = concat(
      u16(nameLenUnits),
      nameBytes,
      asciiBytes("RGB "),
      f32(c.r),
      f32(c.g),
      f32(c.b),
      u16(2), // normal
    );
    chunks.push(u16(0x0001));
    chunks.push(u32(payload.length));
    chunks.push(payload);
  }

  // group end
  chunks.push(u16(0xc002));
  chunks.push(u32(0));

  return concat(...chunks);
}

function parseHex(h: string): { hex: string; r: number; g: number; b: number } | null {
  const s = h.trim().replace(/^#/, "");
  if (!/^[0-9a-fA-F]{6}$/.test(s)) return null;
  const r = parseInt(s.slice(0, 2), 16) / 255;
  const g = parseInt(s.slice(2, 4), 16) / 255;
  const b = parseInt(s.slice(4, 6), 16) / 255;
  return { hex: `#${s.toUpperCase()}`, r, g, b };
}

function asciiBytes(s: string): Uint8Array {
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i) & 0xff;
  return out;
}

function utf16beNullTerminated(s: string): Uint8Array {
  const buf = new Uint8Array((s.length + 1) * 2);
  for (let i = 0; i < s.length; i++) {
    const code = s.charCodeAt(i);
    buf[i * 2] = (code >> 8) & 0xff;
    buf[i * 2 + 1] = code & 0xff;
  }
  return buf;
}

function u16(n: number): Uint8Array {
  return new Uint8Array([(n >> 8) & 0xff, n & 0xff]);
}

function u32(n: number): Uint8Array {
  return new Uint8Array([
    (n >>> 24) & 0xff,
    (n >>> 16) & 0xff,
    (n >>> 8) & 0xff,
    n & 0xff,
  ]);
}

function f32(v: number): Uint8Array {
  const buf = new ArrayBuffer(4);
  new DataView(buf).setFloat32(0, v, false); // big endian
  return new Uint8Array(buf);
}

function concat(...parts: Uint8Array[]): Uint8Array {
  let total = 0;
  for (const p of parts) total += p.length;
  const out = new Uint8Array(total);
  let off = 0;
  for (const p of parts) {
    out.set(p, off);
    off += p.length;
  }
  return out;
}

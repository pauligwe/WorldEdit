import { NextResponse } from "next/server";
import path from "node:path";
import fs from "node:fs/promises";

// POST { id: string, dataUrl: "data:image/png;base64,..." }
// Writes public/worlds/<id>.jpg with the captured frame.
export async function POST(req: Request) {
  try {
    const { id, dataUrl } = await req.json();
    if (typeof id !== "string" || !/^[a-z0-9_-]+$/i.test(id)) {
      return NextResponse.json({ error: "bad id" }, { status: 400 });
    }
    if (typeof dataUrl !== "string" || !dataUrl.startsWith("data:image/")) {
      return NextResponse.json({ error: "bad dataUrl" }, { status: 400 });
    }
    const base64 = dataUrl.split(",", 2)[1];
    if (!base64) return NextResponse.json({ error: "bad dataUrl" }, { status: 400 });
    const bytes = Buffer.from(base64, "base64");
    const out = path.join(process.cwd(), "public", "worlds", `${id}.jpg`);
    await fs.writeFile(out, bytes);
    return NextResponse.json({ ok: true, path: `/worlds/${id}.jpg` });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}

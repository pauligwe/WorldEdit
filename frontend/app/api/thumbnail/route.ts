import { NextResponse } from "next/server";
import path from "node:path";
import fs from "node:fs/promises";
import { v2 as cloudinary } from "cloudinary";

// POST { id: string, dataUrl: "data:image/png;base64,..." }
// Writes public/worlds/<id>.jpg with the captured frame, AND uploads to
// Cloudinary as conjure/worlds/<id> when CLOUDINARY_API_SECRET is set.
// Local write is the source of truth — Cloudinary upload is best-effort.
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

    let cloudinaryUrl: string | null = null;
    if (
      process.env.CLOUDINARY_API_SECRET &&
      (process.env.CLOUDINARY_CLOUD_NAME || process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME)
    ) {
      try {
        cloudinary.config({
          cloud_name:
            process.env.CLOUDINARY_CLOUD_NAME ??
            process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME,
          api_key: process.env.CLOUDINARY_API_KEY,
          api_secret: process.env.CLOUDINARY_API_SECRET,
        });
        const res = await cloudinary.uploader.upload(dataUrl, {
          public_id: `conjure/worlds/${id}`,
          overwrite: true,
          resource_type: "image",
        });
        cloudinaryUrl = res.secure_url;
      } catch (err) {
        console.warn("[thumbnail] Cloudinary upload failed, kept local file:", err);
      }
    }

    return NextResponse.json({
      ok: true,
      path: `/worlds/${id}.jpg`,
      cloudinaryUrl,
    });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}

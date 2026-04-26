#!/usr/bin/env node
// Uploads frontend/public/worlds/*.jpg to Cloudinary under conjure/worlds/<id>.
// Requires CLOUDINARY_URL or (CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET) in env.
//
//   cd frontend && node scripts/upload-world-thumbnails.mjs
import { v2 as cloudinary } from "cloudinary";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const WORLDS_DIR = path.join(ROOT, "public", "worlds");

if (!process.env.CLOUDINARY_URL && !process.env.CLOUDINARY_CLOUD_NAME) {
  console.error("Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET first.");
  process.exit(1);
}

if (!process.env.CLOUDINARY_URL) {
  cloudinary.config({
    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
    api_key: process.env.CLOUDINARY_API_KEY,
    api_secret: process.env.CLOUDINARY_API_SECRET,
  });
}

const files = (await fs.readdir(WORLDS_DIR)).filter((f) => /\.(jpe?g|png|webp)$/i.test(f));
if (files.length === 0) {
  console.log("No thumbnails found in", WORLDS_DIR);
  process.exit(0);
}

for (const f of files) {
  const id = path.basename(f, path.extname(f));
  const publicId = `conjure/worlds/${id}`;
  const filePath = path.join(WORLDS_DIR, f);
  process.stdout.write(`uploading ${f} → ${publicId} ... `);
  try {
    const res = await cloudinary.uploader.upload(filePath, {
      public_id: publicId,
      overwrite: true,
      resource_type: "image",
    });
    console.log("ok", res.secure_url);
  } catch (err) {
    console.log("FAILED", err?.message ?? err);
  }
}

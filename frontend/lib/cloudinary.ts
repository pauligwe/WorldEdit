export const CLOUDINARY_CLOUD_NAME =
  process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME ?? "";

export const CLOUDINARY_UPLOAD_PRESET =
  process.env.NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET ?? "";

export const CLOUDINARY_FOLDER = "conjure";

export const isCloudinaryConfigured = Boolean(CLOUDINARY_CLOUD_NAME);

export function cloudinaryUrl(publicId: string, transform = "f_auto,q_auto"): string {
  return `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/${transform}/${publicId}`;
}

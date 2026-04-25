"use client";
export default function CrosshairHUD() {
  return (
    <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
      <div className="w-2 h-2 rounded-full bg-white/80 mix-blend-difference" />
    </div>
  );
}

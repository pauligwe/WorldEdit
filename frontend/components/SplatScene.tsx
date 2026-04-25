"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import PlayerControls from "./PlayerControls";
import CrosshairHUD from "./CrosshairHUD";
import { loadSpark } from "@/lib/sparkLoader";

interface Pose {
  spawn: [number, number, number];
  yaw: number;
  pitch: number;
}

interface Props {
  splatUrl: string;
  spawn: [number, number, number];
  yaw?: number;
  pitch?: number;
  thumbnailUrl?: string;
  captureMode?: { id: string; force?: boolean };
}

function SplatObject({ url }: { url: string }) {
  const { scene } = useThree();
  const meshRef = useRef<any>(null);

  useEffect(() => {
    let disposed = false;
    loadSpark().then((spark) => {
      if (disposed) return;
      const mesh = new spark.SplatMesh({ url });
      mesh.quaternion.set(0, 1, 0, 0);
      meshRef.current = mesh;
      scene.add(mesh);
    }).catch((err) => console.error("[spark] load failed", err));
    return () => {
      disposed = true;
      const m = meshRef.current;
      if (m) {
        scene.remove(m);
        m.dispose?.();
        meshRef.current = null;
      }
    };
  }, [url, scene]);

  return null;
}

function CameraSpawn({
  spawn,
  yaw,
  pitch,
}: {
  spawn: [number, number, number];
  yaw: number;
  pitch: number;
}) {
  const { camera } = useThree();
  const placed = useRef(false);
  useEffect(() => {
    if (placed.current) return;
    camera.position.set(spawn[0], spawn[1], spawn[2]);
    camera.up.set(0, 1, 0);
    camera.rotation.order = "YXZ";
    camera.rotation.set(pitch, yaw, 0);
    camera.updateProjectionMatrix();
    placed.current = true;
  }, [spawn, yaw, pitch, camera]);
  return null;
}

// Polls the camera pose every frame and pushes it up to the parent so a fixed
// HUD outside <Canvas> can show live spawn/yaw/pitch for tuning new worlds.
function PoseReadout({ onChange }: { onChange: (p: Pose) => void }) {
  const { camera } = useThree();
  useFrame(() => {
    onChange({
      spawn: [camera.position.x, camera.position.y, camera.position.z],
      yaw: camera.rotation.y,
      pitch: camera.rotation.x,
    });
  });
  return null;
}

// Exposes a `captureRef.current()` method that the parent calls to grab a PNG
// of the current frame. Lives inside <Canvas> because R3F's `useThree` only
// works in canvas children.
function CaptureBridge({ captureRef }: { captureRef: React.MutableRefObject<(() => string | null) | null> }) {
  const { gl, scene, camera } = useThree();
  useEffect(() => {
    captureRef.current = () => {
      try {
        gl.render(scene, camera);
        return gl.domElement.toDataURL("image/jpeg", 0.85);
      } catch (err) {
        console.error("[capture] failed", err);
        return null;
      }
    };
    return () => { captureRef.current = null; };
  }, [gl, scene, camera, captureRef]);
  return null;
}

export default function SplatScene({
  splatUrl,
  spawn,
  yaw = 0,
  pitch = 0,
  thumbnailUrl,
  captureMode,
}: Props) {
  const [sparkReady, setSparkReady] = useState(false);
  const [captureMsg, setCaptureMsg] = useState<string | null>(null);
  const [pose, setPose] = useState<Pose>({ spawn, yaw, pitch });
  const [copied, setCopied] = useState(false);
  const captureRef = useRef<(() => string | null) | null>(null);
  const autoFiredRef = useRef(false);
  const lastPoseTickRef = useRef(0);

  // Throttle pose state updates to ~5 Hz so we're not re-rendering the whole
  // tree every frame just to refresh a debug readout.
  const onPoseChange = useCallback((p: Pose) => {
    const now = performance.now();
    if (now - lastPoseTickRef.current < 200) return;
    lastPoseTickRef.current = now;
    setPose(p);
  }, []);

  const copyPose = useCallback(async () => {
    const text = `spawn: [${pose.spawn[0].toFixed(2)}, ${pose.spawn[1].toFixed(2)}, ${pose.spawn[2].toFixed(2)}], yaw: ${pose.yaw.toFixed(3)}, pitch: ${pose.pitch.toFixed(3)}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {}
  }, [pose]);

  useEffect(() => {
    loadSpark().then(() => setSparkReady(true)).catch(() => setSparkReady(true));
  }, []);

  const runCapture = useCallback(async () => {
    if (!captureMode) return;
    const fn = captureRef.current;
    if (!fn) return;
    const dataUrl = fn();
    if (!dataUrl) {
      setCaptureMsg("capture failed");
      return;
    }
    setCaptureMsg("saving thumbnail…");
    try {
      const res = await fetch("/api/thumbnail", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: captureMode.id, dataUrl }),
      });
      const json = await res.json();
      if (json.ok) setCaptureMsg(`saved ${json.path}`);
      else setCaptureMsg(`error: ${json.error ?? "unknown"}`);
    } catch (err) {
      setCaptureMsg(`error: ${String(err)}`);
    }
    setTimeout(() => setCaptureMsg(null), 3000);
  }, [captureMode]);

  // Auto-capture once the splat has had time to render. Skip if a thumbnail
  // already exists at thumbnailUrl (unless `force` is set via ?capture=1).
  useEffect(() => {
    if (!captureMode || !sparkReady) return;
    if (autoFiredRef.current) return;
    autoFiredRef.current = true;

    let cancelled = false;
    (async () => {
      if (!captureMode.force && thumbnailUrl) {
        try {
          const head = await fetch(thumbnailUrl, { method: "HEAD" });
          if (head.ok) return; // already have a thumbnail
        } catch {}
      }
      // Wait for splat to actually render a few frames before capturing.
      await new Promise((r) => setTimeout(r, 1500));
      if (cancelled) return;
      await runCapture();
    })();
    return () => {
      cancelled = true;
    };
  }, [captureMode, sparkReady, thumbnailUrl, runCapture]);

  return (
    <div className="fixed inset-0 bg-black">
      <Canvas
        camera={{ fov: 70, position: spawn, near: 0.05, far: 500 }}
        dpr={[1, 1.5]}
        gl={{
          antialias: false,
          powerPreference: "high-performance",
          // Required so we can read the canvas back via toDataURL.
          preserveDrawingBuffer: !!captureMode,
        }}
        shadows={false}
      >
        <color attach="background" args={["#0a0a0a"]} />
        <ambientLight intensity={1.0} />
        {sparkReady && <SplatObject url={splatUrl} />}
        <CameraSpawn spawn={spawn} yaw={yaw} pitch={pitch} />
        <PlayerControls walls={[]} spawn={spawn} />
        {captureMode && <CaptureBridge captureRef={captureRef} />}
        <PoseReadout onChange={onPoseChange} />
      </Canvas>
      <CrosshairHUD />
      {!sparkReady && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-zinc-300 text-sm font-mono bg-black/60 px-4 py-2 rounded-full">
            loading…
          </div>
        </div>
      )}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs font-mono text-zinc-300 bg-black/70 px-3 py-2 rounded pointer-events-none">
        click to lock · WASD · Space up · Ctrl down · Esc to release
      </div>
      {captureMode && captureMsg && (
        <div className="absolute top-4 right-4 z-10 text-xs font-mono bg-white/90 text-on-surface px-3 py-1.5 rounded shadow-soft border border-outline-variant pointer-events-none">
          {captureMsg}
        </div>
      )}
      <div className="absolute bottom-4 right-4 z-10 text-xs font-mono bg-white/90 text-on-surface px-3 py-2 rounded shadow-soft border border-outline-variant pointer-events-auto flex items-center gap-2">
        <span>
          spawn: [{pose.spawn[0].toFixed(2)}, {pose.spawn[1].toFixed(2)}, {pose.spawn[2].toFixed(2)}] · yaw: {pose.yaw.toFixed(3)} · pitch: {pose.pitch.toFixed(3)}
        </span>
        <button onClick={copyPose} className="text-xs font-medium bg-primary text-on-primary px-2 py-0.5 rounded hover:opacity-90">
          {copied ? "copied" : "copy"}
        </button>
      </div>
    </div>
  );
}

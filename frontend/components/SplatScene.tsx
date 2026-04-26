"use client";
import { useEffect, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import PlayerControls from "./PlayerControls";
import CrosshairHUD from "./CrosshairHUD";
import AgentSidebar, { AGENT_SIDEBAR_WIDTH } from "./AgentSidebar";
import { loadSpark } from "@/lib/sparkLoader";

interface Props {
  splatUrl: string;
  spawn: [number, number, number];
  yaw?: number;
  pitch?: number;
  thumbnailUrl?: string;
  captureMode?: { id: string; force?: boolean; reset?: boolean };
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

type Capture3Result = { thumbnail: string | null; views: [string, string, string] | null };
type Capture3Fn = () => Promise<Capture3Result>;

// Async capture: rotates the camera across yaw thirds, waits a few RAFs between
// each so Spark's splat material has a chance to redraw at the new angle, and
// reads the canvas after each settled frame. Synchronous gl.render() alone
// produced black frames because Spark's per-frame state hadn't updated.
function PerceptionCaptureBridge({
  captureRef,
}: { captureRef: React.MutableRefObject<Capture3Fn | null> }) {
  const { gl, scene, camera } = useThree();
  useEffect(() => {
    const waitFrames = (n: number) =>
      new Promise<void>((resolve) => {
        let i = 0;
        function tick() {
          if (++i >= n) resolve();
          else requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      });

    captureRef.current = async () => {
      try {
        const cam = camera as any;
        const originalYaw = cam.rotation.y;
        await waitFrames(3);
        gl.render(scene, camera);
        const thumbnail = gl.domElement.toDataURL("image/jpeg", 0.85);

        const views: string[] = [];
        const yawOffsets = [0, (2 * Math.PI) / 3, (4 * Math.PI) / 3];
        for (const off of yawOffsets) {
          cam.rotation.y = originalYaw + off;
          cam.updateMatrixWorld(true);
          await waitFrames(3);
          gl.render(scene, camera);
          views.push(gl.domElement.toDataURL("image/jpeg", 0.85));
        }
        cam.rotation.y = originalYaw;
        cam.updateMatrixWorld(true);
        await waitFrames(2);
        gl.render(scene, camera);

        return { thumbnail, views: [views[0], views[1], views[2]] as [string, string, string] };
      } catch (err) {
        console.error("[perception capture] failed", err);
        return { thumbnail: null, views: null };
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const captureRef = useRef<(() => string | null) | null>(null);
  const perceptionRef = useRef<Capture3Fn | null>(null);
  const autoFiredRef = useRef(false);

  useEffect(() => {
    loadSpark().then(() => setSparkReady(true)).catch(() => setSparkReady(true));
  }, []);

  // Auto-capture once the splat has had time to render. Skip if a thumbnail
  // already exists at thumbnailUrl (unless `force` is set via ?capture=1).
  // Captures 3 yaw-rotated perception views and triggers the analyze pipeline.
  useEffect(() => {
    if (!captureMode || !sparkReady) return;
    if (autoFiredRef.current) return;
    autoFiredRef.current = true;

    let cancelled = false;
    (async () => {
      if (captureMode.reset) {
        setCaptureMsg("resetting…");
        try {
          await fetch(`http://localhost:8000/api/analyze/${captureMode.id}/reset`, {
            method: "POST",
          });
        } catch {}
      }
      if (!captureMode.force && thumbnailUrl) {
        try {
          const head = await fetch(thumbnailUrl, { method: "HEAD" });
          if (head.ok) return;
        } catch {}
      }
      await new Promise((r) => setTimeout(r, 1500));
      if (cancelled) return;

      const fn = perceptionRef.current;
      if (!fn) return;
      const { thumbnail, views } = await fn();
      if (cancelled) return;
      if (!thumbnail || !views) {
        setCaptureMsg("capture failed");
        return;
      }
      setCaptureMsg("saving thumbnail…");
      try {
        await fetch("/api/thumbnail", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: captureMode.id, dataUrl: thumbnail }),
        });
      } catch {}

      setCaptureMsg("saving perception frames…");
      try {
        const res = await fetch("http://localhost:8000/api/perception-frames", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            world_id: captureMode.id,
            view_0:   views[0],
            view_120: views[1],
            view_240: views[2],
          }),
        });
        if (!res.ok) {
          setCaptureMsg(`perception frames failed: ${res.status}`);
          return;
        }
      } catch (err) {
        setCaptureMsg(`perception frames error: ${String(err)}`);
        return;
      }

      setCaptureMsg("dispatching agents…");
      try {
        await fetch(`http://localhost:8000/api/analyze/${captureMode.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: "" }),
        });
        setCaptureMsg("agents running…");
      } catch (err) {
        setCaptureMsg(`analyze trigger failed: ${String(err)}`);
        return;
      }

      setTimeout(() => setCaptureMsg(null), 4000);
    })();
    return () => {
      cancelled = true;
    };
  }, [captureMode, sparkReady, thumbnailUrl]);

  const sceneInset = sidebarOpen ? AGENT_SIDEBAR_WIDTH : 0;

  // When the sidebar opens, release pointer lock so the user can interact with
  // the panel (clicking cards, agent nodes) without the camera moving. We also
  // disable pointer-events on the scene container so a stray click on the
  // canvas behind the panel doesn't re-grab the lock.
  useEffect(() => {
    if (sidebarOpen && document.pointerLockElement) {
      document.exitPointerLock();
    }
  }, [sidebarOpen]);

  return (
    <div
      className="fixed inset-0 bg-black transition-[right] duration-300"
      style={{ right: sceneInset }}
    >
      <Canvas
        id="splat-lock-target"
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
        <PlayerControls walls={[]} spawn={spawn} enabled={!sidebarOpen} />
        {captureMode && <CaptureBridge captureRef={captureRef} />}
        {captureMode && <PerceptionCaptureBridge captureRef={perceptionRef} />}
      </Canvas>
      <CrosshairHUD />
      {!sparkReady && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-zinc-300 text-sm font-sans bg-black/60 px-4 py-2 rounded-full">
            loading…
          </div>
        </div>
      )}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs font-sans text-zinc-300 bg-black/70 px-3 py-2 rounded pointer-events-none">
        click to lock · WASD · Space up · Ctrl down · Esc to release
      </div>
      {captureMode && captureMsg && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 text-xs font-sans bg-white/90 text-on-surface px-3 py-1.5 rounded shadow-soft border border-outline-variant pointer-events-none">
          {captureMsg}
        </div>
      )}
      {captureMode && (
        <AgentSidebar
          worldId={captureMode.id}
          open={sidebarOpen}
          onOpenChange={setSidebarOpen}
        />
      )}
    </div>
  );
}

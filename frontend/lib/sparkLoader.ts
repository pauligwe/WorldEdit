// Load Spark in the browser without webpack touching its bundle.
// We fetch the CJS source as text, wrap it in a function that provides
// `exports` and `module`, and eval it. Spark's CJS bundle inlines its WASM
// as a base64 data URL, so it has no other external dependencies aside from
// `three`, which we hand it via a require shim that returns the app's THREE
// instance (so meshes share state with R3F's scene).
import * as THREE from "three";

let cachedPromise: Promise<any> | null = null;

export function loadSpark(): Promise<any> {
  if (typeof window === "undefined") return Promise.reject(new Error("ssr"));
  if (cachedPromise) return cachedPromise;

  cachedPromise = (async () => {
    const res = await fetch("/spark.cjs.js");
    if (!res.ok) throw new Error(`spark fetch failed: ${res.status}`);
    const src = await res.text();
    const moduleObj: any = { exports: {} };
    const requireShim = (name: string) => {
      if (name === "three") return THREE;
      throw new Error(`spark requested unsupported require: ${name}`);
    };
    // eslint-disable-next-line no-new-func
    const fn = new Function("module", "exports", "require", src);
    fn(moduleObj, moduleObj.exports, requireShim);
    return moduleObj.exports;
  })();

  return cachedPromise;
}

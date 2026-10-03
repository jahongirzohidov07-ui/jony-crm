import { api } from "./api";

/**
 * TELEFONGA BILDIRISHNOMA (2026-10-03). Jony Student ilovasida
 * o'quvchining qurilmasini serverga yozadi (api/push.py) — imtihon
 * ochilsa/boshlansa telefonga xabar keladi.
 */

function urlB64ToBytes(s: string): Uint8Array {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const raw = atob((s + pad).replace(/-/g, "+").replace(/_/g, "/"));
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

export function pushSupported(): boolean {
  return typeof window !== "undefined" &&
    "serviceWorker" in navigator && "PushManager" in window &&
    "Notification" in window;
}

export function pushPermission(): NotificationPermission | "unsupported" {
  return pushSupported() ? Notification.permission : "unsupported";
}

/** Ruxsat bor bo'lsa — obunani yangilab serverga yozadi. ask=true bo'lsa
 *  ruxsat so'raydi (faqat foydalanuvchi tugma bosganda chaqirilsin). */
export async function ensurePush(ask = false): Promise<boolean> {
  if (!pushSupported()) return false;
  let perm = Notification.permission;
  if (perm === "default" && ask) perm = await Notification.requestPermission();
  if (perm !== "granted") return false;
  const reg = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    const { key } = await api.get<{ key: string }>("/push/key");
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlB64ToBytes(key) as BufferSource,
    });
  }
  await api.post("/push/subscribe", sub.toJSON());
  return true;
}

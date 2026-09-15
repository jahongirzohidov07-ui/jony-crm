type Notice = { id: string; date?: string | null };
export type NotificationFeed = { student_id: number; items: Notice[]; latest: string | null };
const memory = new Map<string, Set<string>>();
const key = (id: number) => `jonyos_notif_read:${id}`;
export function readNotifications(id: number): Set<string> {
  if (!Number.isInteger(id) || id <= 0) return new Set();
  try {
    const saved = JSON.parse(localStorage.getItem(key(id)) || "[]");
    const ids = Array.isArray(saved) ? saved.filter(v => typeof v === "string") : [];
    return new Set([...ids, ...(memory.get(key(id)) || [])]);
  } catch { return new Set(memory.get(key(id)) || []); }
}
export function markNotificationsRead(id: number, items: Notice[]): Set<string> {
  if (!Number.isInteger(id) || id <= 0) return new Set();
  const read = readNotifications(id);
  items.forEach(n => read.add(n.id));
  memory.set(key(id), read);
  try { localStorage.setItem(key(id), JSON.stringify([...read])); } catch { /* Keep usable in this session. */ }
  return new Set(read);
}
export function hasUnreadNotifications(feed: NotificationFeed): boolean {
  const read = readNotifications(feed.student_id);
  return feed.items.some(n => !read.has(n.id));
}

type Listener = (online: boolean) => void;

const listeners = new Set<Listener>();

if (typeof window !== "undefined") {
  window.addEventListener("online", () => notify(true));
  window.addEventListener("offline", () => notify(false));
}

function notify(online: boolean) {
  for (const fn of listeners) fn(online);
}

export function isOnline(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine;
}

export function subscribeOnline(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

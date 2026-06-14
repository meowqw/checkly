import { getCache, setCache } from "@/lib/offline/cache";

const TEMP_ID_MAP_KEY = "meta:tempIdMap";

export async function loadTempIdMap(): Promise<Map<string, string>> {
  const raw = await getCache<Record<string, string>>(TEMP_ID_MAP_KEY);
  return new Map(Object.entries(raw ?? {}));
}

export async function saveTempId(tempId: string, serverId: string): Promise<void> {
  const map = await loadTempIdMap();
  map.set(tempId, serverId);
  await setCache(TEMP_ID_MAP_KEY, Object.fromEntries(map));
}

export async function resolveTempId(tempId: string, map: Map<string, string>): Promise<string> {
  if (!tempId.startsWith("local_")) return tempId;
  const mapped = map.get(tempId);
  if (!mapped) throw new Error(`Waiting for sync: ${tempId}`);
  return mapped;
}

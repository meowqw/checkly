import { getDb } from "@/lib/offline/db";
import type { QueuedOp } from "@/lib/offline/types";

let onQueueChange: (() => void) | null = null;

export function setQueueChangeListener(listener: (() => void) | null) {
  onQueueChange = listener;
}

function notifyQueueChange() {
  onQueueChange?.();
}

export async function enqueue(op: QueuedOp): Promise<void> {
  const db = await getDb();
  await db.put("queue", op, op.id);
  notifyQueueChange();
}

export async function listQueue(): Promise<QueuedOp[]> {
  const db = await getDb();
  const ops = await db.getAll("queue");
  return ops.sort((a, b) => a.createdAt - b.createdAt);
}

export async function dequeue(id: string): Promise<void> {
  const db = await getDb();
  await db.delete("queue", id);
  notifyQueueChange();
}

export async function queueLength(): Promise<number> {
  const db = await getDb();
  return db.count("queue");
}

export function newOpId(): string {
  return crypto.randomUUID();
}

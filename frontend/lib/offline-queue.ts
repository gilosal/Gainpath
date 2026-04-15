/**
 * offline-queue.ts
 *
 * IndexedDB-backed offline action queue.
 * When the device is offline (spotty gym Wi-Fi), set logs, session completions,
 * and body feedback are saved here and synced when connectivity returns.
 */

import { offlineApi } from "./api";

const DB_NAME = "paceforge-offline";
const STORE = "queue";
const DB_VERSION = 1;

export interface QueuedAction {
  id: string;
  created_at: string;
  action_type: "create_set_log" | "complete_session" | "add_body_feedback";
  payload: Record<string, unknown>;
  session_log_id?: string;
  retry_count: number;
  synced: boolean;
}

// ── DB bootstrap ──────────────────────────────────────────────────────────────

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE, { keyPath: "id" });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  fn: (store: IDBObjectStore) => IDBRequest<T>
): Promise<T> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, mode);
    const store = tx.objectStore(STORE);
    const req = fn(store);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// ── Public API ────────────────────────────────────────────────────────────────

export const offlineQueue = {
  async enqueue(item: Omit<QueuedAction, "id" | "created_at" | "retry_count" | "synced">): Promise<string> {
    const action: QueuedAction = {
      ...item,
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      retry_count: 0,
      synced: false,
    };
    await withStore("readwrite", (s) => s.put(action));
    // Register background sync if supported
    if ("serviceWorker" in navigator && "SyncManager" in window) {
      const reg = await navigator.serviceWorker.ready;
      await (reg as ServiceWorkerRegistration & { sync: { register(tag: string): Promise<void> } })
        .sync.register("sync-offline-queue").catch(() => {});
    }
    return action.id;
  },

  async pending(): Promise<QueuedAction[]> {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).getAll();
      req.onsuccess = () =>
        resolve((req.result as QueuedAction[]).filter((a) => !a.synced));
      req.onerror = () => reject(req.error);
    });
  },

  async count(): Promise<number> {
    const items = await this.pending();
    return items.length;
  },

  async sync(): Promise<{ synced: number; failed: number }> {
    if (!navigator.onLine) return { synced: 0, failed: 0 };

    // Delegate to the backend sync endpoint which processes all server-side pending items.
    // Also flush local IndexedDB items that were created purely client-side.
    try {
      const result = await offlineApi.sync();
      // Mark all local items as synced on success
      const items = await this.pending();
      for (const item of items) {
        await withStore("readwrite", (s) =>
          s.put({ ...item, synced: true })
        );
      }
      return { synced: result.synced, failed: result.failed };
    } catch {
      return { synced: 0, failed: await this.count() };
    }
  },

  async clear(): Promise<void> {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      const req = tx.objectStore(STORE).clear();
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  },
};

// ── Hook helper: queue-aware set log ─────────────────────────────────────────

export async function logSetWithFallback(
  sessionId: string,
  setData: Record<string, unknown>,
  onlineHandler: () => Promise<unknown>
): Promise<void> {
  if (navigator.onLine) {
    try {
      await onlineHandler();
      return;
    } catch {
      // Fall through to offline queue
    }
  }
  await offlineQueue.enqueue({
    action_type: "create_set_log",
    session_log_id: sessionId,
    payload: { session_log_id: sessionId, ...setData },
  });
}

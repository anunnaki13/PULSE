import { useEffect, useRef, useState } from "react";
import { saveSelfAssessment, type SelfAssessmentSavePayload } from "@/lib/phase2-api";

const DB_NAME = "pulse-assessment-queue";
const STORE = "pending_saves";
let initialQueueFlushStarted = false;

type QueueItem = SelfAssessmentSavePayload & { queued_at: number };

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE, { keyPath: "id" });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function putQueued(item: QueueItem) {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

async function deleteQueued(id: string) {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

async function allQueued(): Promise<QueueItem[]> {
  const db = await openDb();
  const rows = await new Promise<QueueItem[]>((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result as QueueItem[]);
    req.onerror = () => reject(req.error);
  });
  db.close();
  return rows.sort((a, b) => a.queued_at - b.queued_at);
}

export function useAssessmentAutoSave(payload: SelfAssessmentSavePayload | null, enabled: boolean) {
  const [state, setState] = useState<"idle" | "saving" | "saved" | "queued" | "error">("idle");
  const latest = useRef(payload);
  const lastPersistedSignature = useRef<string | null>(null);
  latest.current = payload;

  async function flushQueue() {
    if (typeof indexedDB === "undefined") return;
    for (const row of await allQueued()) {
      try {
        await saveSelfAssessment(row);
        await deleteQueued(row.id);
        setState("saved");
      } catch {
        setState("queued");
        return;
      }
    }
  }

  useEffect(() => {
    if (!enabled || !payload) {
      lastPersistedSignature.current = null;
      return;
    }
    const signature = JSON.stringify(payload);
    if (lastPersistedSignature.current === null) {
      lastPersistedSignature.current = signature;
      return;
    }
    if (signature === lastPersistedSignature.current) return;
    const timer = window.setTimeout(async () => {
      const current = latest.current;
      if (!current) return;
      setState("saving");
      try {
        await flushQueue();
        await saveSelfAssessment(current);
        lastPersistedSignature.current = signature;
        setState("saved");
      } catch {
        if (typeof indexedDB === "undefined") {
          setState("error");
          return;
        }
        await putQueued({ ...current, queued_at: Date.now() });
        lastPersistedSignature.current = signature;
        setState("queued");
      }
    }, 5000);
    return () => window.clearTimeout(timer);
  }, [enabled, payload]);

  useEffect(() => {
    const onOnline = () => void flushQueue();
    window.addEventListener("online", onOnline);
    if (!initialQueueFlushStarted) {
      initialQueueFlushStarted = true;
      void flushQueue();
    }
    return () => window.removeEventListener("online", onOnline);
  }, []);

  return state;
}

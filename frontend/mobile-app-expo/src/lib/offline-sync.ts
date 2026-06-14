/**
 * [PHASE5] Offline-first sync for mobile.
 * Persists messages locally, syncs with backend when online.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import NetInfo from "@react-native-async-storage/async-storage";

const MESSAGE_QUEUE_KEY = "@adam_prism:message_queue";
const SYNC_STATUS_KEY = "@adam_prism:sync_status";

export interface QueuedMessage {
  id: string;
  session_id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: number;
  retries: number;
  last_error?: string;
}

export type SyncStatus = "idle" | "syncing" | "error" | "offline";

export class OfflineSyncManager {
  private syncing = false;

  /**
   * [PHASE5] Queue a message for later sync (used when offline).
   */
  async enqueue(message: Omit<QueuedMessage, "retries">): Promise<void> {
    const queue = await this.getQueue();
    queue.push({ ...message, retries: 0 });
    await AsyncStorage.setItem(MESSAGE_QUEUE_KEY, JSON.stringify(queue));
  }

  /**
   * [PHASE5] Get all queued messages.
   */
  async getQueue(): Promise<QueuedMessage[]> {
    const raw = await AsyncStorage.getItem(MESSAGE_QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  }

  /**
   * [PHASE5] Clear the queue.
   */
  async clearQueue(): Promise<void> {
    await AsyncStorage.removeItem(MESSAGE_QUEUE_KEY);
  }

  /**
   * [PHASE5] Sync queued messages with backend.
   * Should be called when:
   *  - App comes to foreground
   *  - Network reconnects
   *  - User manually triggers sync
   */
  async syncWithBackend(
    apiBase: string,
    authToken: string | null,
  ): Promise<{ synced: number; failed: number; status: SyncStatus }> {
    if (this.syncing) {
      return { synced: 0, failed: 0, status: "syncing" };
    }

    this.syncing = true;
    await this.setSyncStatus("syncing");

    const queue = await this.getQueue();
    if (queue.length === 0) {
      this.syncing = false;
      await this.setSyncStatus("idle");
      return { synced: 0, failed: 0, status: "idle" };
    }

    let synced = 0;
    let failed = 0;
    const remaining: QueuedMessage[] = [];

    for (const msg of queue) {
      try {
        const resp = await fetch(`${apiBase}/api/chat/sessions/${msg.session_id}/messages`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
          },
          body: JSON.stringify({
            role: msg.role,
            content: msg.content,
            metadata: { queued_at: msg.timestamp, offline: true },
          }),
        });
        if (resp.ok) {
          synced++;
        } else {
          failed++;
          remaining.push({ ...msg, retries: msg.retries + 1, last_error: `HTTP ${resp.status}` });
        }
      } catch (e: any) {
        failed++;
        remaining.push({ ...msg, retries: msg.retries + 1, last_error: e?.message });
      }
    }

    // Only keep messages with < 5 retries
    const toRetry = remaining.filter(m => m.retries < 5);
    await AsyncStorage.setItem(MESSAGE_QUEUE_KEY, JSON.stringify(toRetry));

    this.syncing = false;
    const status: SyncStatus = failed > 0 ? "error" : "idle";
    await this.setSyncStatus(status);
    return { synced, failed, status };
  }

  /**
   * [PHASE5] Get current sync status.
   */
  async getSyncStatus(): Promise<SyncStatus> {
    const raw = await AsyncStorage.getItem(SYNC_STATUS_KEY);
    return (raw as SyncStatus) || "idle";
  }

  private async setSyncStatus(status: SyncStatus): Promise<void> {
    await AsyncStorage.setItem(SYNC_STATUS_KEY, status);
  }

  /**
   * [PHASE5] Get queue size.
   */
  async queueSize(): Promise<number> {
    const queue = await this.getQueue();
    return queue.length;
  }
}

export const offlineSync = new OfflineSyncManager();

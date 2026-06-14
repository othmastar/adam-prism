/**
 * [PHASE5] Push notifications service for mobile.
 * Sends local notifications when:
 *  - Bottleneck predicted (proactive alert)
 *  - Session has new message from another user
 *  - Scheduled job completed
 */
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

// [PHASE5] Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export class PushNotificationManager {
  private initialized = false;

  /**
   * [PHASE5] Register for push notifications and get permission.
   */
  async initialize(): Promise<string | null> {
    if (this.initialized) return null;

    try {
      // Check / request permission
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      if (existingStatus !== "granted") {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== "granted") {
        console.warn("[PUSH] Permission not granted");
        return null;
      }

      // Get push token (only works on physical devices)
      if (Platform.OS === "android") {
        await Notifications.setNotificationChannelAsync("adam-prism-default", {
          name: "Adam Prism",
          importance: Notifications.AndroidImportance.HIGH,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: "#10b981",
        });
      }

      const tokenData = await Notifications.getExpoPushTokenAsync();
      this.initialized = true;
      console.info("[PUSH] Initialized, token:", tokenData.data.substring(0, 20) + "...");
      return tokenData.data;
    } catch (e) {
      console.error("[PUSH] Init failed:", e);
      return null;
    }
  }

  /**
   * [PHASE5] Schedule a local notification (no push server needed).
   */
  async scheduleLocal(
    title: string,
    body: string,
    data?: Record<string, unknown>,
    triggerSeconds: number = 0,
  ): Promise<string> {
    const id = await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data: data || {},
        sound: true,
      },
      trigger: triggerSeconds > 0
        ? { seconds: triggerSeconds }
        : null,
    });
    return id;
  }

  /**
   * [PHASE5] Send immediate local notification (e.g., for predicted bottleneck).
   */
  async notifyBottleneck(
    serviceName: string,
    probability: number,
  ): Promise<string> {
    return this.scheduleLocal(
      "⚠️ Bottleneck Predicted",
      `${serviceName} showing ${Math.round(probability * 100)}% bottleneck probability. Check root cause now.`,
      { type: "bottleneck", service: serviceName, probability },
    );
  }

  /**
   * [PHASE5] Notify on session update.
   */
  async notifySession(sessionTitle: string, message: string): Promise<string> {
    return this.scheduleLocal(
      `📨 ${sessionTitle}`,
      message,
      { type: "session" },
    );
  }

  /**
   * [PHASE5] Cancel all pending notifications.
   */
  async cancelAll(): Promise<void> {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }
}

export const pushNotifications = new PushNotificationManager();

/**
 * useAdamChat — Hook للـ chat مع كل المميزات
 * =============================================
 * يبسط استخدام api-enhanced في الـ components.
 *
 * المميزات:
 * - إدارة session تلقائياً
 * - file upload مع display
 * - streaming mode
 * - error handling
 * - retry
 * - LTM context auto-recall
 *
 * Usage:
 *   const { sendMessage, isStreaming, error } = useAdamChat();
 *   await sendMessage("مرحبا", [file1, file2]);
 */

import { useState, useCallback, useRef } from "react";
import {
  sendChatMessage,
  streamChatMessage,
  uploadFiles,
  buildMessageWithFile,
  recallLTMContext,
  type ChatContext,
  type UploadResult,
} from "./api-enhanced";

export type UseAdamChatOptions = {
  sessionId?: string;
  enableLTM?: boolean; // auto-recall memories
  enableStreaming?: boolean;
  onMessage?: (role: "user" | "assistant", content: string) => void;
  onError?: (error: string) => void;
};

export type UseAdamChatReturn = {
  sendMessage: (text: string, files?: File[]) => Promise<string>;
  isStreaming: boolean;
  isUploading: boolean;
  error: string | null;
  sessionId: string | null;
  clearError: () => void;
  uploadedFiles: UploadResult[];
};

export function useAdamChat(
  options: UseAdamChatOptions = {},
): UseAdamChatReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(
    options.sessionId || null,
  );
  const [uploadedFiles, setUploadedFiles] = useState<UploadResult[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const sendMessage = useCallback(
    async (text: string, files: File[] = []): Promise<string> => {
      setError(null);

      // 1. ارفع الملفات لو فيه
      let fileContents: { name: string; content: string }[] = [];
      if (files.length > 0) {
        setIsUploading(true);
        try {
          const { successes, failures } = await uploadFiles(files);
          setUploadedFiles(successes);
          fileContents = successes.map((s) => ({
            name: s.filename,
            content: s.text_content,
          }));

          if (failures.length > 0) {
            const errMsg = `فشل رفع ${failures.length} ملف: ${failures
              .map((f) => f.file)
              .join(", ")}`;
            setError(errMsg);
            options.onError?.(errMsg);
          }
        } catch (e) {
          const errMsg = `Upload error: ${e instanceof Error ? e.message : String(e)}`;
          setError(errMsg);
          options.onError?.(errMsg);
          setIsUploading(false);
          return "";
        } finally {
          setIsUploading(false);
        }
      }

      // 2. ابنِ الرسالة مع الملفات
      let message = text;
      for (const file of fileContents) {
        message = buildMessageWithFile(message, file.name, file.content);
      }

      if (!message.trim()) {
        setError("الرسالة فارغة");
        return "";
      }

      // 3. LTM context auto-recall
      let ltmContext: string[] = [];
      if (options.enableLTM) {
        try {
          const recall = await recallLTMContext(message, 5);
          if (recall.context) {
            ltmContext = recall.context
              .split("\n")
              .filter((l: string) => l.trim());
          }
        } catch {
          // silent — LTM optional
        }
      }

      // 4. ابنِ الـ context
      const context: ChatContext = {
        history: [], // يُملأ من الـ caller لو محتاج
        attachments: fileContents.map((f) => ({
          type: "file" as const,
          name: f.name,
          content: f.content,
        })),
        memory: ltmContext,
      };

      // 5. ابعت الرسالة
      setIsStreaming(true);
      abortRef.current = new AbortController();

      try {
        if (options.enableStreaming) {
          // streaming mode
          let fullResponse = "";
          for await (const chunk of streamChatMessage(
            message,
            context,
            sessionId || undefined,
          )) {
            if (chunk.type === "chunk" && chunk.content) {
              fullResponse += chunk.content;
              options.onMessage?.("assistant", chunk.content);
            } else if (chunk.type === "done") {
              const sid = (chunk as any).session_id;
              if (sid) setSessionId(sid);
            }
          }
          options.onMessage?.("user", message);
          return fullResponse;
        } else {
          // REST mode
          const result = await sendChatMessage(
            message,
            context,
            sessionId || undefined,
          );
          if ((result as any).session_id) setSessionId((result as any).session_id);
          options.onMessage?.("user", message);
          options.onMessage?.("assistant", result.response);
          return result.response;
        }
      } catch (e) {
        const errMsg = e instanceof Error ? e.message : String(e);
        setError(errMsg);
        options.onError?.(errMsg);
        return "";
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [sessionId, options.enableLTM, options.enableStreaming, options.onMessage, options.onError],
  );

  return {
    sendMessage,
    isStreaming,
    isUploading,
    error,
    sessionId,
    clearError,
    uploadedFiles,
  };
}

/**
 * [PHASE3] Adam Prism Mobile — Chat store
 */
import { create } from "zustand"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: number
  duration_ms?: number
}

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  error: string | null
  addMessage: (msg: Message) => void
  updateLastMessage: (content: string) => void
  clear: () => void
  setStreaming: (streaming: boolean) => void
  setError: (error: string | null) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  error: null,
  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),
  updateLastMessage: (content) =>
    set((s) => {
      const msgs = [...s.messages]
      if (msgs.length > 0) {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content }
      }
      return { messages: msgs }
    }),
  clear: () => set({ messages: [], error: null }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setError: (error) => set({ error }),
}))

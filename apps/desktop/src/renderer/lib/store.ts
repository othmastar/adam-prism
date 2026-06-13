import { create } from 'zustand'
import type { AppState, Session, Message, Settings, ServerStatus, RightPanelView, BottomPanelView, UpdateStatus, Attachment } from '../types'
import { generateId } from './utils'
import { chatApi } from './api'

function getDefaultSettings(): Settings {
  return {
    backendUrl: 'http://localhost:8000',
    apiKey: '',
    isLocal: true,
    theme: 'dark',
    language: 'ar',
    onboardingComplete: false,
    notificationsEnabled: true,
    model: 'adam',
    windowBounds: { x: 100, y: 100, width: 1400, height: 900 },
    sidebarWidth: 280,
    rightPanelWidth: 360,
    bottomPanelHeight: 220,
    voiceEnabled: true,
    voiceSttLanguage: 'ar',
    voiceTtsLanguage: 'ar'
  }
}

export const useStore = create<AppState>((set, get) => ({
  // Sessions
  sessions: [],
  currentSessionId: null,
  messages: [],

  // UI
  sidebarOpen: true,
  rightPanelView: 'none',
  bottomPanelView: 'none',
  settingsOpen: false,
  commandPaletteOpen: false,
  onboardingVisible: false,

  // Status
  serverStatus: { status: 'offline' },
  isStreaming: false,
  updateStatus: null,

  // Settings
  settings: getDefaultSettings(),

  // Actions
  setSessions: (sessions: Session[]) => set({ sessions }),
  addSession: (session: Session) => set((state) => ({ sessions: [session, ...state.sessions] })),
  removeSession: (id: string) => set((state) => ({
    sessions: state.sessions.filter((s) => s.id !== id),
    currentSessionId: state.currentSessionId === id ? null : state.currentSessionId
  })),

  setCurrentSession: (id: string | null) => set({ currentSessionId: id }),

  setMessages: (messages: Message[]) => set({ messages }),

  addMessage: (message: Message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateMessage: (id: string, updates: Partial<Message>) => set((state) => ({
    messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m))
  })),

  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
  setRightPanelView: (view: RightPanelView) => set({ rightPanelView: view }),
  setBottomPanelView: (view: BottomPanelView) => set({ bottomPanelView: view }),
  setSettingsOpen: (open: boolean) => set({ settingsOpen: open }),
  setCommandPaletteOpen: (open: boolean) => set({ commandPaletteOpen: open }),
  setOnboardingVisible: (visible: boolean) => set({ onboardingVisible: visible }),

  setServerStatus: (status: ServerStatus) => set({ serverStatus: status }),
  setIsStreaming: (streaming: boolean) => set({ isStreaming: streaming }),
  setUpdateStatus: (status: UpdateStatus | null) => set({ updateStatus: status }),

  setSettings: (partial: Partial<Settings>) => set((state) => ({
    settings: { ...state.settings, ...partial }
  })),

  loadSessions: async () => {
    try {
      const response = await chatApi.getSessions()
      if (response.status === 200 && Array.isArray(response.data)) {
        const sessions: Session[] = response.data.map((s: Record<string, unknown>) => ({
          id: s.id as string || s.session_id as string,
          title: s.title as string || s.name as string || 'محادثة جديدة',
          createdAt: new Date(s.created_at as string || Date.now()).getTime(),
          updatedAt: new Date(s.updated_at as string || Date.now()).getTime(),
          messageCount: s.message_count as number || 0,
          lastMessage: s.last_message as string || '',
          model: s.model as string || '',
          pinned: s.pinned as boolean || false
        }))
        set({ sessions })
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  },

  loadMessages: async (sessionId: string) => {
    try {
      const response = await chatApi.getSessionMessages(sessionId)
      if (response.status === 200 && Array.isArray(response.data)) {
        const messages: Message[] = response.data.map((m: Record<string, unknown>) => ({
          id: m.id as string || generateId(),
          role: m.role as 'user' | 'assistant' | 'system',
          content: m.content as string || '',
          timestamp: new Date(m.timestamp as string || m.created_at as string || Date.now()).getTime(),
          tokens: m.tokens as Message['tokens'],
          tools: m.tools as Message['tools'],
          isStreaming: false
        }))
        set({ messages, currentSessionId: sessionId })
      }
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  },

  sendMessage: async (content: string, attachments?: Attachment[]) => {
    const state = get()
    if (state.isStreaming) return

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: Date.now(),
      attachments,
      isStreaming: false
    }

    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true
    }

    set({
      messages: [...state.messages, userMessage, assistantMessage],
      isStreaming: true
    })

    try {
      const { streamChat } = await import('./sse')
      await streamChat({
        message: content,
        sessionId: state.currentSessionId || undefined,
        onToken: (token) => {
          set((s) => ({
            messages: s.messages.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: m.content + token }
                : m
            )
          }))
        },
        onToolCall: (tool) => {
          set((s) => ({
            messages: s.messages.map((m) =>
              m.id === assistantMessage.id
                ? {
                    ...m,
                    tools: [...(m.tools || []), {
                      id: generateId(),
                      name: tool.name,
                      params: tool.params,
                      status: tool.status as 'pending' | 'running' | 'completed' | 'error'
                    }]
                  }
                : m
            )
          }))
        },
        onComplete: (fullResponse) => {
          set((s) => ({
            messages: s.messages.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: fullResponse, isStreaming: false }
                : m
            ),
            isStreaming: false
          }))
          // Refresh sessions
          get().loadSessions()
        },
        onError: (error) => {
          console.error('Chat stream error:', error)
          set((s) => ({
            messages: s.messages.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: `خطأ: ${error.message}`, isStreaming: false }
                : m
            ),
            isStreaming: false
          }))
        }
      })
    } catch (err) {
      console.error('Failed to send message:', err)
      set((s) => ({
        messages: s.messages.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: 'تعذر إرسال الرسالة. يرجى التحقق من اتصال الخادم.', isStreaming: false }
            : m
        ),
        isStreaming: false
      }))
    }
  },

  deleteSession: async (id: string) => {
    try {
      await chatApi.deleteSession(id)
      get().removeSession(id)
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  },

  createNewSession: () => {
    set({
      currentSessionId: null,
      messages: [],
      rightPanelView: 'none',
      bottomPanelView: 'none'
    })
  },

  searchSessions: async (query: string) => {
    try {
      const response = await chatApi.searchSessions(query)
      if (response.status === 200 && Array.isArray(response.data)) {
        return response.data.map((s: Record<string, unknown>) => ({
          id: s.id as string || s.session_id as string,
          title: s.title as string || 'محادثة',
          createdAt: new Date(s.created_at as string || Date.now()).getTime(),
          updatedAt: new Date(s.updated_at as string || Date.now()).getTime(),
          messageCount: s.message_count as number || 0,
          lastMessage: s.last_message as string || ''
        }))
      }
      return []
    } catch {
      return []
    }
  }
}))

// Initialize settings from electron store
export async function initSettings(): Promise<void> {
  try {
    const settings = await window.api.getSettings()
    if (settings) {
      useStore.getState().setSettings(settings as Partial<Settings>)
      if (!settings.onboardingComplete) {
        useStore.getState().setOnboardingVisible(true)
      }
    }
  } catch (err) {
    console.error('Failed to load settings:', err)
  }
}

export function getSettings(): Settings {
  return useStore.getState().settings
}

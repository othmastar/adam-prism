// Session store using localStorage as fallback since better-sqlite3 is main-process only
// This provides client-side caching for sessions

interface StoredSession {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messageCount: number
  lastMessage: string
  model: string
  pinned: boolean
}

interface StoredMessage {
  id: string
  sessionId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  tokens?: { prompt: number; completion: number; total: number }
}

const SESSIONS_KEY = 'adam-prism-sessions'
const MESSAGES_KEY_PREFIX = 'adam-prism-messages-'

export const sessionStore = {
  getSessions(): StoredSession[] {
    try {
      const data = localStorage.getItem(SESSIONS_KEY)
      return data ? JSON.parse(data) : []
    } catch {
      return []
    }
  },

  saveSessions(sessions: StoredSession[]): void {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions))
  },

  addSession(session: StoredSession): void {
    const sessions = this.getSessions()
    sessions.unshift(session)
    this.saveSessions(sessions)
  },

  updateSession(id: string, updates: Partial<StoredSession>): void {
    const sessions = this.getSessions()
    const index = sessions.findIndex((s) => s.id === id)
    if (index !== -1) {
      sessions[index] = { ...sessions[index], ...updates }
      this.saveSessions(sessions)
    }
  },

  deleteSession(id: string): void {
    const sessions = this.getSessions().filter((s) => s.id !== id)
    this.saveSessions(sessions)
    localStorage.removeItem(MESSAGES_KEY_PREFIX + id)
  },

  getMessages(sessionId: string): StoredMessage[] {
    try {
      const data = localStorage.getItem(MESSAGES_KEY_PREFIX + sessionId)
      return data ? JSON.parse(data) : []
    } catch {
      return []
    }
  },

  saveMessages(sessionId: string, messages: StoredMessage[]): void {
    localStorage.setItem(MESSAGES_KEY_PREFIX + sessionId, JSON.stringify(messages))
  },

  addMessage(sessionId: string, message: StoredMessage): void {
    const messages = this.getMessages(sessionId)
    messages.push(message)
    this.saveMessages(sessionId, messages)
  },

  searchSessions(query: string): StoredSession[] {
    const sessions = this.getSessions()
    const lowerQuery = query.toLowerCase()
    return sessions.filter(
      (s) =>
        s.title.toLowerCase().includes(lowerQuery) ||
        s.lastMessage.toLowerCase().includes(lowerQuery)
    )
  },

  clearAll(): void {
    const sessions = this.getSessions()
    sessions.forEach((s) => localStorage.removeItem(MESSAGES_KEY_PREFIX + s.id))
    localStorage.removeItem(SESSIONS_KEY)
  }
}

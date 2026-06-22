import { useCallback } from 'react'
import { useStore } from '../lib/store'
import { chatApi } from '../lib/api'
import { generateId } from '../lib/utils'
import type { Session, Message } from '../types'

export function useSession() {
  const store = useStore()

  const createSession = useCallback((title?: string): Session => {
    const session: Session = {
      id: generateId(),
      title: title || 'محادثة جديدة',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messageCount: 0,
      pinned: false
    }
    store.addSession(session)
    store.setCurrentSession(session.id)
    store.setMessages([])
    return session
  }, [store])

  const switchSession = useCallback(async (sessionId: string) => {
    store.setCurrentSession(sessionId)
    await store.loadMessages(sessionId)
  }, [store])

  const deleteSession = useCallback(async (sessionId: string) => {
    await store.deleteSession(sessionId)
  }, [store])

  const renameSession = useCallback((sessionId: string, title: string) => {
    const sessions = store.sessions.map((s) =>
      s.id === sessionId ? { ...s, title, updatedAt: Date.now() } : s
    )
    store.setSessions(sessions)
  }, [store])

  const pinSession = useCallback((sessionId: string) => {
    const sessions = store.sessions.map((s) =>
      s.id === sessionId ? { ...s, pinned: !s.pinned } : s
    )
    store.setSessions(sessions)
  }, [store])

  return {
    sessions: store.sessions,
    currentSessionId: store.currentSessionId,
    messages: store.messages,
    createSession,
    switchSession,
    deleteSession,
    renameSession,
    pinSession,
    loadSessions: store.loadSessions,
    sendMessage: store.sendMessage,
    createNewSession: store.createNewSession
  }
}

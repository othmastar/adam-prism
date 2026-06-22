import React, { useState, useEffect } from 'react'
import { Users, Plus, MessageSquare, Loader2, Play, CircleDot } from 'lucide-react'
import { subagentsApi } from '../../lib/api'
import type { Subagent } from '../../types'
import { cn, generateId } from '../../lib/utils'

export function SubagentsPanel() {
  const [subagents, setSubagents] = useState<Subagent[]>([])
  const [loading, setLoading] = useState(false)
  const [showSpawnForm, setShowSpawnForm] = useState(false)
  const [spawnName, setSpawnName] = useState('')
  const [spawnType, setSpawnType] = useState('general')
  const [chatTarget, setChatTarget] = useState<string | null>(null)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Record<string, Array<{ role: string; content: string }>>>({})

  useEffect(() => {
    loadSubagents()
  }, [])

  const loadSubagents = async () => {
    setLoading(true)
    try {
      const response = await subagentsApi.list()
      if (response.status === 200 && Array.isArray(response.data)) {
        setSubagents(response.data as Subagent[])
      }
    } catch (err) {
      console.error('Failed to load subagents:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSpawn = async () => {
    if (!spawnName.trim()) return
    try {
      await subagentsApi.spawn(spawnName, spawnType)
      setSpawnName('')
      setShowSpawnForm(false)
      loadSubagents()
    } catch (err) {
      console.error('Failed to spawn subagent:', err)
    }
  }

  const handleChat = async (id: string) => {
    if (!chatMessage.trim()) return
    try {
      const msg = chatMessage
      setChatMessage('')
      setChatHistory((prev) => ({
        ...prev,
        [id]: [...(prev[id] || []), { role: 'user', content: msg }]
      }))

      const response = await subagentsApi.chat(id, msg)
      if (response.status === 200) {
        const data = response.data as Record<string, unknown>
        setChatHistory((prev) => ({
          ...prev,
          [id]: [...(prev[id] || []), { role: 'assistant', content: String(data.response || data.message || '') }]
        }))
      }
    } catch (err) {
      console.error('Chat with subagent failed:', err)
    }
  }

  const statusColors = {
    idle: 'text-dark-400',
    running: 'text-warning',
    completed: 'text-accent',
    error: 'text-danger'
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={20} className="animate-spin text-dark-400" />
          </div>
        ) : subagents.length === 0 && !chatTarget ? (
          <div className="text-center py-12">
            <Users size={32} className="mx-auto text-dark-600 mb-3" />
            <p className="text-sm text-dark-400">لا يوجد وكلاء فرعيين</p>
            <button
              onClick={() => setShowSpawnForm(true)}
              className="mt-3 px-4 py-1.5 text-xs bg-accent/10 text-accent rounded-lg hover:bg-accent/20 transition-colors"
            >
              إنشاء وكيل
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {subagents.map((agent) => (
              <div key={agent.id} className="bg-dark-700 rounded-lg border border-dark-600 overflow-hidden">
                <div className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CircleDot size={12} className={statusColors[agent.status]} />
                      <span className="text-xs font-medium text-dark-100">{agent.name}</span>
                      <span className="text-[9px] bg-dark-600 text-dark-400 px-1.5 py-0.5 rounded">{agent.type}</span>
                    </div>
                    <button
                      onClick={() => setChatTarget(chatTarget === agent.id ? null : agent.id)}
                      className="p-1 rounded text-dark-400 hover:text-accent hover:bg-dark-600 transition-colors"
                    >
                      <MessageSquare size={12} />
                    </button>
                  </div>
                  <div className="text-[10px] text-dark-500 mt-1">
                    {agent.status === 'running' ? 'قيد التشغيل' : agent.status === 'idle' ? 'في الانتظار' : agent.status === 'completed' ? 'مكتمل' : 'خطأ'}
                    {' • '}
                    {new Date(agent.createdAt).toLocaleTimeString('ar-SA')}
                  </div>
                </div>

                {/* Chat area */}
                {chatTarget === agent.id && (
                  <div className="border-t border-dark-600 p-2">
                    <div className="max-h-32 overflow-y-auto mb-2">
                      {(chatHistory[agent.id] || []).map((msg, i) => (
                        <div key={i} className={cn('text-[10px] mb-1', msg.role === 'user' ? 'text-dark-300' : 'text-accent')}>
                          <span className="font-medium">{msg.role === 'user' ? 'أنت: ' : 'الوكيل: '}</span>
                          {msg.content}
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-1">
                      <input
                        type="text"
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleChat(agent.id)}
                        placeholder="رسالة للوكيل..."
                        className="flex-1 bg-dark-600 text-[10px] text-dark-100 px-2 py-1 rounded focus:outline-none focus:ring-1 focus:ring-accent"
                      />
                      <button
                        onClick={() => handleChat(agent.id)}
                        className="p-1 rounded bg-accent/10 text-accent hover:bg-accent/20"
                      >
                        <Play size={10} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Spawn form */}
      {showSpawnForm && (
        <div className="border-t border-dark-600 p-3">
          <input
            type="text"
            value={spawnName}
            onChange={(e) => setSpawnName(e.target.value)}
            placeholder="اسم الوكيل"
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent mb-2"
          />
          <select
            value={spawnType}
            onChange={(e) => setSpawnType(e.target.value)}
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 focus:outline-none focus:border-accent mb-2"
          >
            <option value="general">عام</option>
            <option value="code">برمجة</option>
            <option value="research">بحث</option>
            <option value="writing">كتابة</option>
          </select>
          <div className="flex gap-2">
            <button onClick={handleSpawn} className="px-3 py-1.5 text-xs bg-accent text-white rounded-lg hover:bg-accent-hover">إنشاء</button>
            <button onClick={() => setShowSpawnForm(false)} className="px-3 py-1.5 text-xs bg-dark-600 text-dark-200 rounded-lg hover:bg-dark-500">إلغاء</button>
          </div>
        </div>
      )}

      {!showSpawnForm && subagents.length > 0 && (
        <div className="border-t border-dark-600 p-2">
          <button
            onClick={() => setShowSpawnForm(true)}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs text-accent bg-accent/10 rounded-lg hover:bg-accent/20 transition-colors"
          >
            <Plus size={14} />
            إنشاء وكيل
          </button>
        </div>
      )}
    </div>
  )
}

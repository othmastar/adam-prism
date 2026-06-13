import React, { useState, useEffect } from 'react'
import { Plug, Plus, Wrench, Loader2, Server } from 'lucide-react'
import { mcpApi } from '../../lib/api'
import type { MCPTool, MCPServer } from '../../types'
import { cn } from '../../lib/utils'

export function MCPPanel() {
  const [tools, setTools] = useState<MCPTool[]>([])
  const [loading, setLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [serverName, setServerName] = useState('')
  const [serverCommand, setServerCommand] = useState('')
  const [serverArgs, setServerArgs] = useState('')
  const [activeTab, setActiveTab] = useState<'tools' | 'servers'>('tools')

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    setLoading(true)
    try {
      const response = await mcpApi.getTools()
      if (response.status === 200 && Array.isArray(response.data)) {
        setTools(response.data as MCPTool[])
      }
    } catch (err) {
      console.error('Failed to load MCP tools:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddServer = async () => {
    if (!serverName.trim() || !serverCommand.trim()) return
    try {
      const args = serverArgs.split(' ').filter(Boolean)
      await mcpApi.addServer(serverName, serverCommand, args)
      setServerName('')
      setServerCommand('')
      setServerArgs('')
      setShowAddForm(false)
      loadTools()
    } catch (err) {
      console.error('Failed to add MCP server:', err)
    }
  }

  // Group tools by server
  const toolsByServer = tools.reduce<Record<string, MCPTool[]>>((acc, tool) => {
    const server = tool.server || 'default'
    if (!acc[server]) acc[server] = []
    acc[server].push(tool)
    return acc
  }, {})

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-dark-600">
        <button
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-colors',
            activeTab === 'tools' ? 'text-accent border-b-2 border-accent' : 'text-dark-400 hover:text-dark-200'
          )}
          onClick={() => setActiveTab('tools')}
        >
          الأدوات
        </button>
        <button
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-colors',
            activeTab === 'servers' ? 'text-accent border-b-2 border-accent' : 'text-dark-400 hover:text-dark-200'
          )}
          onClick={() => setActiveTab('servers')}
        >
          الخوادم
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={20} className="animate-spin text-dark-400" />
          </div>
        ) : activeTab === 'tools' ? (
          Object.keys(toolsByServer).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(toolsByServer).map(([server, serverTools]) => (
                <div key={server}>
                  <div className="flex items-center gap-2 mb-2">
                    <Server size={12} className="text-accent" />
                    <span className="text-xs font-medium text-dark-200">{server}</span>
                    <span className="text-[9px] bg-dark-600 text-dark-400 px-1.5 py-0.5 rounded">
                      {serverTools.length} أداة
                    </span>
                  </div>
                  <div className="space-y-1.5 mr-4">
                    {serverTools.map((tool, i) => (
                      <div key={tool.name || i} className="bg-dark-700 rounded-lg p-2.5 border border-dark-600">
                        <div className="flex items-center gap-2">
                          <Wrench size={10} className="text-dark-400" />
                          <span className="text-xs text-dark-200">{tool.name}</span>
                        </div>
                        {tool.description && (
                          <p className="text-[10px] text-dark-500 mt-1">{tool.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Plug size={32} className="mx-auto text-dark-600 mb-3" />
              <p className="text-sm text-dark-400">لا توجد أدوات MCP</p>
              <p className="text-[10px] text-dark-500 mt-1">أضف خادم MCP للبدء</p>
            </div>
          )
        ) : (
          <div className="text-center py-8">
            <Server size={24} className="mx-auto text-dark-600 mb-2" />
            <p className="text-xs text-dark-400">إدارة خوادم MCP</p>
          </div>
        )}
      </div>

      {/* Add server form */}
      {showAddForm && (
        <div className="border-t border-dark-600 p-3">
          <input
            type="text"
            value={serverName}
            onChange={(e) => setServerName(e.target.value)}
            placeholder="اسم الخادم"
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent mb-2"
          />
          <input
            type="text"
            value={serverCommand}
            onChange={(e) => setServerCommand(e.target.value)}
            placeholder="الأمر (مثل: npx, python)"
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent mb-2"
          />
          <input
            type="text"
            value={serverArgs}
            onChange={(e) => setServerArgs(e.target.value)}
            placeholder="المعلمات (مفصولة بمسافات)"
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent mb-2"
          />
          <div className="flex gap-2">
            <button onClick={handleAddServer} className="px-3 py-1.5 text-xs bg-accent text-white rounded-lg hover:bg-accent-hover">إضافة</button>
            <button onClick={() => setShowAddForm(false)} className="px-3 py-1.5 text-xs bg-dark-600 text-dark-200 rounded-lg hover:bg-dark-500">إلغاء</button>
          </div>
        </div>
      )}

      {!showAddForm && (
        <div className="border-t border-dark-600 p-2">
          <button
            onClick={() => setShowAddForm(true)}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs text-accent bg-accent/10 rounded-lg hover:bg-accent/20 transition-colors"
          >
            <Plus size={14} />
            إضافة خادم MCP
          </button>
        </div>
      )}
    </div>
  )
}

import React, { useState, useEffect } from 'react'
import { Wrench, Play, Shield, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { toolsApi, skillsApi } from '../../lib/api'
import type { ToolInfo, SkillInfo } from '../../types'
import { cn } from '../../lib/utils'

export function ToolsPanel() {
  const [tools, setTools] = useState<ToolInfo[]>([])
  const [skills, setSkills] = useState<SkillInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'tools' | 'skills'>('tools')
  const [executingTool, setExecutingTool] = useState<string | null>(null)
  const [toolResult, setToolResult] = useState<Record<string, string>>({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [toolsRes, skillsRes] = await Promise.all([
        toolsApi.getAvailable(),
        skillsApi.getAll()
      ])
      if (toolsRes.status === 200 && Array.isArray(toolsRes.data)) {
        setTools(toolsRes.data as ToolInfo[])
      }
      if (skillsRes.status === 200 && Array.isArray(skillsRes.data)) {
        setSkills(skillsRes.data as SkillInfo[])
      }
    } catch (err) {
      console.error('Failed to load tools/skills:', err)
    } finally {
      setLoading(false)
    }
  }

  const executeTool = async (toolName: string) => {
    setExecutingTool(toolName)
    setToolResult({})
    try {
      const response = await toolsApi.execute(toolName, {})
      setToolResult({ [toolName]: JSON.stringify(response.data, null, 2) })
    } catch (err) {
      setToolResult({ [toolName]: `خطأ: ${(err as Error).message}` })
    } finally {
      setExecutingTool(null)
    }
  }

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
            activeTab === 'skills' ? 'text-accent border-b-2 border-accent' : 'text-dark-400 hover:text-dark-200'
          )}
          onClick={() => setActiveTab('skills')}
        >
          المهارات
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="flex items-center justify-center py-12 text-dark-400">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : activeTab === 'tools' ? (
          tools.length > 0 ? (
            <div className="space-y-2">
              {tools.map((tool, i) => (
                <div key={tool.name || i} className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Wrench size={12} className="text-accent" />
                        <span className="text-xs font-medium text-dark-100 truncate">{tool.name}</span>
                        {tool.requiresPermission && (
                          <Shield size={10} className="text-warning" title="يتطلب إذن" />
                        )}
                      </div>
                      <p className="text-[10px] text-dark-400 mt-1 leading-relaxed">{tool.description}</p>
                    </div>
                    <button
                      onClick={() => executeTool(tool.name)}
                      disabled={executingTool === tool.name}
                      className={cn(
                        'p-1.5 rounded-lg transition-colors flex-shrink-0',
                        executingTool === tool.name
                          ? 'bg-dark-600 text-dark-400'
                          : 'bg-accent/10 text-accent hover:bg-accent/20'
                      )}
                    >
                      {executingTool === tool.name ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <Play size={12} />
                      )}
                    </button>
                  </div>
                  {toolResult[tool.name] && (
                    <pre className="mt-2 text-[10px] text-dark-300 bg-dark-800 rounded p-2 overflow-x-auto max-h-32">
                      {toolResult[tool.name]}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Wrench size={32} className="mx-auto text-dark-600 mb-3" />
              <p className="text-sm text-dark-400">لا توجد أدوات متاحة</p>
            </div>
          )
        ) : skills.length > 0 ? (
          <div className="space-y-2">
            {skills.map((skill, i) => (
              <div key={skill.id || i} className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-dark-100">{skill.name}</span>
                  <span className="text-[9px] bg-dark-600 text-dark-400 px-1.5 py-0.5 rounded">{skill.category}</span>
                </div>
                <p className="text-[10px] text-dark-400 mt-1">{skill.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-sm text-dark-400">لا توجد مهارات متاحة</p>
          </div>
        )}
      </div>
    </div>
  )
}

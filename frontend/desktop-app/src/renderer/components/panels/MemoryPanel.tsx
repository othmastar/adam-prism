import React, { useState, useEffect, useCallback } from 'react'
import { Search, Plus, Brain, Database, Loader2, Tag } from 'lucide-react'
import { memoryApi } from '../../lib/api'
import type { MemoryStats, MemorySearchResult } from '../../types'
import { cn } from '../../lib/utils'

export function MemoryPanel() {
  const [stats, setStats] = useState<MemoryStats | null>(null)
  const [searchResults, setSearchResults] = useState<MemorySearchResult[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [showStoreForm, setShowStoreForm] = useState(false)
  const [storeContent, setStoreContent] = useState('')
  const [storeCategory, setStoreCategory] = useState('')
  const [activeTab, setActiveTab] = useState<'stats' | 'search'>('stats')

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    try {
      const response = await memoryApi.getStats()
      if (response.status === 200) {
        setStats(response.data as MemoryStats)
      }
    } catch (err) {
      console.error('Failed to load memory stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return
    setLoading(true)
    try {
      const response = await memoryApi.search(searchQuery)
      if (response.status === 200) {
        setSearchResults(Array.isArray(response.data) ? response.data as MemorySearchResult[] : [])
      }
    } catch (err) {
      console.error('Memory search failed:', err)
    } finally {
      setLoading(false)
    }
  }, [searchQuery])

  const handleStore = async () => {
    if (!storeContent.trim()) return
    try {
      await memoryApi.store(storeContent, storeCategory || undefined)
      setStoreContent('')
      setStoreCategory('')
      setShowStoreForm(false)
      loadStats()
    } catch (err) {
      console.error('Failed to store memory:', err)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-dark-600">
        <button
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-colors',
            activeTab === 'stats' ? 'text-accent border-b-2 border-accent' : 'text-dark-400 hover:text-dark-200'
          )}
          onClick={() => setActiveTab('stats')}
        >
          الإحصائيات
        </button>
        <button
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-colors',
            activeTab === 'search' ? 'text-accent border-b-2 border-accent' : 'text-dark-400 hover:text-dark-200'
          )}
          onClick={() => setActiveTab('search')}
        >
          البحث
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === 'stats' && (
          <>
            {loading && !stats ? (
              <div className="flex items-center justify-center py-12 text-dark-400">
                <Loader2 size={20} className="animate-spin" />
              </div>
            ) : stats ? (
              <div className="space-y-3">
                {/* Total memories */}
                <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                      <Brain size={18} className="text-accent" />
                    </div>
                    <div>
                      <div className="text-xl font-bold text-dark-100">{stats.totalMemories}</div>
                      <div className="text-[10px] text-dark-400">إجمالي الذكريات</div>
                    </div>
                  </div>
                </div>

                {/* Categories */}
                {stats.categories && Object.keys(stats.categories).length > 0 && (
                  <div className="bg-dark-700 rounded-lg p-4 border border-dark-600">
                    <div className="flex items-center gap-2 mb-3">
                      <Tag size={14} className="text-dark-400" />
                      <span className="text-xs font-medium text-dark-200">التصنيفات</span>
                    </div>
                    <div className="space-y-2">
                      {Object.entries(stats.categories).map(([category, count]) => (
                        <div key={category} className="flex items-center justify-between">
                          <span className="text-xs text-dark-300">{category}</span>
                          <span className="text-xs text-dark-500 bg-dark-600 px-2 py-0.5 rounded">{count as number}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Last updated */}
                <div className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                  <div className="flex items-center gap-2">
                    <Database size={12} className="text-dark-400" />
                    <span className="text-[10px] text-dark-400">آخر تحديث: {stats.lastUpdated || 'غير متوفر'}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Brain size={32} className="mx-auto text-dark-600 mb-3" />
                <p className="text-sm text-dark-400">لا يمكن تحميل إحصائيات الذاكرة</p>
              </div>
            )}
          </>
        )}

        {activeTab === 'search' && (
          <>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="ابحث في الذاكرة..."
                className="flex-1 bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent"
              />
              <button
                onClick={handleSearch}
                className="px-3 py-1.5 bg-accent/10 text-accent rounded-lg hover:bg-accent/20 transition-colors"
              >
                <Search size={14} />
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={16} className="animate-spin text-dark-400" />
              </div>
            ) : searchResults.length > 0 ? (
              <div className="space-y-2">
                {searchResults.map((result, i) => (
                  <div key={result.id || i} className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                    <p className="text-xs text-dark-200 leading-relaxed">{result.content}</p>
                    <div className="flex items-center gap-2 mt-2 text-[10px] text-dark-500">
                      <span className="bg-dark-600 px-1.5 py-0.5 rounded">{result.category}</span>
                      <span>•</span>
                      <span>{result.timestamp}</span>
                      <span>•</span>
                      <span>التطابق: {(result.relevance * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : searchQuery ? (
              <div className="text-center py-8 text-xs text-dark-400">لا توجد نتائج</div>
            ) : null}
          </>
        )}
      </div>

      {/* Store form */}
      {showStoreForm && (
        <div className="border-t border-dark-600 p-3">
          <input
            type="text"
            value={storeCategory}
            onChange={(e) => setStoreCategory(e.target.value)}
            placeholder="التصنيف (اختياري)"
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent mb-2"
          />
          <textarea
            value={storeContent}
            onChange={(e) => setStoreContent(e.target.value)}
            placeholder="المحتوى..."
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent resize-none h-20"
          />
          <div className="flex gap-2 mt-2">
            <button onClick={handleStore} className="px-3 py-1.5 text-xs bg-accent text-white rounded-lg hover:bg-accent-hover">حفظ</button>
            <button onClick={() => setShowStoreForm(false)} className="px-3 py-1.5 text-xs bg-dark-600 text-dark-200 rounded-lg hover:bg-dark-500">إلغاء</button>
          </div>
        </div>
      )}

      {!showStoreForm && (
        <div className="border-t border-dark-600 p-2">
          <button
            onClick={() => setShowStoreForm(true)}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs text-accent bg-accent/10 rounded-lg hover:bg-accent/20 transition-colors"
          >
            <Plus size={14} />
            حفظ ذكرى
          </button>
        </div>
      )}
    </div>
  )
}

import React, { useState, useEffect, useCallback } from 'react'
import { Search, Plus, BookOpen, FileText, FolderOpen, Loader2 } from 'lucide-react'
import { knowledgeApi } from '../../lib/api'
import type { KnowledgeCollection, KnowledgeSearchResult } from '../../types'
import { cn } from '../../lib/utils'

export function KnowledgePanel() {
  const [collections, setCollections] = useState<KnowledgeCollection[]>([])
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [addContent, setAddContent] = useState('')
  const [addCollection, setAddCollection] = useState('')
  const [activeTab, setActiveTab] = useState<'collections' | 'search'>('collections')

  useEffect(() => {
    loadCollections()
  }, [])

  const loadCollections = async () => {
    setLoading(true)
    try {
      const response = await knowledgeApi.getCollections()
      if (response.status === 200 && Array.isArray(response.data)) {
        setCollections(response.data as KnowledgeCollection[])
      }
    } catch (err) {
      console.error('Failed to load collections:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return
    setLoading(true)
    try {
      const response = await knowledgeApi.search(searchQuery)
      if (response.status === 200) {
        setSearchResults(Array.isArray(response.data) ? response.data as KnowledgeSearchResult[] : [])
      }
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setLoading(false)
    }
  }, [searchQuery])

  const handleAdd = async () => {
    if (!addContent.trim()) return
    try {
      await knowledgeApi.add(addContent, addCollection || undefined)
      setAddContent('')
      setAddCollection('')
      setShowAddForm(false)
      loadCollections()
    } catch (err) {
      console.error('Failed to add knowledge:', err)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-dark-600">
        <button
          className={cn(
            'flex-1 px-3 py-2 text-xs font-medium transition-colors',
            activeTab === 'collections' ? 'text-accent border-b-2 border-accent' : 'text-dark-400 hover:text-dark-200'
          )}
          onClick={() => setActiveTab('collections')}
        >
          المجموعات
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
        {activeTab === 'collections' && (
          <>
            {loading && collections.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-dark-400">
                <Loader2 size={20} className="animate-spin" />
              </div>
            ) : collections.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen size={32} className="mx-auto text-dark-600 mb-3" />
                <p className="text-sm text-dark-400">لا توجد مجموعات معرفة بعد</p>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="mt-3 px-4 py-1.5 text-xs bg-accent/10 text-accent rounded-lg hover:bg-accent/20 transition-colors"
                >
                  إضافة معرفة
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {collections.map((collection, i) => (
                  <div key={collection.id || i} className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                    <div className="flex items-center gap-2">
                      <FolderOpen size={14} className="text-accent" />
                      <span className="text-xs font-medium text-dark-100">{collection.name}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-[10px] text-dark-400">
                      <span>{collection.documentCount} مستند</span>
                      <span>{collection.createdAt}</span>
                    </div>
                  </div>
                ))}
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
                placeholder="ابحث في المعرفة..."
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
                  <div key={i} className="bg-dark-700 rounded-lg p-3 border border-dark-600">
                    <p className="text-xs text-dark-200 leading-relaxed">{result.content}</p>
                    <div className="flex items-center gap-2 mt-2 text-[10px] text-dark-500">
                      <span>المصدر: {result.source}</span>
                      <span>•</span>
                      <span>التطابق: {(result.score * 100).toFixed(0)}%</span>
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

      {/* Add form */}
      {showAddForm && (
        <div className="border-t border-dark-600 p-3">
          <input
            type="text"
            value={addCollection}
            onChange={(e) => setAddCollection(e.target.value)}
            placeholder="اسم المجموعة (اختياري)"
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent mb-2"
          />
          <textarea
            value={addContent}
            onChange={(e) => setAddContent(e.target.value)}
            placeholder="المحتوى..."
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-xs text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent resize-none h-20"
          />
          <div className="flex gap-2 mt-2">
            <button onClick={handleAdd} className="px-3 py-1.5 text-xs bg-accent text-white rounded-lg hover:bg-accent-hover">
              إضافة
            </button>
            <button onClick={() => setShowAddForm(false)} className="px-3 py-1.5 text-xs bg-dark-600 text-dark-200 rounded-lg hover:bg-dark-500">
              إلغاء
            </button>
          </div>
        </div>
      )}

      {/* Add button */}
      {!showAddForm && (
        <div className="border-t border-dark-600 p-2">
          <button
            onClick={() => setShowAddForm(true)}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs text-accent bg-accent/10 rounded-lg hover:bg-accent/20 transition-colors"
          >
            <Plus size={14} />
            إضافة معرفة
          </button>
        </div>
      )}
    </div>
  )
}

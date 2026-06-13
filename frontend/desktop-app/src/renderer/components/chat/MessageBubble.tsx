import React, { useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, User, Bot, Volume2 } from 'lucide-react'
import type { Message } from '../../types'
import { ToolIndicator } from './ToolIndicator'
import { StreamingMessage } from './StreamingMessage'
import { cn, formatTime, getDirection } from '../../lib/utils'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copiedBlock, setCopiedBlock] = useState<string | null>(null)
  const isUser = message.role === 'user'
  const isRTL = getDirection(message.content) === 'rtl'

  const handleCopyBlock = (code: string, id: string) => {
    navigator.clipboard.writeText(code)
    setCopiedBlock(id)
    setTimeout(() => setCopiedBlock(null), 2000)
  }

  const handleCopyMessage = () => {
    navigator.clipboard.writeText(message.content)
  }

  return (
    <div
      className={cn(
        'flex gap-3 px-4 py-3 group animate-fadeIn',
        isUser ? 'flex-row-reverse' : ''
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5',
          isUser
            ? 'bg-accent/20 text-accent'
            : 'bg-gradient-to-br from-accent to-emerald-400 text-white'
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Message content */}
      <div className={cn('flex-1 min-w-0', isUser ? 'text-left' : '')}>
        {/* Header */}
        <div className={cn('flex items-center gap-2 mb-1', isUser && 'flex-row-reverse')}>
          <span className="text-xs font-medium text-dark-300">
            {isUser ? 'أنت' : 'آدم'}
          </span>
          <span className="text-[10px] text-dark-500">{formatTime(message.timestamp)}</span>
          {message.tokens && (
            <span className="text-[9px] text-dark-500">
              {message.tokens.total} رمز
            </span>
          )}
        </div>

        {/* Content */}
        <div
          className={cn(
            'rounded-xl px-4 py-3 max-w-[85%]',
            isUser
              ? 'bg-accent/10 border border-accent/20 mr-auto'
              : 'bg-dark-700 border border-dark-600',
            isRTL && !isUser && 'text-right'
          )}
          dir={isRTL ? 'rtl' : 'ltr'}
        >
          {message.isStreaming && !message.content ? (
            <div className="flex items-center gap-2 text-dark-400">
              <Loader2 className="animate-spin" size={14} />
              <span className="text-sm">جاري التفكير...</span>
            </div>
          ) : message.isStreaming ? (
            <div className="markdown-content text-sm text-dark-100">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {message.content}
              </ReactMarkdown>
              <StreamingMessage content="" />
            </div>
          ) : (
            <div className="markdown-content text-sm text-dark-100">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={getMarkdownComponents(copiedBlock, handleCopyBlock)}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Tool calls */}
        {message.tools && message.tools.length > 0 && (
          <div className="mt-2 max-w-[85%]">
            {message.tools.map((tool) => (
              <ToolIndicator key={tool.id} tool={tool} />
            ))}
          </div>
        )}

        {/* Actions */}
        {!message.isStreaming && !isUser && (
          <div className="flex items-center gap-1 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopyMessage}
              className="p-1 rounded text-dark-500 hover:text-dark-200 hover:bg-dark-700 transition-colors"
              title="نسخ"
            >
              <Copy size={12} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function getMarkdownComponents(copiedBlock: string | null, handleCopyBlock: (code: string, id: string) => void) {
  return {
    code({ className, children, ...props }: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) {
      const match = /language-(\w+)/.exec(className || '')
      const codeString = String(children).replace(/\n$/, '')
      const blockId = codeString.slice(0, 20)

      if (!match) {
        return (
          <code className="bg-dark-600 px-1.5 py-0.5 rounded text-accent text-[13px]" {...props}>
            {children}
          </code>
        )
      }

      return (
        <div className="relative my-3 rounded-lg overflow-hidden border border-dark-500">
          <div className="flex items-center justify-between px-4 py-1.5 bg-dark-800 border-b border-dark-500">
            <span className="text-[10px] text-dark-400">{match[1]}</span>
            <button
              onClick={() => handleCopyBlock(codeString, blockId)}
              className="flex items-center gap-1 text-[10px] text-dark-400 hover:text-dark-200 transition-colors"
            >
              {copiedBlock === blockId ? (
                <>
                  <Check size={10} />
                  تم النسخ
                </>
              ) : (
                <>
                  <Copy size={10} />
                  نسخ
                </>
              )}
            </button>
          </div>
          <SyntaxHighlighter
            style={oneDark}
            language={match[1]}
            PreTag="div"
            customStyle={{
              margin: 0,
              padding: '12px 16px',
              background: '#12121a',
              fontSize: '13px',
              lineHeight: '1.5'
            }}
          >
            {codeString}
          </SyntaxHighlighter>
        </div>
      )
    },
    a({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) {
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline" {...props}>
          {children}
        </a>
      )
    }
  }
}

const markdownComponents = getMarkdownComponents(null, () => {})

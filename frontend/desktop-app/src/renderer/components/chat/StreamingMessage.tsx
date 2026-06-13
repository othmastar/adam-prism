import React from 'react'
import { Loader2 } from 'lucide-react'

interface StreamingMessageProps {
  content: string
}

export function StreamingMessage({ content }: StreamingMessageProps) {
  return (
    <div className="flex items-start gap-1">
      <span>{content}</span>
      <span className="inline-block w-1.5 h-4 bg-accent rounded-sm animate-pulse mt-1" />
    </div>
  )
}

import React from 'react'
import { cn } from '../../lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: React.ReactNode
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label className="text-sm font-medium text-dark-200">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              'w-full bg-dark-700 border border-dark-500 rounded-lg px-4 py-2.5 text-sm text-dark-100',
              'placeholder:text-dark-400 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50',
              'transition-all duration-150',
              icon && 'pr-10',
              error && 'border-danger focus:border-danger focus:ring-danger/50',
              className
            )}
            {...props}
          />
        </div>
        {error && (
          <p className="text-xs text-danger">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label className="text-sm font-medium text-dark-200">{label}</label>
        )}
        <textarea
          ref={ref}
          className={cn(
            'w-full bg-dark-700 border border-dark-500 rounded-lg px-4 py-2.5 text-sm text-dark-100',
            'placeholder:text-dark-400 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50',
            'transition-all duration-150 resize-none',
            error && 'border-danger',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    )
  }
)

TextArea.displayName = 'TextArea'

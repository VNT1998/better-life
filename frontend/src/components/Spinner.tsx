import type { HTMLAttributes } from 'react'

interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg'
}

export function Spinner({ size = 'md', className = '', ...props }: SpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
  }

  return (
    <div
      role="status"
      aria-label="Loading"
      className={`inline-block animate-spin rounded-full border-solid border-sky-500 border-t-transparent ${sizeClasses[size]} ${className}`}
      {...props}
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}

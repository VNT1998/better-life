import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  disabled,
  children,
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: 'bg-sky-500 hover:bg-sky-600 active:bg-sky-700 text-white shadow-md shadow-sky-500/20',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-700',
    outline: 'border border-slate-200 hover:border-slate-300 text-slate-700 bg-white',
    danger: 'bg-rose-500 hover:bg-rose-600 text-white shadow-md shadow-rose-500/20',
  }

  const sizeClasses = {
    sm: 'py-1.5 px-3 text-xs',
    md: 'py-2 px-4 text-sm',
    lg: 'py-2.5 px-5 text-base',
  }

  return (
    <button
      disabled={disabled}
      className={`inline-flex items-center justify-center font-medium rounded-xl transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

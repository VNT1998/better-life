import React, { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Uncaught error in component tree:', error, errorInfo)
  }

  handleReload = (): void => {
    window.location.reload()
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-8 text-center space-y-4">
            <div className="w-14 h-14 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center mx-auto">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">Something went wrong</h2>
            <p className="text-sm text-slate-500 leading-relaxed">
              An unexpected application error occurred. We have logged this event for investigation.
            </p>
            {this.state.error && (
              <pre className="text-xs font-mono bg-slate-100 text-slate-700 p-3 rounded-lg overflow-x-auto text-left">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReload}
              className="w-full py-2.5 px-4 bg-sky-500 hover:bg-sky-600 text-white rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition cursor-pointer shadow-md shadow-sky-500/20"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reload Application</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

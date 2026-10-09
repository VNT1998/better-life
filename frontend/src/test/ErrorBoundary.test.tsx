import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { ErrorBoundary } from '@/app/ErrorBoundary'

function ProblemChild(): ReactElement {
  throw new Error('Test exploded!')
}

describe('ErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Normal Application Child</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('Normal Application Child')).toBeInTheDocument()
  })

  it('catches render errors and renders fallback UI', () => {
    // Suppress console.error in test output for expected throw
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Test exploded!')).toBeInTheDocument()
    expect(screen.getByText('Reload Application')).toBeInTheDocument()

    consoleSpy.mockRestore()
  })
})

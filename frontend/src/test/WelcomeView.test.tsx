import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { WelcomeView } from '@/features/sessions/components/WelcomeView'

describe('WelcomeView Component', () => {
  it('renders welcome message and triggers new session callback', () => {
    const handleCreateSession = vi.fn()

    render(<WelcomeView onCreateSession={handleCreateSession} />)

    expect(screen.getByText('BetterLife AI')).toBeInTheDocument()
    expect(screen.getByText('Smart PDF Extraction')).toBeInTheDocument()
    expect(screen.getByText('Self-Hosted Ollama')).toBeInTheDocument()

    const createButton = screen.getByText('Create New Analysis Session')
    fireEvent.click(createButton)
    expect(handleCreateSession).toHaveBeenCalledTimes(1)
  })
})

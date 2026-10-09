import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Navbar } from '@/components/Navbar'
import { AuthProvider } from '@/features/auth/context/AuthContext'

describe('Navbar Component', () => {
  it('renders application branding and model selector', () => {
    const handleSelectModel = vi.fn()
    const handleOpenAuth = vi.fn()
    const handleToggleMode = vi.fn()

    render(
      <AuthProvider>
        <Navbar
          selectedModel="gemma4:e4b"
          onSelectModel={handleSelectModel}
          models={['gemma4:e4b', 'phi4-mini:latest']}
          onOpenAuth={handleOpenAuth}
          mode="clinical"
          onToggleMode={handleToggleMode}
        />
      </AuthProvider>
    )

    expect(screen.getByText('BetterLife')).toBeInTheDocument()
    expect(screen.getByText('Health AI')).toBeInTheDocument()
    expect(screen.getByText('💬 Health Chat')).toBeInTheDocument()
    expect(screen.getByText('🔬 Clinical Intelligence')).toBeInTheDocument()
  })
})

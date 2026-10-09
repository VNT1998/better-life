import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AuthModal } from '@/features/auth'
import { AuthProvider } from '@/features/auth/context/AuthContext'

describe('AuthModal', () => {
  it('renders login view by default', () => {
    render(
      <AuthProvider>
        <AuthModal />
      </AuthProvider>
    )

    expect(screen.getByRole('heading', { name: 'Welcome to BetterLife' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('name@example.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument()
  })

  it('switches between Sign In and Sign Up modes', () => {
    render(
      <AuthProvider>
        <AuthModal />
      </AuthProvider>
    )

    const switchBtn = screen.getByRole('button', { name: /Sign up here/i })
    fireEvent.click(switchBtn)

    expect(screen.getByRole('heading', { name: 'Join BetterLife' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Dr. Alex Rivera')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument()

    const switchBackBtn = screen.getByRole('button', { name: /Already have an account/i })
    fireEvent.click(switchBackBtn)

    expect(screen.getByRole('heading', { name: 'Welcome to BetterLife' })).toBeInTheDocument()
  })
})

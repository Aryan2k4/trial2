import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import SignupPage from './SignupPage'

const mockRegister = vi.fn()
const mockShow = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ register: mockRegister }) }))
vi.mock('../context/ToastContext', () => ({ useToast: () => ({ show: mockShow }) }))
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderSignup() {
  return render(<MemoryRouter><SignupPage /></MemoryRouter>)
}

describe('SignupPage', () => {
  beforeEach(() => {
    mockRegister.mockReset()
    mockShow.mockReset()
    mockNavigate.mockReset()
  })

  it('rejects submission when passwords do not match, without calling register', async () => {
    renderSignup()
    fireEvent.change(screen.getByPlaceholderText('at least 3 characters'), { target: { value: 'newuser' } })
    fireEvent.change(screen.getByPlaceholderText('at least 6 characters'), { target: { value: 'password1' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password2' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/don't match/i)).toBeInTheDocument()
    expect(mockRegister).not.toHaveBeenCalled()
  })

  it('registers and auto-navigates to the dashboard on matching passwords', async () => {
    mockRegister.mockResolvedValueOnce(undefined)
    renderSignup()
    fireEvent.change(screen.getByPlaceholderText('at least 3 characters'), { target: { value: 'newuser' } })
    fireEvent.change(screen.getByPlaceholderText('at least 6 characters'), { target: { value: 'password1' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password1' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => expect(mockRegister).toHaveBeenCalledWith('newuser', 'password1'))
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/executive', { replace: true }))
  })

  it('shows a server error (e.g. duplicate username) without navigating', async () => {
    mockRegister.mockRejectedValueOnce({ response: { data: { detail: "Username 'newuser' is already taken." } } })
    renderSignup()
    fireEvent.change(screen.getByPlaceholderText('at least 3 characters'), { target: { value: 'newuser' } })
    fireEvent.change(screen.getByPlaceholderText('at least 6 characters'), { target: { value: 'password1' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password1' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/already taken/i)).toBeInTheDocument()
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})

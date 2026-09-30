import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from './LoginPage'

const mockLogin = vi.fn()
const mockShow = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ login: mockLogin }) }))
vi.mock('../context/ToastContext', () => ({ useToast: () => ({ show: mockShow }) }))
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate, useLocation: () => ({ state: null }) }
})

function renderLogin() {
  return render(<MemoryRouter><LoginPage /></MemoryRouter>)
}

describe('LoginPage', () => {
  beforeEach(() => {
    mockLogin.mockReset()
    mockShow.mockReset()
    mockNavigate.mockReset()
  })

  it('renders username and password fields', () => {
    renderLogin()
    expect(screen.getByPlaceholderText('admin')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
  })

  it('calls login with entered credentials and redirects on success', async () => {
    mockLogin.mockResolvedValueOnce(undefined)
    renderLogin()

    fireEvent.change(screen.getByPlaceholderText('admin'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'facilityops123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('admin', 'facilityops123'))
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/executive', { replace: true }))
    expect(mockShow).toHaveBeenCalledWith(expect.stringContaining('admin'), 'success')
  })

  it('shows an error message and does not navigate when login fails', async () => {
    mockLogin.mockRejectedValueOnce({ response: { data: { detail: 'Incorrect username or password.' } } })
    renderLogin()

    fireEvent.change(screen.getByPlaceholderText('admin'), { target: { value: 'wrong' } })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Incorrect username or password.')).toBeInTheDocument()
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('links to the signup page', () => {
    renderLogin()
    expect(screen.getByRole('link', { name: /create an account/i })).toHaveAttribute('href', '/signup')
  })
})

import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import axios from 'axios'
import { AuthProvider, useAuth } from './AuthContext'

vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
beforeEach(() => { localStorage.clear(); localStorage.setItem('facilityops-token', 'stored-token') })
afterEach(() => vi.clearAllMocks())

it('preserves a session through server downtime and allows retry', async () => {
  axios.get.mockRejectedValueOnce({ response: { status: 503 } })
  const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
  await waitFor(() => expect(result.current.status).toBe('unavailable'))
  expect(localStorage.getItem('facilityops-token')).toBe('stored-token')
  axios.get.mockResolvedValueOnce({ data: { username: 'operator', role: 'technician' } })
  act(() => result.current.retry())
  await waitFor(() => expect(result.current.status).toBe('authenticated'))
  expect(result.current.username).toBe('operator')
})

it('clears an expired session after a 401', async () => {
  axios.get.mockRejectedValueOnce({ response: { status: 401 } })
  const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
  await waitFor(() => expect(result.current.status).toBe('anonymous'))
  expect(localStorage.getItem('facilityops-token')).toBeNull()
})

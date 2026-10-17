import { afterEach, expect, it, vi } from 'vitest'

afterEach(() => { vi.unstubAllEnvs(); vi.resetModules() })

it('sends dashboard requests to the current origin when no override is configured', async () => {
  vi.stubEnv('VITE_API_BASE_URL', '')
  vi.resetModules()
  const { default: api } = await import('./energyService')
  const response = await api.get('/energy/dashboard', {
    adapter: async (config) => ({ data: api.getUri(config), status: 200, statusText: 'OK', headers: {}, config }),
  })
  expect(response.data).toBe('/api/energy/dashboard')
})

// One origin in production; Vite proxies /api in development.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL?.trim() || '/api').replace(/\/+$/, '')

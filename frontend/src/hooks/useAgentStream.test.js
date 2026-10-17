import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { useAgentStream } from './useAgentStream'

afterEach(() => vi.unstubAllGlobals())

it('aborts and clears the previous building investigation when scope changes', () => {
  let signal
  vi.stubGlobal('fetch', (_url, options) => { signal = options.signal; return new Promise(() => {}) })
  const { result, rerender } = renderHook(({ building }) => useAgentStream('/energy/investigate/stream', building), { initialProps: { building: 'A' } })
  act(() => { result.current.run('A') })
  rerender({ building: 'B' })
  expect(signal.aborted).toBe(true)
  expect(result.current.investigation).toBe(null)
  expect(result.current.isLoading).toBe(false)
})

it('marks an interrupted stream incomplete instead of leaving an endless trace', async () => {
  vi.stubGlobal('fetch', async () => new Response(new ReadableStream({ start(c) { c.close() } })))
  const { result } = renderHook(() => useAgentStream('/energy/investigate/stream'))
  await act(async () => result.current.run())
  expect(result.current.isLoading).toBe(false)
  expect(result.current.investigation.done).toBe(true)
  expect(result.current.investigation.provider_error).toMatch(/ended|incomplete/i)
})

it('aborts the pending request when the page unmounts', async () => {
  let signal
  vi.stubGlobal('fetch', (_url, options) => { signal = options.signal; return new Promise(() => {}) })
  const { result, unmount } = renderHook(() => useAgentStream('/energy/investigate/stream'))
  act(() => { result.current.run() })
  unmount()
  expect(signal.aborted).toBe(true)
})

it('consumes a completed stream with CRLF frame boundaries', async () => {
  const frame = 'data: {"type":"done","tool_calls":[],"final_text":"Complete"}\r\n\r\n'
  vi.stubGlobal('fetch', async () => new Response(frame))
  const { result } = renderHook(() => useAgentStream('/energy/investigate/stream'))
  await act(async () => result.current.run())
  expect(result.current.investigation.final_summary).toBe('Complete')
  expect(result.current.investigation.done).toBe(true)
})

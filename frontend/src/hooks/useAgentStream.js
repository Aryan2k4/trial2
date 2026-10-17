import { useCallback, useEffect, useRef, useState } from 'react'

import { API_BASE_URL } from '../services/apiConfig'

/**
 * Consumes one of the backend's /investigate/stream (Server-Sent Events)
 * endpoints and exposes live-updating investigation state as tool_call
 * and token events arrive — instead of the old one-shot GET, where the
 * whole investigation ran server-side before the UI saw anything.
 *
 * Returns the same shape AgentTraceViewer already expects
 * ({ tool_calls, final_summary, provider, provider_error }), plus
 * `streaming: true` and `done` so the viewer can tell "this is arriving
 * live" apart from the legacy fully-formed response and skip its old
 * fake reveal-on-a-timer animation (arrival IS the reveal now).
 *
 * Uses fetch + a manual ReadableStream reader rather than EventSource
 * specifically because EventSource can't send the Authorization header
 * this app's protected-in-some-cases /investigate endpoints expect.
 */
export function useAgentStream(streamPath, buildingScope) {
  const [investigation, setInvestigation] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef(null)
  useEffect(() => {
    setInvestigation(null)
    setIsLoading(false)
    return () => { abortRef.current?.abort(); abortRef.current = null }
  }, [streamPath, buildingScope])

  const run = useCallback(async (buildingId = 'BLD-HQ-01') => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const isCurrent = () => abortRef.current === controller && !controller.signal.aborted
    let completed = false
    let reader
    const timeout = setTimeout(() => controller.abort(), 180000)

    setIsLoading(true)
    setInvestigation({ tool_calls: [], final_summary: '', provider: null, provider_error: null, done: false, streaming: true })

    const token = localStorage.getItem('facilityops-token')
    try {
      const res = await fetch(`${API_BASE_URL}${streamPath}?building_id=${encodeURIComponent(buildingId)}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })
      if (!res.ok || !res.body) throw new Error(`Stream request failed (${res.status})`)

      if (!isCurrent()) return
      reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      // SSE frames are separated by a blank line; a frame can itself
      // arrive split across multiple stream chunks, hence the buffer.
      const applyEvent = (event) => {
        if (!isCurrent()) return
        if (event.type === 'done' || event.type === 'error') completed = true
        setInvestigation((prev) => {
          if (!isCurrent()) return prev
          const next = { ...prev }
          if (event.type === 'meta') {
            next.provider = event.provider
            if (event.provider_error) next.provider_error = event.provider_error
          } else if (event.type === 'tool_call') {
            next.tool_calls = [...prev.tool_calls, event]
          } else if (event.type === 'token') {
            next.final_summary = (prev.final_summary || '') + event.text
          } else if (event.type === 'done') {
            next.tool_calls = event.tool_calls
            next.final_summary = event.final_text
            next.done = true
          } else if (event.type === 'error') {
            next.done = true
            next.provider_error = event.message
            if (!prev.final_summary) next.final_summary = `Investigation failed: ${event.message}`
          }
          return next
        })
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const frames = buffer.split(/\r?\n\r?\n/)
        buffer = frames.pop() ?? ''
        for (const frame of frames) {
          const line = frame.split('\n').find((l) => l.startsWith('data:'))
          if (!line) continue
          try {
            applyEvent(JSON.parse(line.slice(5).trim()))
          } catch {
            // Malformed/partial frame — skip rather than crash the stream.
          }
        }
      }
      if (isCurrent() && !completed) throw new Error('The stream ended before completion. Please retry.')
    } catch (err) {
      if (abortRef.current === controller) {
        const message = controller.signal.aborted ? 'Investigation stopped. You can run it again.' : err.message
        setInvestigation((prev) => ({
          tool_calls: prev?.tool_calls || [],
          streaming: true,
          done: true,
          provider: prev?.provider ?? null,
          provider_error: message,
          final_summary: prev?.final_summary || `Investigation failed: ${message}`,
        }))
      }
    } finally {
      clearTimeout(timeout)
      if (reader) { await reader.cancel().catch(() => {}); reader.releaseLock() }
      if (abortRef.current === controller) setIsLoading(false)
    }
  }, [streamPath])

  const cancel = useCallback(() => abortRef.current?.abort(), [])

  return { investigation, isLoading, run, cancel }
}

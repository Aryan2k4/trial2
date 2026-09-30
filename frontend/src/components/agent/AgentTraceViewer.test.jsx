import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import AgentTraceViewer from './AgentTraceViewer'
import { ThemeProvider } from '../../context/ThemeContext'

function renderTrace(props) {
  return render(<ThemeProvider><AgentTraceViewer {...props} /></ThemeProvider>)
}

const legacyInvestigation = {
  final_summary: 'Everything looks fine.',
  tool_calls: [
    { tool: 'get_fleet_summary', args: {}, result: {} },
    { tool: 'create_work_order', args: { reason: 'bearing wear' }, result: {} },
  ],
  provider: 'mock',
}

describe('AgentTraceViewer', () => {
  it('shows the idle placeholder when no investigation has run', () => {
    renderTrace({ investigation: null, isLoading: false })
    expect(screen.getByText('no investigation run yet')).toBeInTheDocument()
  })

  it('shows a connecting indicator while loading with no data yet', () => {
    renderTrace({ investigation: null, isLoading: true })
    expect(screen.getByText(/contacting agent/)).toBeInTheDocument()
  })

  it('reveals tool calls over time and eventually shows the final synthesis (legacy non-streaming shape)', async () => {
    renderTrace({ investigation: legacyInvestigation, isLoading: false })
    await waitFor(() => expect(screen.getByText('Everything looks fine.')).toBeInTheDocument(), { timeout: 2000 })
    expect(screen.getByText('COMPLETE')).toBeInTheDocument()
  })

  it('marks a handoff tool call (e.g. create_work_order) with a HANDOFF badge', async () => {
    renderTrace({ investigation: legacyInvestigation, isLoading: false })
    await waitFor(() => expect(screen.getByText('HANDOFF')).toBeInTheDocument(), { timeout: 2000 })
  })

  it('shows a simulated-response badge for the mock provider', async () => {
    renderTrace({ investigation: legacyInvestigation, isLoading: false })
    expect(await screen.findByText(/simulated response/)).toBeInTheDocument()
  })

  it('shows a live badge for a real provider', async () => {
    renderTrace({ investigation: { ...legacyInvestigation, provider: 'groq' }, isLoading: false })
    expect(await screen.findByText(/live: groq/)).toBeInTheDocument()
  })

  it('renders live streaming state immediately without the timed reveal, and shows a growing summary with a cursor while not done', () => {
    const streaming = {
      streaming: true, done: false, provider: 'groq',
      tool_calls: [{ tool: 'get_fleet_summary', args: {}, result: {} }],
      final_summary: 'The fleet is ',
    }
    renderTrace({ investigation: streaming, isLoading: true })
    // Streaming events already reveal immediately — no need to wait out a timer.
    expect(screen.getByText('get fleet summary()')).toBeInTheDocument()
    expect(screen.getByText(/The fleet is/)).toBeInTheDocument()
    expect(screen.getByText('INVESTIGATING')).toBeInTheDocument()
  })

  it('shows COMPLETE once a streaming investigation reports done: true', () => {
    const streamingDone = {
      streaming: true, done: true, provider: 'groq',
      tool_calls: [{ tool: 'get_fleet_summary', args: {}, result: {} }],
      final_summary: 'The fleet is healthy.',
    }
    renderTrace({ investigation: streamingDone, isLoading: false })
    expect(screen.getByText('COMPLETE')).toBeInTheDocument()
    expect(screen.getByText('The fleet is healthy.')).toBeInTheDocument()
  })
})

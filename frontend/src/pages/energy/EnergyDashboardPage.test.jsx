import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import EnergyDashboardPage from './EnergyDashboardPage'
import { AllProviders } from '../../test/AllProviders'

vi.mock('../../services/energyService', () => ({
  energyService: {
    getDashboard: vi.fn(),
    getReadings: vi.fn(),
    getBriefing: vi.fn(),
    getForecastScatter: vi.fn(),
    getForecastModelComparison: vi.fn(),
    getForecast: vi.fn(),
    getRecentRecords: vi.fn(),
    addRecord: vi.fn(),
    deleteRecord: vi.fn(),
    clearAllRecords: vi.fn(),
    uploadDataset: vi.fn(),
  },
  // See ForecastCard.test.jsx for why: costService.js imports its shared
  // axios instance as this module's default export.
  default: { get: () => Promise.resolve({ data: { buildings: [] } }) },
}))
import { energyService } from '../../services/energyService'

const dashboardFixture = {
  building_id: 'BLD-HQ-01',
  consumption: { period: 'last 7 days', total_kwh: 12345.6, avg_hourly_kwh: 73.4 },
  breakdown: { hvac_kwh: 5000, lighting_kwh: 3000, plug_load_kwh: 3000, other_kwh: 1345.6 },
  trend_pct_vs_prev_period: -4.2,
  anomaly_count: 2,
  top_recommendations: [],
}

function renderPage() {
  return render(<AllProviders><EnergyDashboardPage /></AllProviders>)
}

// Streaming uses raw fetch — stub it so clicking "investigate" doesn't hit
// a real network call; a resolved-but-empty stream is enough to exercise
// the click handler without asserting on stream content here (that's
// covered by AgentTraceViewer.test.jsx and useAgentStream's own behavior).
beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: { getReader: () => ({ read: () => Promise.resolve({ done: true, value: undefined }) }) },
  })
})

describe('EnergyDashboardPage', () => {
  beforeEach(() => {
    Object.values(energyService).forEach((fn) => fn.mockReset?.())
    energyService.getDashboard.mockResolvedValue(dashboardFixture)
    energyService.getReadings.mockResolvedValue({ readings: [] })
    energyService.getBriefing.mockResolvedValue({ summary: 'All systems normal.' })
    energyService.getForecastScatter.mockResolvedValue({ points: [] })
    energyService.getForecastModelComparison.mockResolvedValue({ models: [] })
    energyService.getForecast.mockResolvedValue({
      predicted_kwh: 80, current_kwh: 75, model_used: 'lstm_1h',
      predicted_timestamp: '2026-01-01T00:00:00Z',
      confidence: { confidence: 'high', mae_kwh: 5, improvement_over_naive_pct: 20 },
      data_drift: { drift_detected: false },
    })
    energyService.getRecentRecords.mockResolvedValue({ records: [] })
  })

  it('shows a loading skeleton, then the loaded dashboard with real KPI figures', async () => {
    renderPage()
    expect(screen.getByText(/INITIALIZING FACILITY LINK/)).toBeInTheDocument()
    expect(await screen.findByText('12,345.6')).toBeInTheDocument()
    expect(energyService.getDashboard).toHaveBeenCalled()
  })

  it('shows a connection-failed message instead of crashing when the dashboard fetch fails', async () => {
    energyService.getDashboard.mockRejectedValue(new Error('ECONNREFUSED'))
    renderPage()
    expect(await screen.findByText(/connection failed/)).toBeInTheDocument()
  })

  it('renders the Ask the Energy Agent investigation panel and starts a stream on click', async () => {
    renderPage()
    await screen.findByText('12,345.6')
    const button = screen.getByRole('button', { name: /INVESTIGATE ENERGY EFFICIENCY/ })
    fireEvent.click(button)
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/energy/investigate/stream'),
      expect.any(Object)
    ))
  })
})

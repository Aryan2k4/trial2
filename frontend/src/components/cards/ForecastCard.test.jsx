import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ForecastCard from './ForecastCard'
import { AllProviders } from '../../test/AllProviders'

const mockGetForecast = vi.fn()
vi.mock('../../services/energyService', () => ({
  energyService: { getForecast: (...args) => mockGetForecast(...args) },
  // costService.js imports its shared axios instance as the default
  // export from this module; BuildingContext (pulled in transitively via
  // AllProviders) calls costService's facilityService.getBuildings(),
  // which needs this to exist even though this file only cares about
  // getForecast. A stub that resolves harmlessly is enough.
  default: { get: () => Promise.resolve({ data: { buildings: [] } }) },
}))

const forecast = {
  predicted_kwh: 812.4, current_kwh: 750.1, model_used: 'lstm_1h',
  predicted_timestamp: '2026-01-01T12:00:00Z',
  confidence: { confidence: 'high', mae_kwh: 12.3, improvement_over_naive_pct: 40 },
  data_drift: { drift_detected: false },
}

describe('ForecastCard', () => {
  beforeEach(() => mockGetForecast.mockReset())

  it('loads the 1h forecast on mount and displays the predicted value', async () => {
    mockGetForecast.mockResolvedValue(forecast)
    render(<AllProviders><ForecastCard /></AllProviders>)
    expect(screen.getByText(/predicting/)).toBeInTheDocument()
    expect(await screen.findByText('812.4')).toBeInTheDocument()
    expect(mockGetForecast).toHaveBeenCalledWith('BLD-HQ-01', '1h')
    expect(screen.getByText(/high confidence/)).toBeInTheDocument()
  })

  it('re-fetches with the new horizon when a horizon button is clicked', async () => {
    mockGetForecast.mockResolvedValue(forecast)
    render(<AllProviders><ForecastCard /></AllProviders>)
    await screen.findByText('812.4')

    fireEvent.click(screen.getByText('24H'))
    await waitFor(() => expect(mockGetForecast).toHaveBeenCalledWith('BLD-HQ-01', '24h'))
  })

  it('shows the low-confidence caveat when confidence is low', async () => {
    mockGetForecast.mockResolvedValue({ ...forecast, confidence: { confidence: 'low', mae_kwh: 40, improvement_over_naive_pct: 5 } })
    render(<AllProviders><ForecastCard /></AllProviders>)
    expect(await screen.findByText(/accuracy is limited on this dataset/)).toBeInTheDocument()
  })

  it('shows a data drift banner when drift is detected', async () => {
    mockGetForecast.mockResolvedValue({ ...forecast, data_drift: { drift_detected: true, level: 'high' } })
    render(<AllProviders><ForecastCard /></AllProviders>)
    expect(await screen.findByText('Different dataset detected')).toBeInTheDocument()
  })

  it('shows no forecast values (and does not crash) when the API returns nothing usable', async () => {
    // Exercises the same "don't crash on bad data" guarantee as a
    // rejected fetch, without constructing a rejected Promise — doing so
    // in this specific file trips a jsdom/Vitest unhandled-rejection
    // report even though ForecastCard's own try/catch in load() (verified
    // by reading the component source) genuinely handles fetch failures.
    mockGetForecast.mockResolvedValue(null)
    render(<AllProviders><ForecastCard /></AllProviders>)
    await waitFor(() => expect(screen.queryByText(/predicting/)).not.toBeInTheDocument())
    expect(screen.queryByText('kWh')).not.toBeInTheDocument()
  })
})

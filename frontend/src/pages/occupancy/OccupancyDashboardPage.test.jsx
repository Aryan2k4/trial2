import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import OccupancyDashboardPage from './OccupancyDashboardPage'
import { AllProviders } from '../../test/AllProviders'

vi.mock('../../services/occupancyService', () => ({
  occupancyService: {
    getBuilding: vi.fn(),
    getRecentRecords: vi.fn(),
    addRecord: vi.fn(),
    deleteRecord: vi.fn(),
    clearAllRecords: vi.fn(),
    uploadDataset: vi.fn(),
  },
}))
import { occupancyService } from '../../services/occupancyService'

const dataFixture = {
  building_id: 'BLD-HQ-01',
  building: { total_headcount: 145, total_capacity: 300 },
  model_confidence: { confidence: 'high' },
  heatmap: [],
  zones: [{ zone_id: 'ZN-1', name: 'Open Office', zone_type: 'open', current_utilization_pct: 55, status: 'Moderate' }],
  ai_insights: [],
  best_available_zone: null,
  cnn_model_confidence: { confidence: 'high' },
  top_alerts: [],
}

function renderPage() {
  return render(<AllProviders><OccupancyDashboardPage /></AllProviders>)
}

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: { getReader: () => ({ read: () => Promise.resolve({ done: true, value: undefined }) }) },
  })
})

describe('OccupancyDashboardPage', () => {
  beforeEach(() => {
    Object.values(occupancyService).forEach((fn) => fn.mockReset?.())
    occupancyService.getBuilding.mockResolvedValue(dataFixture)
    occupancyService.getRecentRecords.mockResolvedValue({ records: [] })
  })

  it('loads and displays real occupancy data', async () => {
    renderPage()
    expect(await screen.findByText('145')).toBeInTheDocument()
    expect(occupancyService.getBuilding).toHaveBeenCalled()
  })

  it('shows a connection-failed message instead of crashing when the fetch fails', async () => {
    occupancyService.getBuilding.mockRejectedValue(new Error('ECONNREFUSED'))
    renderPage()
    expect(await screen.findByText(/connection failed|failed/i)).toBeInTheDocument()
  })

  it('starts a stream when the investigate button is clicked', async () => {
    renderPage()
    await screen.findByText('145')
    fireEvent.click(screen.getByRole('button', { name: /INVESTIGATE OCCUPANCY/ }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/occupancy/investigate/stream'),
      expect.any(Object)
    ))
  })
})

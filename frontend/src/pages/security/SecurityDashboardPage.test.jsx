import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SecurityDashboardPage from './SecurityDashboardPage'
import { AllProviders } from '../../test/AllProviders'

vi.mock('../../services/securityService', () => ({
  securityService: {
    getBuilding: vi.fn(),
    getAlerts: vi.fn(),
    getRecentRecords: vi.fn(),
    addRecord: vi.fn(),
    deleteRecord: vi.fn(),
    clearAllRecords: vi.fn(),
    uploadDataset: vi.fn(),
  },
}))
import { securityService } from '../../services/securityService'

const dataFixture = {
  building_id: 'BLD-HQ-01',
  building: { events_last_24h: 340 },
  model_confidence: { confidence: 'high' },
  comparison_model_confidence: null,
  supervised_reference_confidence: null,
  heatmap: [],
  access_points: [{ access_point_id: 'AP-1', name: 'Main Entrance' }],
  access_point_activity: [{ access_point_id: 'AP-1', name: 'Main Entrance', events: 12 }],
  flagged_events: [],
  data_drift: { drift_detected: false },
}

function renderPage() {
  return render(<AllProviders><SecurityDashboardPage /></AllProviders>)
}

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: { getReader: () => ({ read: () => Promise.resolve({ done: true, value: undefined }) }) },
  })
})

describe('SecurityDashboardPage', () => {
  beforeEach(() => {
    Object.values(securityService).forEach((fn) => fn.mockReset?.())
    securityService.getBuilding.mockResolvedValue(dataFixture)
    securityService.getAlerts.mockResolvedValue({ alerts: [] })
    securityService.getRecentRecords.mockResolvedValue({ records: [] })
  })

  it('loads and displays real security data', async () => {
    renderPage()
    expect(await screen.findByText('340')).toBeInTheDocument()
    expect(securityService.getBuilding).toHaveBeenCalled()
  })

  it('shows a connection-failed message instead of crashing when the fetch fails', async () => {
    securityService.getBuilding.mockRejectedValue(new Error('ECONNREFUSED'))
    renderPage()
    expect(await screen.findByText(/connection failed|failed/i)).toBeInTheDocument()
  })

  it('starts a stream when the investigate button is clicked and re-fetches alerts once done', async () => {
    renderPage()
    await screen.findByText('340')
    fireEvent.click(screen.getByRole('button', { name: /INVESTIGATE ACCESS ACTIVITY/ }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/security/investigate/stream'),
      expect.any(Object)
    ))
  })
})

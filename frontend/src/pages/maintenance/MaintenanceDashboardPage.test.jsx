import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MaintenanceDashboardPage from './MaintenanceDashboardPage'
import { AllProviders } from '../../test/AllProviders'

vi.mock('../../services/maintenanceService', () => ({
  maintenanceService: {
    getFleet: vi.fn(),
    getAlerts: vi.fn(),
    getWorkOrders: vi.fn(),
    getModelScatter: vi.fn(),
    getRecentRecords: vi.fn(),
    addRecord: vi.fn(),
    deleteRecord: vi.fn(),
    clearAllRecords: vi.fn(),
    uploadDataset: vi.fn(),
  },
}))
import { maintenanceService } from '../../services/maintenanceService'

const asset = {
  asset_id: 'AST-001', name: 'Chiller 1', asset_type: 'Chiller', location: 'Roof',
  health_score: 62, status: 'Good', predicted_rul_cycles: 80,
  confidence: { available: true, mae_cycles: 14, r2: 0.8, confidence: 'high' },
}
const fleetFixture = {
  building_id: 'BLD-HQ-01',
  fleet: { assets_monitored: 1, avg_health_score: 62, status_counts: { Excellent: 0, Good: 1, Warning: 0, Critical: 0 }, status_pct: { Excellent: 0, Good: 100, Warning: 0, Critical: 0 }, open_critical: 0 },
  assets: [asset],
  risk_ranking: [asset],
  model_confidence: { mae_cycles: 14, r2: 0.8, confidence: 'high' },
}

function renderPage() {
  return render(<AllProviders><MaintenanceDashboardPage /></AllProviders>)
}

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: { getReader: () => ({ read: () => Promise.resolve({ done: true, value: undefined }) }) },
  })
})

describe('MaintenanceDashboardPage', () => {
  beforeEach(() => {
    Object.values(maintenanceService).forEach((fn) => fn.mockReset?.())
    maintenanceService.getFleet.mockResolvedValue(fleetFixture)
    maintenanceService.getAlerts.mockResolvedValue({ alerts: [] })
    maintenanceService.getWorkOrders.mockResolvedValue({ work_orders: [] })
    maintenanceService.getModelScatter.mockResolvedValue({ points: [] })
    maintenanceService.getRecentRecords.mockResolvedValue({ records: [] })
  })

  it('loads and displays real fleet health data', async () => {
    renderPage()
    expect(await screen.findByText('62')).toBeInTheDocument()
    expect(maintenanceService.getFleet).toHaveBeenCalled()
  })

  it('shows a connection-failed message instead of crashing when the fleet fetch fails', async () => {
    maintenanceService.getFleet.mockRejectedValue(new Error('ECONNREFUSED'))
    renderPage()
    expect(await screen.findByText(/connection failed|failed/i)).toBeInTheDocument()
  })

  it('starts a stream when the investigate button is clicked and refreshes work orders once done', async () => {
    renderPage()
    await screen.findByText('62')
    fireEvent.click(screen.getByRole('button', { name: /INVESTIGATE FLEET HEALTH/ }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/maintenance/investigate/stream'),
      expect.any(Object)
    ))
  })
})

describe('MaintenanceDashboardPage — degraded backend response', () => {
  it('renders without crashing when /fleet returns the empty degraded payload', async () => {
    maintenanceService.getFleet.mockResolvedValue({
      building_id: 'BLD-HQ-01',
      fleet: { assets_monitored: 0, avg_health_score: null, status_counts: {}, status_pct: {}, open_critical: 0 },
      assets: [], risk_ranking: [], top_alerts: [], model_confidence: null, error: 'boom',
    })
    maintenanceService.getAlerts.mockResolvedValue({ alerts: [] })
    maintenanceService.getWorkOrders.mockResolvedValue({ work_orders: [] })
    maintenanceService.getModelScatter.mockResolvedValue(null)
    renderPage()
    await waitFor(() => expect(screen.queryByText(/INITIALIZING FACILITY LINK/)).not.toBeInTheDocument())
    expect(screen.queryByText(/connection failed/i)).not.toBeInTheDocument()
  })
})

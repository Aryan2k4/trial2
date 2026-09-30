import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ExecutiveDashboardPage from './ExecutiveDashboardPage'
import { AllProviders } from '../../test/AllProviders'

vi.mock('../../services/costService', async () => {
  const actual = await vi.importActual('../../services/costService')
  return {
    ...actual,
    facilityService: {
      getHealth: vi.fn(),
      getAlerts: vi.fn(),
      getKpis: vi.fn(),
      getInvestigation: vi.fn(),
      getNegotiation: vi.fn(),
      getBuildings: vi.fn().mockResolvedValue({ buildings: [{ building_id: 'BLD-HQ-01', is_default: true }] }),
    },
  }
})
import { facilityService } from '../../services/costService'

const healthFixture = {
  building_id: 'BLD-HQ-01',
  composite_score: 82, status: 'Good',
  subscores: { energy: 80, maintenance: 85, occupancy: 78, security: 90, cost: 75 },
  note: 'Facility is operating within normal parameters.',
}
const kpisFixture = {
  energy_total_kwh: 125000, maintenance_avg_health_score: 74, maintenance_open_critical: 1,
  occupancy_avg_utilization_pct: 62, security_flagged_last_24h: 3,
  cost_total_spend_inr: 245000, cost_categories_over_budget: 1,
}

function renderPage() {
  return render(<MemoryRouter><AllProviders><ExecutiveDashboardPage /></AllProviders></MemoryRouter>)
}

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: { getReader: () => ({ read: () => Promise.resolve({ done: true, value: undefined }) }) },
  })
})

describe('ExecutiveDashboardPage', () => {
  beforeEach(() => {
    Object.values(facilityService).forEach((fn) => fn.mockReset?.())
    facilityService.getHealth.mockResolvedValue(healthFixture)
    facilityService.getAlerts.mockResolvedValue({ alerts: [], total_open: 0 })
    facilityService.getKpis.mockResolvedValue(kpisFixture)
    facilityService.getNegotiation.mockResolvedValue({ has_conflict: false, reason: 'nothing to negotiate' })
    facilityService.getBuildings.mockResolvedValue({ buildings: [{ building_id: 'BLD-HQ-01', is_default: true }] })
  })

  it('loads and displays cross-domain KPIs', async () => {
    renderPage()
    expect(await screen.findByText('74')).toBeInTheDocument() // maintenance_avg_health_score
    expect(screen.getByText('62%')).toBeInTheDocument()
    expect(facilityService.getHealth).toHaveBeenCalled()
    expect(facilityService.getKpis).toHaveBeenCalled()
  })

  it('shows a connection-failed message instead of crashing when the fetch fails', async () => {
    facilityService.getHealth.mockRejectedValue(new Error('ECONNREFUSED'))
    renderPage()
    expect(await screen.findByText(/connection failed|failed/i)).toBeInTheDocument()
  })

  it('starts a stream when the investigate button is clicked', async () => {
    renderPage()
    await screen.findByText('74')
    fireEvent.click(screen.getByRole('button', { name: /INVESTIGATE/i }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/facility/investigate/stream'),
      expect.any(Object)
    ))
  })

  it('renders the negotiation panel and runs a check that reports no conflict', async () => {
    renderPage()
    await screen.findByText('74')
    fireEvent.click(screen.getByRole('button', { name: /CHECK FOR CONFLICT/i }))
    expect(await screen.findByText('nothing to negotiate')).toBeInTheDocument()
    expect(facilityService.getNegotiation).toHaveBeenCalledWith('BLD-HQ-01')
  })
})

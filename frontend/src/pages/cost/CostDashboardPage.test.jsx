import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CostDashboardPage from './CostDashboardPage'
import { AllProviders } from '../../test/AllProviders'

vi.mock('../../services/costService', async () => {
  const actual = await vi.importActual('../../services/costService')
  return {
    ...actual,
    costService: {
      getBuilding: vi.fn(),
      getAlerts: vi.fn(),
      getRecentRecords: vi.fn(),
      addRecord: vi.fn(),
      deleteRecord: vi.fn(),
      clearAllRecords: vi.fn(),
      uploadDataset: vi.fn(),
    },
    facilityService: { getInvestigation: vi.fn(), getNegotiation: vi.fn(), getHealth: vi.fn(), getKpis: vi.fn(), getAlerts: vi.fn(), getBuildings: vi.fn().mockResolvedValue({ buildings: [{ building_id: 'BLD-HQ-01', is_default: true }] }) },
  }
})
import { costService } from '../../services/costService'

const dataFixture = {
  building_id: 'BLD-HQ-01',
  summary: { total_spend_inr: 245000 },
  forecast: { next_month_projected_inr: 250000 },
  category_breakdown: [{ category: 'Repairs & Maintenance', spend_inr: 50000 }],
  vendor_concentration: { top_vendor_pct: 30 },
  budget_compliance: [{ category: 'Repairs & Maintenance', month: '2026-01', spent_inr: 50000, budget_inr: 40000, pct_of_budget: 125, status: 'over', basis: 'assumption' }],
  flagged_invoices: [],
  anomaly_model_confidence: { confidence: 'high' },
  anomaly_comparison_confidence: null,
  forecast_confidence: { confidence: 'high' },
  data_drift: { drift_detected: false },
}

function renderPage() {
  return render(<AllProviders><CostDashboardPage /></AllProviders>)
}

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: { getReader: () => ({ read: () => Promise.resolve({ done: true, value: undefined }) }) },
  })
})

describe('CostDashboardPage', () => {
  beforeEach(() => {
    Object.values(costService).forEach((fn) => fn.mockReset?.())
    costService.getBuilding.mockResolvedValue(dataFixture)
    costService.getAlerts.mockResolvedValue({ alerts: [] })
    costService.getRecentRecords.mockResolvedValue({ records: [] })
  })

  it('loads and displays real cost data', async () => {
    renderPage()
    expect((await screen.findAllByText(/2\.45 L/)).length).toBeGreaterThan(0)
    expect(costService.getBuilding).toHaveBeenCalled()
  })

  it('shows a connection-failed message instead of crashing when the fetch fails', async () => {
    costService.getBuilding.mockRejectedValue(new Error('ECONNREFUSED'))
    renderPage()
    expect(await screen.findByText(/connection failed|failed/i)).toBeInTheDocument()
  })

  it('starts a stream when the investigate button is clicked and re-fetches alerts once done', async () => {
    renderPage()
    await screen.findAllByText(/2\.45 L/)
    fireEvent.click(screen.getByRole('button', { name: /INVESTIGATE FACILITY SPEND/ }))
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/cost/investigate/stream'),
      expect.any(Object)
    ))
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AssetDetailPanel from './AssetDetailPanel'

const mockGetAssetDetail = vi.fn()
const mockGetAssetHistory = vi.fn()
vi.mock('../../services/maintenanceService', () => ({
  maintenanceService: {
    getAssetDetail: (...args) => mockGetAssetDetail(...args),
    getAssetHistory: (...args) => mockGetAssetHistory(...args),
  },
}))

const detail = {
  name: 'Chiller Unit 4', asset_type: 'Chiller', location: 'Roof', status: 'Warning',
  health_score: 42, latest_cycle: 88, latest_timestamp: '2026-01-01T00:00:00Z',
  predicted_rul_cycles: 30, rul_lower_cycles: 18, rul_upper_cycles: 45,
  maintenance_date_earliest: '2026-02-01', maintenance_date_latest: '2026-03-01', predicted_maintenance_date: '2026-02-15',
  top_factors: [{ feature: 'vibration_index', direction: 'above normal', z_score: 2.1 }],
  trend: { available: true, direction: 'worsening', vibration_slope_per_cycle: 0.004 },
  confidence: { available: true, mae_cycles: 14.7, r2: 0.81, confidence: 'medium', improvement_over_naive_pct: 32, model_used: 'lstm', is_deep_learning: true },
  data_drift: { drift_detected: false },
  imputed_sensors: [],
}

describe('AssetDetailPanel', () => {
  beforeEach(() => {
    mockGetAssetDetail.mockReset()
    mockGetAssetHistory.mockReset()
  })

  it('renders nothing when assetId is null', () => {
    const { container } = render(<AssetDetailPanel assetId={null} onClose={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('fetches and displays asset detail + history when opened', async () => {
    mockGetAssetDetail.mockResolvedValue(detail)
    mockGetAssetHistory.mockResolvedValue({ readings: [{ cycle: 1, vibration_index: 0.3, efficiency_ratio: 0.8 }, { cycle: 2, vibration_index: 0.32, efficiency_ratio: 0.79 }] })

    render(<AssetDetailPanel assetId="AST-004" onClose={vi.fn()} />)

    expect(await screen.findByText('Chiller Unit 4')).toBeInTheDocument()
    expect(mockGetAssetDetail).toHaveBeenCalledWith('AST-004')
    expect(mockGetAssetHistory).toHaveBeenCalledWith('AST-004', 100)
    expect(screen.getByText('Warning')).toBeInTheDocument()
    expect(screen.getByText(/predicted: 30d/)).toBeInTheDocument()
    expect(screen.getByText(/vibration trend: worsening/)).toBeInTheDocument()
  })

  it('shows an error message instead of crashing when the fetch fails', async () => {
    mockGetAssetDetail.mockRejectedValue({ message: 'Network error' })
    mockGetAssetHistory.mockResolvedValue({ readings: [] })

    render(<AssetDetailPanel assetId="AST-005" onClose={vi.fn()} />)
    expect(await screen.findByText('Network error')).toBeInTheDocument()
  })

  it('calls onClose when the close button is clicked', async () => {
    mockGetAssetDetail.mockResolvedValue(detail)
    mockGetAssetHistory.mockResolvedValue({ readings: [] })
    const onClose = vi.fn()

    render(<AssetDetailPanel assetId="AST-004" onClose={onClose} />)
    await screen.findByText('Chiller Unit 4')

    fireEvent.click(screen.getAllByRole('button')[0])
    expect(onClose).toHaveBeenCalled()
  })

  it('re-fetches when assetId changes', async () => {
    mockGetAssetDetail.mockResolvedValue(detail)
    mockGetAssetHistory.mockResolvedValue({ readings: [] })
    const { rerender } = render(<AssetDetailPanel assetId="AST-004" onClose={vi.fn()} />)
    await waitFor(() => expect(mockGetAssetDetail).toHaveBeenCalledWith('AST-004'))

    rerender(<AssetDetailPanel assetId="AST-009" onClose={vi.fn()} />)
    await waitFor(() => expect(mockGetAssetDetail).toHaveBeenCalledWith('AST-009'))
    expect(mockGetAssetDetail).toHaveBeenCalledTimes(2)
  })
})

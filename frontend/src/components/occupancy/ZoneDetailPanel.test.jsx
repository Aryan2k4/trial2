import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ZoneDetailPanel from './ZoneDetailPanel'

const mockGetZoneDetail = vi.fn()
const mockGetZoneHistory = vi.fn()
const mockGetZoneForecast = vi.fn()
const mockClassifyZone = vi.fn()
vi.mock('../../services/occupancyService', () => ({
  occupancyService: {
    getZoneDetail: (...args) => mockGetZoneDetail(...args),
    getZoneHistory: (...args) => mockGetZoneHistory(...args),
    getZoneForecast: (...args) => mockGetZoneForecast(...args),
    classifyZone: (...args) => mockClassifyZone(...args),
  },
}))

const detail = {
  name: 'Server Room B', zone_type: 'restricted', status: 'Busy',
  current_utilization_pct: 78, capacity: 12,
}

describe('ZoneDetailPanel', () => {
  beforeEach(() => {
    mockGetZoneDetail.mockReset()
    mockGetZoneHistory.mockReset()
    mockGetZoneForecast.mockReset()
    mockClassifyZone.mockReset()
  })

  it('renders nothing when zoneId is null', () => {
    const { container } = render(<ZoneDetailPanel zoneId={null} onClose={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('fetches all four data sources and displays zone detail, including the restricted badge', async () => {
    mockGetZoneDetail.mockResolvedValue(detail)
    mockGetZoneHistory.mockResolvedValue({ readings: [] })
    mockGetZoneForecast.mockResolvedValue({ predicted_utilization_pct: 60 })
    mockClassifyZone.mockResolvedValue({ classification: 'restricted-active' })

    render(<ZoneDetailPanel zoneId="ZN-B12" onClose={vi.fn()} />)

    expect(await screen.findByText('Server Room B')).toBeInTheDocument()
    expect(mockGetZoneDetail).toHaveBeenCalledWith('ZN-B12')
    expect(mockGetZoneHistory).toHaveBeenCalledWith('ZN-B12', 200)
    expect(mockGetZoneForecast).toHaveBeenCalledWith('ZN-B12')
    expect(mockClassifyZone).toHaveBeenCalledWith('ZN-B12')
    expect(screen.getByText('RESTRICTED')).toBeInTheDocument()
    expect(screen.getByText('78%')).toBeInTheDocument()
  })

  it('still renders zone detail when forecast/classification calls fail (they are individually caught)', async () => {
    mockGetZoneDetail.mockResolvedValue(detail)
    mockGetZoneHistory.mockResolvedValue({ readings: [] })
    mockGetZoneForecast.mockRejectedValue(new Error('no forecast'))
    mockClassifyZone.mockRejectedValue(new Error('no classification'))

    render(<ZoneDetailPanel zoneId="ZN-B12" onClose={vi.fn()} />)
    expect(await screen.findByText('Server Room B')).toBeInTheDocument()
  })

  it('shows an error message instead of crashing when the detail fetch fails', async () => {
    mockGetZoneDetail.mockRejectedValue({ message: 'zone not found' })
    mockGetZoneHistory.mockResolvedValue({ readings: [] })
    mockGetZoneForecast.mockResolvedValue(null)
    mockClassifyZone.mockResolvedValue(null)

    render(<ZoneDetailPanel zoneId="ZN-BAD" onClose={vi.fn()} />)
    expect(await screen.findByText('zone not found')).toBeInTheDocument()
  })

  it('calls onClose when the close button is clicked', async () => {
    mockGetZoneDetail.mockResolvedValue(detail)
    mockGetZoneHistory.mockResolvedValue({ readings: [] })
    mockGetZoneForecast.mockResolvedValue(null)
    mockClassifyZone.mockResolvedValue(null)
    const onClose = vi.fn()

    render(<ZoneDetailPanel zoneId="ZN-B12" onClose={onClose} />)
    await screen.findByText('Server Room B')
    fireEvent.click(screen.getAllByRole('button')[0])
    expect(onClose).toHaveBeenCalled()
  })
})

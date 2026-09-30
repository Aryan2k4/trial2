import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import CommandPalette from './CommandPalette'

const mockNavigate = vi.fn()
const mockSearch = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})
vi.mock('../../services/costService', () => ({ facilityService: { search: (...args) => mockSearch(...args) } }))

function renderPalette(open = true) {
  const onClose = vi.fn()
  render(<MemoryRouter><CommandPalette open={open} onClose={onClose} /></MemoryRouter>)
  return { onClose }
}

describe('CommandPalette', () => {
  beforeEach(() => {
    mockNavigate.mockReset()
    mockSearch.mockReset()
  })

  it('renders nothing when closed', () => {
    const { container } = render(<MemoryRouter><CommandPalette open={false} onClose={vi.fn()} /></MemoryRouter>)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows quick-jump nav shortcuts when the query is empty', () => {
    renderPalette()
    expect(screen.getByText('Energy flow')).toBeInTheDocument()
    expect(screen.getByText('Asset care')).toBeInTheDocument()
  })

  it('navigates and closes when a nav shortcut is clicked', () => {
    const { onClose } = renderPalette()
    fireEvent.click(screen.getByText('Energy flow'))
    expect(mockNavigate).toHaveBeenCalledWith('/energy')
    expect(onClose).toHaveBeenCalled()
  })

  it('queries facilityService.search when typing and renders results', async () => {
    mockSearch.mockResolvedValueOnce({
      results: [{ domain: 'maintenance', type: 'asset', id: 'AST-001', label: 'HVAC-001', subtitle: 'HVAC Chiller', route: '/maintenance' }],
    })
    renderPalette()
    fireEvent.change(screen.getByPlaceholderText(/search assets/i), { target: { value: 'HVAC' } })

    await waitFor(() => expect(mockSearch).toHaveBeenCalledWith('HVAC'), { timeout: 500 })
    expect(await screen.findByText('HVAC-001')).toBeInTheDocument()
  })

  it('shows a no-matches message when search returns empty', async () => {
    mockSearch.mockResolvedValueOnce({ results: [] })
    renderPalette()
    fireEvent.change(screen.getByPlaceholderText(/search assets/i), { target: { value: 'zzzznotfound' } })

    expect(await screen.findByText(/no matches for/i)).toBeInTheDocument()
  })
})

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataDriftBanner from './DataDriftBanner'

describe('DataDriftBanner', () => {
  it('renders nothing when drift is not detected', () => {
    const { container } = render(<DataDriftBanner drift={{ drift_detected: false }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when drift is undefined', () => {
    const { container } = render(<DataDriftBanner drift={undefined} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a warning with the drift level and subject when drift is detected', () => {
    render(<DataDriftBanner drift={{ drift_detected: true, level: 'high' }} subject="the uploaded CSV" />)
    expect(screen.getByText('Different dataset detected')).toBeInTheDocument()
    expect(screen.getByText(/the uploaded CSV/)).toBeInTheDocument()
    expect(screen.getByText(/high drift/)).toBeInTheDocument()
  })

  it('falls back to the default subject text when none is given', () => {
    render(<DataDriftBanner drift={{ drift_detected: true, level: 'moderate' }} />)
    expect(screen.getByText(/this dataset doesn't match/)).toBeInTheDocument()
  })
})

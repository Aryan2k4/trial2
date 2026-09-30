import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import DataManagerModal from './DataManagerModal'

const mockShow = vi.fn()
vi.mock('../../context/ToastContext', () => ({ useToast: () => ({ show: mockShow }) }))

const fields = [
  { key: 'vendor_name', label: 'Vendor', type: 'text', required: true },
  { key: 'amount_inr', label: 'Amount', type: 'number', required: true },
]
const columns = [{ key: 'vendor_name', label: 'Vendor' }, { key: 'amount_inr', label: 'Amount' }]

function makeProps(overrides = {}) {
  return {
    open: true,
    onClose: vi.fn(),
    title: 'Manage Cost Dataset',
    subtitle: 'Records',
    fields,
    columns,
    fetchRecords: vi.fn().mockResolvedValue({ records: [{ id: 1, vendor_name: 'Acme', amount_inr: 500 }] }),
    addRecord: vi.fn().mockResolvedValue({ id: 2 }),
    deleteRecord: vi.fn().mockResolvedValue({}),
    clearAllRecords: vi.fn().mockResolvedValue({}),
    onChanged: vi.fn(),
    ...overrides,
  }
}

describe('DataManagerModal', () => {
  beforeEach(() => mockShow.mockReset())

  it('loads and displays existing records on open', async () => {
    const props = makeProps()
    render(<DataManagerModal {...props} />)
    expect(await screen.findByText(/Acme/)).toBeInTheDocument()
    expect(props.fetchRecords).toHaveBeenCalled()
  })

  it('submits a new record via addRecord, shows a success toast, and refreshes', async () => {
    const props = makeProps()
    render(<DataManagerModal {...props} />)
    await screen.findByText(/Acme/)

    fireEvent.change(screen.getByLabelText(/Vendor/i), { target: { value: 'New Vendor' } })
    fireEvent.change(screen.getByLabelText(/Amount/i), { target: { value: '1234' } })
    fireEvent.click(screen.getByRole('button', { name: /add record/i }))

    await waitFor(() => expect(props.addRecord).toHaveBeenCalledWith(
      expect.objectContaining({ vendor_name: 'New Vendor', amount_inr: 1234 })
    ))
    await waitFor(() => expect(mockShow).toHaveBeenCalledWith(expect.stringContaining('added'), 'success'))
  })

  it('shows an error toast when addRecord fails, without crashing', async () => {
    const props = makeProps({ addRecord: vi.fn().mockRejectedValue({ message: 'Server error' }) })
    render(<DataManagerModal {...props} />)
    await screen.findByText(/Acme/)

    fireEvent.change(screen.getByLabelText(/Vendor/i), { target: { value: 'X' } })
    fireEvent.change(screen.getByLabelText(/Amount/i), { target: { value: '1' } })
    fireEvent.click(screen.getByRole('button', { name: /add record/i }))

    await waitFor(() => expect(mockShow).toHaveBeenCalledWith('Server error', 'error'))
  })

  it('deletes a record and calls onChanged', async () => {
    const props = makeProps()
    render(<DataManagerModal {...props} />)
    await screen.findByText(/Acme/)

    const deleteButtons = screen.getAllByTitle('Delete this record')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => expect(props.deleteRecord).toHaveBeenCalledWith(1))
    await waitFor(() => expect(props.onChanged).toHaveBeenCalled())
  })

  it('renders nothing when closed', () => {
    const props = makeProps({ open: false })
    const { container } = render(<DataManagerModal {...props} />)
    expect(container).toBeEmptyDOMElement()
  })
})

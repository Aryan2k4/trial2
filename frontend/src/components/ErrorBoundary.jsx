import { Component } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

/**
 * Was missing from this app entirely — meaning a render-time error in ANY
 * component (a malformed API response after uploading an edge-case CSV, a
 * chart library choking on unusual data shape, anything) crashed React's
 * whole tree with no user-facing message: a blank white screen, which is
 * exactly the "blank screen on CSV upload" symptom reported. This doesn't
 * fix whichever specific component might throw — it makes ANY such crash
 * show a recoverable message instead of nothing, and (critically) prints
 * the real error to the browser console so the actual broken component
 * can be identified from a bug report going forward.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('FacilityOS crashed:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    // A full reload (not just clearing local state) since whatever data
    // caused the crash is likely still in memory/context otherwise.
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="min-h-screen bg-[#0d0f13] flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center">
          <div className="grid h-12 w-12 place-items-center rounded-full bg-rose-500/10 border border-rose-500/30 mx-auto mb-4">
            <AlertTriangle size={22} className="text-rose-400" />
          </div>
          <h1 className="font-display text-lg font-semibold text-white mb-2">Something went wrong</h1>
          <p className="font-body text-sm text-slate-400 mb-1 leading-relaxed">
            A part of the dashboard hit an unexpected error and couldn't render.
          </p>
          {this.state.error?.message && (
            <p className="font-mono text-[11px] text-slate-600 mb-5 break-words">{this.state.error.message}</p>
          )}
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-[#0d0f13] font-display text-sm font-semibold px-5 py-2.5 transition"
          >
            <RefreshCw size={14} />
            Reload
          </button>
        </div>
      </div>
    )
  }
}

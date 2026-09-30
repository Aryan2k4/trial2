import { useCallback, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale, Play } from 'lucide-react'
import { facilityService } from '../../services/costService'

const AGENT_LABEL = { cost: 'Cost Agent', maintenance: 'Maintenance Agent', mediator: 'Mediator' }
const AGENT_COLOR = {
  cost: 'border-amber-400/50 text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10',
  maintenance: 'border-teal-400/50 text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-500/10',
  mediator: 'border-violet-400/50 text-violet-700 dark:text-violet-400 bg-violet-50 dark:bg-violet-500/10',
}

/**
 * Runs and displays a multi-agent negotiation: the Cost Agent and
 * Maintenance Agent stating their real, data-grounded positions on the
 * "Repairs & Maintenance" budget category, followed by a mediator's
 * concrete resolution — genuine conflict resolution, not two opinions
 * shown side by side. Honestly reports "no conflict right now" when the
 * underlying numbers don't actually clash.
 */
export default function NegotiationPanel({ buildingId }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = useCallback(async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await facilityService.getNegotiation(buildingId)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [buildingId])

  return (
    <div className="surface-card p-5 sm:p-6">
      <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
        <h3 className="font-display text-base font-medium text-ink dark:text-slate-200 tracking-wide flex items-center gap-2">
          <Scale size={16} className="text-violet-500" /> Cost vs. Maintenance Negotiation
        </h3>
        <button
          onClick={run}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 font-mono text-[10px] tracking-wide text-white bg-violet-600 hover:bg-violet-700 disabled:opacity-50 transition-colors"
        >
          <Play size={10} fill="currentColor" /> {loading ? 'CHECKING…' : 'CHECK FOR CONFLICT'}
        </button>
      </div>
      <p className="text-[11px] text-slate-500 mb-4 font-body">
        Only runs a real negotiation when the Repairs &amp; Maintenance budget is actually over/at-risk AND a real asset
        is Critical or Warning — otherwise it says so plainly.
      </p>

      {error && <p className="text-xs text-red-500 dark:text-red-400 font-mono">{error}</p>}

      {result && !result.has_conflict && (
        <p className="text-xs text-slate-500 dark:text-slate-400 font-body py-4 text-center">{result.reason}</p>
      )}

      <AnimatePresence>
        {result?.has_conflict && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-3">
            <div className="rounded-xl bg-slate-50 dark:bg-slate-800/50 p-3 text-[11px] font-mono text-slate-500 dark:text-slate-400">
              {result.category.category}: ₹{result.category.spent_inr.toLocaleString('en-IN')} / ₹{result.category.budget_inr.toLocaleString('en-IN')}
              {' '}({result.category.pct_of_budget}% — {result.category.status}) · {result.at_risk_assets.length} at-risk asset(s)
            </div>
            {result.rounds.map((round, i) => (
              <div key={i} className={`rounded-xl border p-3 ${AGENT_COLOR[round.agent]}`}>
                <span className="font-mono text-[9px] tracking-widest uppercase">{AGENT_LABEL[round.agent]}</span>
                <p className="text-xs mt-1.5 leading-relaxed font-body text-slate-700 dark:text-slate-200">{round.position}</p>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {!result && !loading && !error && (
        <div className="text-xs text-slate-400 dark:text-slate-600 font-mono py-6 text-center">no check run yet</div>
      )}
    </div>
  )
}

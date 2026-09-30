import { useState, useRef, useEffect } from 'react'
import { Building2, ChevronDown, Check } from 'lucide-react'
import { useBuilding } from '../../context/BuildingContext'

/**
 * Lets the operator switch which building every dashboard, agent, and
 * ML model call is scoped to. Only lists buildings that actually have
 * data (see GET /api/facility/buildings) so there's never a dead entry.
 */
export default function BuildingSwitcher() {
  const { buildingId, setBuildingId, buildings, loading } = useBuilding()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  if (loading || buildings.length <= 1) {
    // Nothing to switch between yet (or still loading) — show a plain,
    // non-interactive label instead of a dropdown with one dead option.
    return (
      <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 font-mono text-[10px] text-slate-400 md:flex dark:border-white/[0.08] dark:bg-white/[0.04]">
        <Building2 size={12} /> {buildingId}
      </div>
    )
  }

  return (
    <div className="relative hidden md:block" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 font-mono text-[10px] text-slate-500 shadow-sm transition hover:border-slate-300 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-slate-300 dark:hover:border-white/20"
      >
        <Building2 size={12} /> {buildingId} <ChevronDown size={11} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute left-0 top-[calc(100%+6px)] z-40 w-56 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl dark:border-white/10 dark:bg-[#15161a] dark:shadow-black/40">
          <div className="px-3 py-2 font-mono text-[9px] tracking-widest text-slate-400 dark:text-slate-500">SWITCH BUILDING</div>
          {buildings.map((b) => (
            <button
              key={b.building_id}
              onClick={() => { setBuildingId(b.building_id); setOpen(false) }}
              className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left font-mono text-[11px] transition ${b.building_id === buildingId ? 'text-teal-600 dark:text-teal-400 bg-slate-50 dark:bg-white/[0.05]' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/[0.05]'}`}
            >
              <span>{b.building_id}{b.is_default ? ' (default)' : ''}</span>
              {b.building_id === buildingId && <Check size={12} />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

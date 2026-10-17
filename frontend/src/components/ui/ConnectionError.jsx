import { AlertCircle, RefreshCw } from 'lucide-react'

export default function ConnectionError({ onRetry, retrying }) {
  return <section role="alert" className="mx-auto my-12 max-w-lg px-6 text-center">
    <AlertCircle className="mx-auto text-amber-500" size={32} />
    <h1 className="mt-4 text-xl font-semibold text-ink dark:text-white">Connection failed</h1>
    <p className="mt-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">We couldn’t load this dashboard. The server may be waking up or your connection may have changed. Try reconnecting in a moment.</p>
    <button onClick={onRetry} disabled={retrying} className="mx-auto mt-6 flex items-center gap-2 rounded-xl bg-teal-500 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-60"><RefreshCw size={16} className={retrying ? 'animate-spin' : ''} />{retrying ? 'Reconnecting…' : 'Try again'}</button>
  </section>
}

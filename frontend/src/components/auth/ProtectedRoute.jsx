import { Navigate, useLocation } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { status, retry, logout } = useAuth()
  const location = useLocation()

  if (status === 'checking') {
    return (
      <div className="min-h-screen bg-[#0d0f13] flex items-center justify-center">
        <div className="text-center" role="status"><Loader2 size={22} className="mx-auto animate-spin text-teal-400" /><p className="mt-4 text-sm text-slate-300">Connecting to your workspace…</p><p className="mt-2 text-xs text-slate-400">Free hosting may take a minute to wake up.</p></div>
      </div>
    )
  }

  if (status === 'unavailable') {
    return <div className="min-h-screen bg-[#0d0f13] flex items-center justify-center p-6"><div className="max-w-md text-center" role="alert"><h1 className="text-xl font-semibold text-white">Connection interrupted</h1><p className="mt-3 text-sm text-slate-300">Your session is saved. The server may be waking up or temporarily unavailable.</p><button onClick={retry} className="mt-6 rounded-xl bg-teal-400 px-5 py-3 font-semibold text-slate-950">Try again</button><button onClick={logout} className="ml-4 text-sm text-slate-300">Sign out</button></div></div>
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

import { Activity, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'

export default function StatusRing({ status, loading, data }) {
  let ringColor = 'border-emerald-500 shadow-emerald-500/20'
  let glowColor = 'bg-emerald-500/10'
  let Icon = Activity
  let statusText = 'POLICY ACTIVE'

  if (status === 'PENDING') {
    ringColor = 'border-amber-500 shadow-amber-500/40 animate-pulse'
    glowColor = 'bg-amber-500/20'; Icon = AlertTriangle; statusText = 'REVIEW REQUIRED'
  } else if (status === 'SUCCESS') {
    ringColor = 'border-amber-400 shadow-amber-400/50'
    glowColor = 'bg-amber-400/20'; Icon = CheckCircle; statusText = 'PAYOUT INITIATED'
  } else if (status === 'DENIED') {
    ringColor = 'border-rose-500 shadow-rose-500/40'
    glowColor = 'bg-rose-500/20'; Icon = AlertTriangle; statusText = 'CLAIM DENIED'
  } else if (status === 'CAPPED') {
    ringColor = 'border-orange-500 shadow-orange-500/40'
    glowColor = 'bg-orange-500/20'; Icon = AlertTriangle; statusText = 'DAILY CAP REACHED'
  } else if (status === 'ERROR') {
    ringColor = 'border-rose-800 shadow-rose-800/40'
    glowColor = 'bg-rose-800/20'; Icon = AlertTriangle; statusText = 'CONNECTION ERROR'
  }

  return (
    <div className="relative flex flex-col items-center justify-center py-4">
      <div className={`absolute w-56 h-56 rounded-full blur-3xl transition-colors duration-700 ${glowColor}`} />
      <div className={`relative w-48 h-48 rounded-full border-[6px] shadow-2xl flex flex-col items-center justify-center bg-neutral-900/40 backdrop-blur-md transition-all duration-700 ${ringColor}`}>
        {loading ? (
          <div className="flex flex-col items-center text-white">
            <Loader2 className="w-10 h-10 mb-2 animate-spin text-emerald-300" />
            <span className="text-xs tracking-widest font-semibold uppercase">Analyzing...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center">
            <Icon className={`w-10 h-10 mb-2 transition-colors ${
              status === 'SUCCESS' ? 'text-amber-400' : status === 'ACTIVE' ? 'text-emerald-400' :
              status === 'DENIED' ? 'text-rose-400' : 'text-amber-500'
            }`} />
            <h2 className="text-xs tracking-widest font-bold text-white uppercase">{statusText}</h2>
            {data?.payout && (
              <div className="mt-2 text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-amber-200 to-amber-500">
                ₹{data.payout}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

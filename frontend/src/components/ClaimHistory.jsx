import { CheckCircle, AlertTriangle, XCircle, Clock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const statusConfig = {
  SUCCESS: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', label: 'Approved' },
  PENDING: { icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', label: 'In Review' },
  DENIED: { icon: XCircle, color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', label: 'Denied' },
}

export default function ClaimHistory({ claims }) {
  if (!claims || claims.length === 0) return null

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">Claim History</span>
        <span className="text-xs text-neutral-500 font-mono">{claims.length} claim{claims.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="space-y-2 max-h-[240px] overflow-y-auto pr-1 scrollbar-thin">
        <AnimatePresence>
          {[...claims].reverse().map((claim, i) => {
            const cfg = statusConfig[claim.status] || statusConfig.DENIED
            const Icon = cfg.icon
            const time = new Date(claim.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
            return (
              <motion.div key={claim.id}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className={`flex items-center gap-3 p-3 rounded-xl border ${cfg.border} ${cfg.bg}`}>
                <Icon className={`w-5 h-5 shrink-0 ${cfg.color}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white truncate">{claim.reason}</span>
                    {claim.amount > 0 && <span className="text-sm font-bold text-white ml-2">₹{claim.amount}</span>}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-neutral-400 font-mono">{claim.id}</span>
                    <span className="text-[10px] text-neutral-500">•</span>
                    <span className="text-[10px] text-neutral-400">{time}</span>
                    <span className="text-[10px] text-neutral-500">•</span>
                    <span className={`text-[10px] font-semibold ${cfg.color}`}>{cfg.label}</span>
                    <span className="text-[10px] text-neutral-500">•</span>
                    <span className="text-[10px] text-neutral-400 font-mono">TCS {claim.tcs_score?.toFixed(2)}</span>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}

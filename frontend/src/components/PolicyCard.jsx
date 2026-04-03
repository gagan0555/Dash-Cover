import { Shield, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function PolicyCard({ enrollmentData, formData }) {
  const [expanded, setExpanded] = useState(false)

  if (!enrollmentData) return null

  const items = [
    { label: 'Coverage Tier', value: enrollmentData.coverage_tier || 'Standard' },
    { label: 'Weekly Premium', value: `₹${enrollmentData.weekly_premium}` },
    { label: 'Daily Payout Cap', value: `₹${enrollmentData.tier_cap || 600}` },
    { label: 'Zone', value: enrollmentData.zone_id },
    { label: 'Risk Multiplier', value: `${enrollmentData.zone_risk_multiplier || 1.5}x` },
    { label: 'Worker ID', value: enrollmentData.worker_id },
  ]

  return (
    <div className="w-full bg-neutral-900 border border-white/10 rounded-xl overflow-hidden transition-all">
      <button onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-all">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">Policy Details</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-emerald-400">₹{enrollmentData.weekly_premium}/wk</span>
          {expanded ? <ChevronUp className="w-4 h-4 text-neutral-500" /> : <ChevronDown className="w-4 h-4 text-neutral-500" />}
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-3 border-t border-white/5 pt-3 grid grid-cols-2 gap-2">
          {items.map(({ label, value }) => (
            <div key={label} className="flex flex-col">
              <span className="text-[10px] text-neutral-500 uppercase tracking-wider">{label}</span>
              <span className="text-sm font-semibold text-white">{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

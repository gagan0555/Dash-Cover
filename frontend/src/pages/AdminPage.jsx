import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { ShieldCheck, ArrowLeft, Users, FileText, Banknote, TrendingDown, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { API_BASE_URL } from '../config'
import ZoneRiskMap from '../components/ZoneRiskMap'

export default function AdminPage() {
  const [stats, setStats] = useState(null)
  const [workers, setWorkers] = useState([])
  const [claims, setClaims] = useState([])
  const [zones, setZones] = useState({ zones: [], storm_active: false })
  const [loading, setLoading] = useState(true)

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [s, w, c, z] = await Promise.all([
        axios.get(`${API_BASE_URL}/admin/stats`),
        axios.get(`${API_BASE_URL}/admin/workers`),
        axios.get(`${API_BASE_URL}/admin/claims`),
        axios.get(`${API_BASE_URL}/admin/zones`),
      ])
      setStats(s.data); setWorkers(w.data.workers); setClaims(c.data.claims); setZones(z.data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [])

  const toggleStorm = async (active) => {
    await axios.post(`${API_BASE_URL}/demo/set-storm?active=${active}`)
    await fetchAll()
  }

  const toggleCurfew = async (active) => {
    await axios.post(`${API_BASE_URL}/demo/set-curfew?active=${active}`)
    await fetchAll()
  }

  const toggleStrike = async (active) => {
    await axios.post(`${API_BASE_URL}/demo/set-strike?active=${active}`)
    await fetchAll()
  }

  const statCards = stats ? [
    { label: 'Total Workers', value: stats.total_workers, icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Total Claims', value: stats.total_claims, icon: FileText, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Total Payouts', value: `₹${stats.total_payouts.toLocaleString()}`, icon: Banknote, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'Loss Ratio', value: stats.loss_ratio.toFixed(4), icon: TrendingDown,
      color: stats.loss_ratio < 0.7 ? 'text-emerald-400' : 'text-rose-400',
      bg: stats.loss_ratio < 0.7 ? 'bg-emerald-500/10' : 'bg-rose-500/10' },
  ] : []

  const statusBadge = (s) => {
    const m = { SUCCESS: 'bg-emerald-500/20 text-emerald-300', PENDING: 'bg-amber-500/20 text-amber-300', DENIED: 'bg-rose-500/20 text-rose-300' }
    return <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${m[s] || 'bg-neutral-700 text-neutral-300'}`}>{s}</span>
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 font-sans">
      {/* Header */}
      <header className="bg-neutral-900 border-b border-white/10 px-6 py-4 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-1.5 text-neutral-400 hover:text-white transition-all">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <ShieldCheck className="w-6 h-6 text-indigo-400" />
          <h1 className="text-lg font-bold text-white">Dash-Cover <span className="text-indigo-400 font-medium">Admin</span></h1>
        </div>
        <div className="flex items-center gap-3">
          {stats?.storm_active && (
            <span className="text-[10px] px-2 py-1 rounded-full bg-rose-500/20 text-rose-300 font-bold uppercase animate-pulse">⚡ Storm Active</span>
          )}
          {stats?.curfew_active && (
            <span className="text-[10px] px-2 py-1 rounded-full bg-rose-600/20 text-rose-300 font-bold uppercase animate-pulse">🚫 Curfew Active</span>
          )}
          {stats?.strike_active && (
            <span className="text-[10px] px-2 py-1 rounded-full bg-orange-600/20 text-orange-200 font-bold uppercase animate-pulse">📢 Strike Active</span>
          )}
          <button onClick={fetchAll} className="p-2 hover:bg-white/10 rounded-lg transition-all">
            <RefreshCw className={`w-4 h-4 text-neutral-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Alert Controls */}
        <div className="flex flex-wrap gap-4 bg-neutral-900/50 p-4 rounded-2xl border border-white/10">
          <div className="space-y-2">
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest px-1">Weather / Storm</p>
            <div className="flex gap-2">
              <button onClick={() => toggleStorm(true)}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${stats?.storm_active ? 'bg-rose-600 text-white shadow-[0_0_15px_rgba(225,29,72,0.4)]' : 'bg-neutral-800 text-neutral-400 border border-neutral-700'}`}>
                Activate Storm
              </button>
              <button onClick={() => toggleStorm(false)}
                className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 border border-neutral-600 text-white text-xs font-medium rounded-lg transition-all">
                Clear
              </button>
            </div>
          </div>

          <div className="w-px h-12 bg-white/5 self-end mb-1" />

          <div className="space-y-2">
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest px-1">Curfew Alert</p>
            <div className="flex gap-2">
              <button onClick={() => toggleCurfew(true)}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${stats?.curfew_active ? 'bg-rose-600 text-white shadow-[0_0_15px_rgba(225,29,72,0.4)]' : 'bg-neutral-800 text-neutral-400 border border-neutral-700'}`}>
                Trigger Curfew
              </button>
              <button onClick={() => toggleCurfew(false)}
                className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 border border-neutral-600 text-white text-xs font-medium rounded-lg transition-all">
                Clear
              </button>
            </div>
          </div>

          <div className="w-px h-12 bg-white/5 self-end mb-1" />

          <div className="space-y-2">
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest px-1">Market Strike</p>
            <div className="flex gap-2">
              <button onClick={() => toggleStrike(true)}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${stats?.strike_active ? 'bg-orange-600 text-white shadow-[0_0_15px_rgba(234,88,12,0.4)]' : 'bg-neutral-800 text-neutral-400 border border-neutral-700'}`}>
                Trigger Strike
              </button>
              <button onClick={() => toggleStrike(false)}
                className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 border border-neutral-600 text-white text-xs font-medium rounded-lg transition-all">
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Stat Cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {statCards.map(({ label, value, icon: Icon, color, bg }) => (
              <motion.div key={label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="bg-neutral-900 border border-white/10 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg ${bg}`}><Icon className={`w-4 h-4 ${color}`} /></div>
                  <span className="text-xs text-neutral-400 font-medium uppercase tracking-wider">{label}</span>
                </div>
                <p className="text-2xl font-bold text-white">{value}</p>
              </motion.div>
            ))}
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Worker Table */}
          <div className="bg-neutral-900 border border-white/10 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-white/5 flex justify-between items-center">
              <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">Enrolled Workers</span>
              <span className="text-xs text-neutral-500 font-mono">{workers.length}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-neutral-500 uppercase tracking-wider border-b border-white/5">
                    <th className="text-left px-4 py-2">Worker</th>
                    <th className="text-left px-4 py-2">Zone</th>
                    <th className="text-center px-4 py-2">Claims</th>
                    <th className="text-right px-4 py-2">Paid</th>
                    <th className="text-right px-4 py-2">TCS</th>
                  </tr>
                </thead>
                <tbody>
                  {workers.map(w => (
                    <tr key={w.worker_id} className="border-b border-white/5 hover:bg-white/5 transition-all">
                      <td className="px-4 py-2.5">
                        <div className="font-semibold text-white">{w.name}</div>
                        <div className="text-[10px] text-neutral-500 font-mono">{w.worker_id} · {w.behavior_profile}</div>
                      </td>
                      <td className="px-4 py-2.5 text-neutral-400 text-xs">{w.zone_id}</td>
                      <td className="px-4 py-2.5 text-center font-mono text-white">{w.total_claims}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-emerald-400">₹{w.total_paid}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-white">{w.last_tcs?.toFixed(2) || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Zone Risk Map */}
          <div className="bg-neutral-900 border border-white/10 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-white/5">
              <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">Zone Risk Map — Pan India</span>
            </div>
            <div className="h-[320px]">
              <ZoneRiskMap zones={zones.zones} stormActive={zones.storm_active} />
            </div>
          </div>
        </div>

        {/* Claims Feed */}
        <div className="bg-neutral-900 border border-white/10 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-white/5 flex justify-between items-center">
            <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">All Claims</span>
            <span className="text-xs text-neutral-500 font-mono">{claims.length} total</span>
          </div>
          {claims.length === 0 ? (
            <div className="p-8 text-center text-neutral-500 text-sm">No claims yet. Simulate a storm to generate claim events.</div>
          ) : (
            <div className="divide-y divide-white/5 max-h-[300px] overflow-y-auto">
              {claims.map(c => (
                <div key={c.id} className="px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-all">
                  <div className="flex items-center gap-3">
                    {statusBadge(c.status)}
                    <div>
                      <p className="text-sm text-white font-medium">{c.reason}</p>
                      <p className="text-[10px] text-neutral-500 font-mono">{c.id} · {c.worker_id} · {new Date(c.timestamp).toLocaleTimeString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    {c.amount > 0 && <p className="text-sm font-bold text-white">₹{c.amount}</p>}
                    <p className="text-[10px] text-neutral-400 font-mono">TCS {c.tcs_score?.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

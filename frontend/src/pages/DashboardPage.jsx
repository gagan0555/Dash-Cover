import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { ShieldCheck, CloudRain, AlertTriangle, Loader2, LayoutDashboard } from 'lucide-react'
import { Link } from 'react-router-dom'
import { API_BASE_URL } from '../config'
import StatusRing from '../components/StatusRing'
import WeatherWidget from '../components/WeatherWidget'
import PolicyCard from '../components/PolicyCard'
import ClaimHistory from '../components/ClaimHistory'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
}

export default function DashboardPage({ workerId, enrollmentData, formData }) {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState({ status: 'ACTIVE' })
  const [claims, setClaims] = useState([])
  const [weather, setWeather] = useState(null)

  const fetchWeather = async () => {
    try { const r = await axios.get(`${API_BASE_URL}/weather/current`); setWeather(r.data) } catch {}
  }
  const fetchClaims = async () => {
    try { const r = await axios.get(`${API_BASE_URL}/claims/${workerId}`); setClaims(r.data.claims) } catch {}
  }

  useEffect(() => { fetchWeather(); fetchClaims() }, [])

  const simulateStorm = async (wid) => {
    setLoading(true)
    try {
      await axios.post(`${API_BASE_URL}/demo/set-storm?active=true`)
      const r = await axios.get(`${API_BASE_URL}/check-payout/${wid}`)
      setData(r.data)
      await fetchClaims()
      await fetchWeather()
    } catch (err) {
      setData({ status: 'ERROR', message: 'Failed to connect to Oracle.' })
    } finally { setLoading(false) }
  }

  const resetEnv = async () => {
    setLoading(true)
    try {
      await axios.post(`${API_BASE_URL}/demo/set-storm?active=false`)
      setData({ status: 'ACTIVE', message: 'Weather cleared. All systems normal.' })
      setClaims([])
      await fetchWeather()
    } catch {} finally { setLoading(false) }
  }

  const status = data?.status || 'ACTIVE'

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 flex flex-col font-sans relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div variants={pageVariants} initial="initial" animate="animate"
        className="flex-1 flex flex-col relative z-10 w-full max-w-md mx-auto">

        {/* Header */}
        <header className="p-4 flex flex-col gap-3 w-full bg-neutral-900 border-b border-white/10 shadow-lg">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              <h1 className="text-xl font-bold tracking-tight text-white">GigShield</h1>
            </div>
            <div className="flex items-center gap-2 bg-neutral-800 rounded-full px-3 py-1.5 border border-white/15">
              <span className={`w-2 h-2 rounded-full ${status === 'ACTIVE' ? 'bg-emerald-400' : status === 'SUCCESS' ? 'bg-amber-400' : 'bg-rose-400'} animate-pulse`} />
              <span className="text-xs font-mono font-semibold text-white">
                TCS: {data?.tcs_score != null ? data.tcs_score.toFixed(2) : '—'}
              </span>
            </div>
          </div>
          <div className="flex justify-between items-end border-t border-white/5 pt-3 mt-1">
            <div>
              <p className="text-xs text-neutral-400 font-medium tracking-wide">Welcome back,</p>
              <p className="text-sm font-bold text-white">{formData.name || 'Ravi'}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-neutral-400 font-medium tracking-wide">Linked UPI</p>
              <p className="text-sm font-mono text-emerald-300">{formData.upi || 'ravi@okaxis'}</p>
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto p-4 space-y-4">
          <WeatherWidget weather={weather} />
          <StatusRing status={status} loading={loading} data={data} />
          <PolicyCard enrollmentData={enrollmentData} formData={formData} />

          {/* Telemetry */}
          {(data?.reason || data?.message || status !== 'ACTIVE') && (
            <div className="w-full bg-neutral-900 overflow-hidden border border-white/10 rounded-2xl shadow-xl">
              <div className="bg-neutral-800/50 px-4 py-2 border-b border-white/5 flex justify-between items-center">
                <span className="text-xs uppercase tracking-wider text-neutral-300 font-bold">Live Telemetry</span>
                <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-bold tracking-wider ${
                  status === 'SUCCESS' ? 'bg-amber-400/20 text-amber-300' :
                  status === 'DENIED' ? 'bg-rose-500/20 text-rose-300' :
                  status === 'CAPPED' ? 'bg-orange-500/20 text-orange-300' :
                  status === 'ERROR' ? 'bg-rose-900/50 text-rose-200' : 'bg-emerald-500/20 text-emerald-300'
                }`}>{status}</span>
              </div>
              <div className="p-4">
                <p className="text-sm text-white leading-relaxed font-medium">
                  {data?.reason || data?.message || 'Policy standing by.'}
                </p>
                {data?.tcs_breakdown && (
                  <div className="pt-3 mt-3 border-t border-white/10 flex justify-between text-xs font-mono text-neutral-400">
                    <span>LOC: <span className="text-white">{data.tcs_breakdown.location_match.score}</span></span>
                    <span>BEH: <span className="text-white">{data.tcs_breakdown.behavioral_check.score}</span></span>
                    <span>FRQ: <span className="text-white">{data.tcs_breakdown.frequency_cap.score}</span></span>
                  </div>
                )}
              </div>
            </div>
          )}

          <ClaimHistory claims={claims} />
        </main>

        {/* Controls */}
        <div className="p-4 w-full bg-neutral-950 border-t border-white/5 space-y-2.5">
          <button onClick={() => simulateStorm(workerId || 'W123')} disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-br from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-semibold py-3.5 px-6 rounded-xl shadow-lg transition-all active:scale-[0.98] disabled:opacity-50">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CloudRain className="w-5 h-5" />}
            <span>Simulate Storm ({workerId || 'W123'})</span>
          </button>
          <button onClick={() => simulateStorm('W456')} disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-white font-medium py-3 px-6 rounded-xl transition-all active:scale-[0.98] disabled:opacity-50">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>Simulate Fraud (W456)</span>
          </button>
          <div className="flex justify-between items-center pt-1">
            <button onClick={resetEnv} disabled={loading}
              className="text-neutral-500 hover:text-neutral-300 text-sm underline underline-offset-4 decoration-neutral-700 transition-all">
              Reset Environment
            </button>
            <Link to="/admin" className="flex items-center gap-1.5 text-sm text-indigo-400 hover:text-indigo-300 transition-all">
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Admin Panel</span>
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

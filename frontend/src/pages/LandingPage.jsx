import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, ArrowRight, LogIn, UserPlus, ShieldAlert, Eye, EyeOff } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import EnrollmentModal from '../components/EnrollmentModal'
import axios from 'axios'
import { API_BASE_URL } from '../config'

const fade = (x = 0, y = 0) => ({
  initial: { opacity: 0, x, y },
  animate: { opacity: 1, x: 0, y: 0, transition: { duration: 0.3 } },
  exit:    { opacity: 0, x: -x, y: -y, transition: { duration: 0.25 } },
})

const inputCls = (focus) =>
  `w-full bg-neutral-900 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-neutral-600 text-sm focus:outline-none ${focus} transition-all`

export default function LandingPage({ onEnrolled }) {
  const [tab, setTab] = useState('signup')
  const [showModal, setShowModal] = useState(false)
  const [workerId, setWorkerId] = useState('')
  const [showAdminForm, setShowAdminForm] = useState(false)
  const [adminUser, setAdminUser] = useState('')
  const [adminPass, setAdminPass] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')          // single shared error state
  const navigate = useNavigate()

  const switchTab = (t) => { setTab(t); setError(''); setShowAdminForm(false) }
const handleWorkerLogin = async (e) => {
  e.preventDefault()
  if (!workerId.trim()) return setError('Please enter your Worker ID.')
  try {
    const r = await axios.get(`${API_BASE_URL}/worker/${workerId.trim()}`)
    onEnrolled(r.data.worker_id, r.data, {
      name: r.data.name,
      upi: r.data.upi,
    })
  } catch {
    setError('Worker ID not found. Please sign up first.')
  }
}

  const handleAdminLogin = (e) => {
    e.preventDefault()
    if (adminUser === 'admin' && adminPass === 'admin123') navigate('/admin')
    else setError('Invalid credentials. Try admin / admin123')
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 flex flex-col font-sans relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div {...fade(0, 20)} className="flex-1 flex flex-col relative z-10 w-full max-w-md mx-auto">

        <header className="p-6 pt-12 flex justify-center">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-8 h-8 text-emerald-400" />
            <h1 className="text-3xl font-bold tracking-tight">Dash-Cover</h1>
          </div>
        </header>

        <main className="flex-1 flex flex-col justify-center px-6 pb-12">

          {/* Hero — changes per tab */}
          <AnimatePresence mode="wait">
            {tab === 'signup' ? (
              <motion.div key="hero-signup" {...fade(0, 10)} className="text-center space-y-3 mb-8">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wide">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  Instant Parametric Coverage
                </div>
                <h2 className="text-3xl font-extrabold leading-tight">
                  Don't let <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">bad weather</span> wash away your earnings.
                </h2>
                <p className="text-neutral-400 leading-relaxed">
                  Automatic payouts triggered by rain and unsafe air quality. No delays. Cash straight to your UPI.
                </p>
              </motion.div>
            ) : (
              <motion.div key="hero-login" {...fade(0, 10)} className="text-center mb-8">
                <h2 className="text-2xl font-bold">Welcome back</h2>
                <p className="text-neutral-400 text-sm mt-1">Sign in to check your coverage & claims.</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Tabs */}
          <div className="flex bg-neutral-900 border border-white/10 rounded-xl p-1 mb-6">
            <button onClick={() => switchTab('signup')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${tab === 'signup' ? 'bg-emerald-500 text-neutral-950 shadow' : 'text-neutral-400 hover:text-white'}`}>
              <UserPlus className="w-4 h-4" /> Sign Up
            </button>
            <button onClick={() => switchTab('login')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${tab === 'login' ? 'bg-white/10 text-white shadow' : 'text-neutral-400 hover:text-white'}`}>
              <LogIn className="w-4 h-4" /> Login
            </button>
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">

            {tab === 'signup' && (
              <motion.div key="signup" {...fade(-10)}>
                <button onClick={() => setShowModal(true)}
                  className="w-full group flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-4 px-6 rounded-2xl shadow-[0_0_40px_rgba(16,185,129,0.3)] hover:shadow-[0_0_60px_rgba(16,185,129,0.5)] transition-all active:scale-[0.98]">
                  Secure My Income Now
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
                <p className="text-xs text-neutral-500 mt-4 text-center font-medium uppercase tracking-wider">₹25 / week • Cancel anytime</p>
              </motion.div>
            )}

            {tab === 'login' && (
              <motion.div key="login" {...fade(10)} className="space-y-4">

                {/* Worker login */}
                <form onSubmit={handleWorkerLogin} className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-1.5">Worker ID</label>
                    <input type="text" placeholder="e.g. W123" value={workerId}
                      onChange={e => { setWorkerId(e.target.value); setError('') }}
                      className={inputCls('focus:border-emerald-500/50')} />
                  </div>
                  {error && !showAdminForm && <p className="text-xs text-rose-400 font-medium">{error}</p>}
                  <button type="submit"
                    className="w-full flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 border border-white/10 text-white font-semibold py-3.5 rounded-xl transition-all active:scale-[0.98]">
                    <LogIn className="w-4 h-4" /> Sign In as Worker
                  </button>
                </form>

                <div className="flex items-center gap-3">
                  <div className="flex-1 h-px bg-white/5" />
                  <span className="text-xs text-neutral-600">or</span>
                  <div className="flex-1 h-px bg-white/5" />
                </div>

                {/* Admin login */}
                {!showAdminForm ? (
                  <button onClick={() => { setShowAdminForm(true); setError('') }}
                    className="w-full flex items-center justify-center gap-2 bg-indigo-500/10 border border-indigo-500/20 hover:border-indigo-500/40 text-indigo-400 text-sm font-semibold py-3 rounded-xl transition-all">
                    <ShieldAlert className="w-4 h-4" /> Admin Login
                  </button>
                ) : (
                  <motion.form onSubmit={handleAdminLogin} {...fade(0, 6)}
                    className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-4 space-y-3">
                    <p className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldAlert className="w-3.5 h-3.5" /> Admin Access
                    </p>
                    <input type="text" placeholder="Username" value={adminUser}
                      onChange={e => { setAdminUser(e.target.value); setError('') }}
                      className={inputCls('focus:border-indigo-500/50')} />
                    <div className="relative">
                      <input type={showPass ? 'text' : 'password'} placeholder="Password" value={adminPass}
                        onChange={e => { setAdminPass(e.target.value); setError('') }}
                        className={inputCls('focus:border-indigo-500/50') + ' pr-10'} />
                      <button type="button" onClick={() => setShowPass(v => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors">
                        {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {error && showAdminForm && <p className="text-xs text-rose-400 font-medium">{error}</p>}
                    <div className="flex gap-2">
                      <button type="button" onClick={() => { setShowAdminForm(false); setError('') }}
                        className="flex-1 py-2.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 text-sm font-medium transition-all">
                        Cancel
                      </button>
                      <button type="submit"
                        className="flex-1 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold transition-all flex items-center justify-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5" /> Enter
                      </button>
                    </div>
                  </motion.form>
                )}
              </motion.div>
            )}

          </AnimatePresence>
        </main>
      </motion.div>

      <EnrollmentModal isOpen={showModal} onClose={() => setShowModal(false)} onEnrolled={onEnrolled} />
    </div>
  )
}

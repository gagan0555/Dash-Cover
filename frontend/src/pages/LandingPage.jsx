import { useState } from 'react'
import { motion } from 'framer-motion'
import { ShieldCheck, ArrowRight } from 'lucide-react'
import EnrollmentModal from '../components/EnrollmentModal'

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.4 } },
}

export default function LandingPage({ onEnrolled }) {
  const [showModal, setShowModal] = useState(false)

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 flex flex-col font-sans relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit"
        className="flex-1 flex flex-col relative z-10 w-full max-w-md mx-auto">
        <header className="p-6 pt-12 flex justify-center items-center">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-8 h-8 text-emerald-400" />
            <h1 className="text-3xl font-bold tracking-tight text-white">GigShield</h1>
          </div>
        </header>

        <main className="flex-1 flex flex-col justify-center px-6 pb-20">
          <div className="space-y-6 text-center">
            <div className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold tracking-wide uppercase mb-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-2" />
              Instant Parametric Coverage
            </div>
            <h2 className="text-4xl font-extrabold text-white leading-tight">
              Don't let <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">bad weather</span> wash away your earnings.
            </h2>
            <p className="text-neutral-400 text-lg leading-relaxed">
              Automatic payouts triggered by rain and unsafe air quality. No claims adjusters. No delays. Cash straight to your UPI.
            </p>
            <div className="pt-8">
              <button onClick={() => setShowModal(true)}
                className="w-full group flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-4 px-6 rounded-2xl shadow-[0_0_40px_rgba(16,185,129,0.3)] hover:shadow-[0_0_60px_rgba(16,185,129,0.5)] transition-all active:scale-[0.98]">
                <span>Secure My Income Now</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <p className="text-xs text-neutral-500 mt-4 font-medium uppercase tracking-wider">₹25 / week • Cancel anytime</p>
            </div>
          </div>
        </main>
      </motion.div>

      <EnrollmentModal isOpen={showModal} onClose={() => setShowModal(false)} onEnrolled={onEnrolled} />
    </div>
  )
}

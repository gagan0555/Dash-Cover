import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, User, Phone, Bike, Wallet, MapPin, Search, Loader2 } from 'lucide-react'
import axios from 'axios'
import { API_BASE_URL } from '../config'

export default function EnrollmentModal({ isOpen, onClose, onEnrolled }) {
  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    name: '', phone: '', vehicle: '', upi: '',
    coverage_tier: 'Standard',
  })
  
  // Geolocation Search State
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [selectedLocation, setSelectedLocation] = useState(null)
  
  const searchTimeoutRef = useRef(null)
  const isSelectedSearch = useRef(false) // Add a flag to skip searching when we programmatically set the query

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value })

  // Debounced Search
  useEffect(() => {
    if (searchQuery.length < 3) {
      setSearchResults([])
      setShowResults(false)
      return
    }

    // Skip the search if the user just clicked an item from the dropdown
    if (isSelectedSearch.current) {
      isSelectedSearch.current = false
      return
    }

    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)

    searchTimeoutRef.current = setTimeout(async () => {
      setIsSearching(true)
      try {
        const r = await axios.get(`${API_BASE_URL}/geocode?q=${encodeURIComponent(searchQuery)}`)
        // Filter out duplicates based on lat/lon
        const unique = r.data.results.filter((v, i, a) => a.findIndex(t => (t.lat === v.lat && t.lon === v.lon)) === i)
        setSearchResults(unique)
        setShowResults(true)
      } catch (err) {
        console.error("Geocoding failed", err)
      } finally {
        setIsSearching(false)
      }
    }, 500)

    return () => clearTimeout(searchTimeoutRef.current)
  }, [searchQuery])

  const handleSelectLocation = (loc) => {
    setSelectedLocation({
      ...loc,
      zone_id: `${loc.name.replace(/\s+/g, '')}-DynamicZone`
    })
    
    // Set the flag BEFORE setting search query so the useEffect skips the search
    isSelectedSearch.current = true
    setSearchQuery(`${loc.name}${loc.state ? `, ${loc.state}` : ''}`)
    
    setShowResults(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (step === 1) {
      if (!selectedLocation) {
        setError('Please search and select a valid operating area.')
        return
      }
      setError('')
      setStep(2)
      return
    }
    
    setError('')
    try {
      const payload = {
        name: formData.name,
        phone: formData.phone,
        vehicle: formData.vehicle,
        upi: formData.upi,
        coverage_tier: formData.coverage_tier,
        zone_id: selectedLocation.zone_id,
        lat: selectedLocation.lat,
        lon: selectedLocation.lon,
      }
      const r = await axios.post(`${API_BASE_URL}/enroll`, payload)
      onClose()
      setTimeout(() => onEnrolled(r.data.worker_id, r.data, { ...formData, operating_area: selectedLocation.name }), 400)
    } catch (err) {
      setError(err.response?.data?.detail || 'Enrollment failed. Is the backend running?')
    }
  }

  const inputCls = "w-full bg-neutral-950 border border-neutral-800 rounded-xl py-3 pl-10 pr-4 text-white placeholder-neutral-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 20 }}
            className="bg-neutral-900 border border-white/10 rounded-3xl p-6 w-full max-w-md shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 h-1 bg-emerald-500 transition-all duration-300" style={{ width: step === 1 ? '50%' : '100%' }} />
            <div className="mb-6 flex justify-between items-center">
              <h3 className="text-xl font-bold text-white">{step === 1 ? 'Worker Details' : 'Coverage Setup'}</h3>
              <span className="text-xs font-medium bg-neutral-800 px-2 py-1 rounded text-neutral-400">Step {step} of 2</span>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {step === 1 ? (
                <motion.div key="s1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-neutral-400 px-1">Full Name</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                      <input required type="text" name="name" value={formData.name} onChange={handleChange} placeholder="e.g. Ravi Kumar" className={inputCls} />
                    </div>
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-neutral-400 px-1">Mobile Number</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                      <input required type="tel" name="phone" value={formData.phone} onChange={handleChange} placeholder="+91 98765 43210" className={inputCls} />
                    </div>
                  </div>
                  
                  <div className="space-y-1.5 relative">
                    <label className="text-xs font-semibold text-neutral-400 px-1">Operating Area</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 z-10" />
                      <input 
                        required 
                        type="text" 
                        value={searchQuery} 
                        onChange={(e) => {
                          setSearchQuery(e.target.value)
                          if (selectedLocation && e.target.value !== selectedLocation.name) {
                            setSelectedLocation(null) // invalidate selection if they type again
                          }
                        }}
                        onFocus={() => { if(searchResults.length > 0) setShowResults(true) }}
                        placeholder="Search city, town, or pin code..." 
                        className={inputCls} 
                      />
                      {isSearching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500 animate-spin" />}
                    </div>
                    
                    {/* Autocomplete Dropdown */}
                    <AnimatePresence>
                      {showResults && searchResults.length > 0 && (
                        <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                          className="absolute z-20 w-full mt-1 bg-neutral-800 border border-neutral-700 rounded-xl shadow-xl overflow-hidden max-h-48 overflow-y-auto">
                          {searchResults.map((loc, idx) => (
                            <button key={idx} type="button" onClick={() => handleSelectLocation(loc)}
                              className="w-full text-left px-4 py-2.5 hover:bg-neutral-700 transition-colors border-b border-neutral-700/50 last:border-0">
                              <div className="text-sm font-medium text-white flex items-center gap-2">
                                <MapPin className="w-3 h-3 text-emerald-400" />
                                {loc.name}
                              </div>
                              <div className="text-[10px] text-neutral-400 pl-5">
                                {loc.state ? `${loc.state}, ` : ''}{loc.country} · Lat: {loc.lat.toFixed(2)}, Lon: {loc.lon.toFixed(2)}
                              </div>
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                    
                    {selectedLocation && (
                      <p className="text-[10px] text-emerald-500/80 px-1 flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" /> Area secured: {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
                      </p>
                    )}
                  </div>
                  
                  {error && <p className="text-rose-400 text-sm text-center bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">{error}</p>}
                  
                  <button type="submit" className={`w-full font-bold py-3.5 rounded-xl shadow-lg mt-2 transition-all ${selectedLocation ? 'bg-emerald-500 hover:bg-emerald-400 text-neutral-950' : 'bg-neutral-800 text-neutral-500 cursor-not-allowed'}`}>
                    Next Step
                  </button>
                </motion.div>
              ) : (
                <motion.div key="s2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-neutral-400 px-1">Coverage Tier</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button type="button" onClick={() => setFormData({...formData, coverage_tier: 'Basic'})}
                        className={`py-2 px-3 rounded-xl border text-sm text-left transition-all ${formData.coverage_tier === 'Basic' ? 'bg-emerald-500/20 border-emerald-500 text-white' : 'bg-neutral-950 border-neutral-800 text-neutral-400 hover:border-neutral-600'}`}>
                        <div className="font-bold">Basic</div>
                        <div className="text-[10px] opacity-80">₹300 Daily Cap</div>
                      </button>
                      <button type="button" onClick={() => setFormData({...formData, coverage_tier: 'Standard'})}
                        className={`py-2 px-3 rounded-xl border text-sm text-left transition-all ${formData.coverage_tier === 'Standard' ? 'bg-emerald-500/20 border-emerald-500 text-white' : 'bg-neutral-950 border-neutral-800 text-neutral-400 hover:border-neutral-600'}`}>
                        <div className="font-bold">Standard</div>
                        <div className="text-[10px] opacity-80">₹600 Daily Cap</div>
                      </button>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-neutral-400 px-1">Vehicle Registration</label>
                    <div className="relative">
                      <Bike className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                      <input required type="text" name="vehicle" value={formData.vehicle} onChange={handleChange} placeholder="e.g. MH 01 AB 1234" className={`${inputCls} uppercase`} />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-neutral-400 px-1">UPI ID for Payouts</label>
                    <div className="relative">
                      <Wallet className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                      <input required type="text" name="upi" value={formData.upi} onChange={handleChange} placeholder="username@upi" className={`${inputCls} text-emerald-400`} />
                    </div>
                  </div>
                  {error && <p className="text-rose-400 text-sm text-center bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">{error}</p>}
                  <div className="flex gap-3 mt-2">
                    <button type="button" onClick={() => setStep(1)} className="w-1/3 bg-neutral-800 hover:bg-neutral-700 text-white font-medium py-3.5 rounded-xl transition-all">Back</button>
                    <button type="submit" className="w-2/3 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold py-3.5 rounded-xl shadow-lg transition-all flex justify-center items-center gap-2">
                      <span>Activate Policy</span>
                      <ShieldCheck className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              )}
            </form>
            <button onClick={onClose} className="absolute top-4 right-4 text-neutral-500 hover:text-white p-1">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

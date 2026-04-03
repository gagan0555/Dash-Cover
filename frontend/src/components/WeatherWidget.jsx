import { CloudRain, Wind, AlertTriangle, CheckCircle } from 'lucide-react'

export default function WeatherWidget({ weather }) {
  if (!weather) return null

  const rainSafe = weather.rain_1h <= 10.0
  const aqiSafe = weather.aqi <= 400

  return (
    <div className={`w-full rounded-xl border px-4 py-3 flex items-center justify-between gap-3 transition-all duration-500 ${
      weather.trigger_fired
        ? 'bg-rose-950/40 border-rose-500/30'
        : 'bg-neutral-900/60 border-white/10'
    }`}>
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <CloudRain className={`w-4 h-4 ${rainSafe ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span className="font-mono text-white">{weather.rain_1h}<span className="text-neutral-500 text-xs">mm</span></span>
          {rainSafe
            ? <CheckCircle className="w-3 h-3 text-emerald-500" />
            : <AlertTriangle className="w-3 h-3 text-rose-400 animate-pulse" />
          }
        </div>
        <div className="w-px h-4 bg-white/10" />
        <div className="flex items-center gap-1.5">
          <Wind className={`w-4 h-4 ${aqiSafe ? 'text-emerald-400' : 'text-rose-400'}`} />
          <span className="font-mono text-white">{weather.aqi}<span className="text-neutral-500 text-xs"> AQI</span></span>
          {aqiSafe
            ? <CheckCircle className="w-3 h-3 text-emerald-500" />
            : <AlertTriangle className="w-3 h-3 text-rose-400 animate-pulse" />
          }
        </div>
      </div>
      {weather.storm_active && (
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold uppercase tracking-wider animate-pulse">
          ⚡ Storm
        </span>
      )}
    </div>
  )
}

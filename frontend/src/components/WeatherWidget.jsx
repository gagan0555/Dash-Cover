import { CloudRain, Wind, AlertTriangle, CheckCircle, Thermometer, Droplets, MapPin, Wifi, WifiOff } from 'lucide-react'

export default function WeatherWidget({ weather }) {
  if (!weather) return null

  const rainSafe = weather.rain_1h <= 10.0
  const aqiSafe = weather.aqi <= 400
  const isLive = weather.source === 'live'

  return (
    <div className={`w-full rounded-2xl border overflow-hidden transition-all duration-500 ${
      weather.trigger_fired
        ? 'bg-rose-950/40 border-rose-500/30'
        : 'bg-neutral-900/60 border-white/10'
    }`}>
      {/* Location & Source Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-neutral-800/40 border-b border-white/5">
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3 h-3 text-emerald-400" />
          <span className="text-xs font-semibold text-white">{weather.city || 'Unknown'}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {isLive
            ? <><Wifi className="w-3 h-3 text-emerald-400" /><span className="text-[10px] text-emerald-400 font-semibold uppercase">Live</span></>
            : <><WifiOff className="w-3 h-3 text-amber-400" /><span className="text-[10px] text-amber-400 font-semibold uppercase">{weather.source === 'mock' ? 'Demo' : 'Offline'}</span></>
          }
        </div>
      </div>

      {/* Weather Details */}
      <div className="px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-4 text-sm">
          {/* Temp */}
          <div className="flex items-center gap-1">
            <Thermometer className="w-4 h-4 text-orange-400" />
            <span className="font-mono text-white text-base font-bold">{weather.temp_c ?? '—'}°</span>
          </div>

          <div className="w-px h-5 bg-white/10" />

          {/* Rain */}
          <div className="flex items-center gap-1">
            <CloudRain className={`w-4 h-4 ${rainSafe ? 'text-emerald-400' : 'text-rose-400'}`} />
            <span className="font-mono text-white">{weather.rain_1h}<span className="text-neutral-500 text-xs">mm</span></span>
            {rainSafe
              ? <CheckCircle className="w-3 h-3 text-emerald-500" />
              : <AlertTriangle className="w-3 h-3 text-rose-400 animate-pulse" />
            }
          </div>

          <div className="w-px h-5 bg-white/10" />

          {/* AQI */}
          <div className="flex items-center gap-1">
            <Wind className={`w-4 h-4 ${aqiSafe ? 'text-emerald-400' : 'text-rose-400'}`} />
            <span className="font-mono text-white">{weather.aqi}<span className="text-neutral-500 text-xs"> AQI</span></span>
            {aqiSafe
              ? <CheckCircle className="w-3 h-3 text-emerald-500" />
              : <AlertTriangle className="w-3 h-3 text-rose-400 animate-pulse" />
            }
          </div>
        </div>

        <div className="flex gap-1.5">
          {weather.storm_active && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold uppercase tracking-wider animate-pulse">
              ⚡ Storm
            </span>
          )}
          {weather.curfew_active && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-600/20 text-rose-100 font-bold uppercase tracking-wider animate-pulse">
              🚫 Curfew
            </span>
          )}
          {weather.strike_active && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-orange-600/20 text-orange-200 font-bold uppercase tracking-wider animate-pulse">
              📢 Strike
            </span>
          )}
        </div>
      </div>

      {/* Description Bar */}
      <div className="px-4 py-1.5 border-t border-white/5 flex items-center justify-between">
        <span className="text-[11px] text-neutral-400 italic">{weather.description || ''}</span>
        {weather.humidity != null && (
          <div className="flex items-center gap-1">
            <Droplets className="w-3 h-3 text-blue-400" />
            <span className="text-[10px] text-neutral-500 font-mono">{weather.humidity}%</span>
          </div>
        )}
      </div>
    </div>
  )
}

import { MapContainer, TileLayer, Polygon, Tooltip, Marker } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const RISK_COLORS = {
  high: { fill: '#ef4444', stroke: '#dc2626' },
  medium: { fill: '#f59e0b', stroke: '#d97706' },
  low: { fill: '#22c55e', stroke: '#16a34a' },
}

const STORM_COLOR = { fill: '#ef4444', stroke: '#ff0000' }

export default function ZoneRiskMap({ zones = [], stormActive = false }) {
  return (
    <>
      <style>{`
        .dark-tooltip { background: #1e1e2e !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #e2e8f0 !important; border-radius: 8px !important; padding: 8px 12px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important; }
        .dark-tooltip::before { border-top-color: #1e1e2e !important; }
        .zone-label { background: none !important; border: none !important; }
        @keyframes pulse-zone { 0%,100% { opacity: 0.3; } 50% { opacity: 0.6; } }
        .storm-zone-pulse { animation: pulse-zone 1.5s ease-in-out infinite; }
      `}</style>
      
      <MapContainer 
        center={[28.58, 77.22]} 
        zoom={10} 
        zoomControl={false} 
        attributionControl={false}
        className="w-full h-full z-10"
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={19}
        />
        
        {zones.map(zone => {
          const isStormZone = zone.storm_active
          const colors = isStormZone ? STORM_COLOR : RISK_COLORS[zone.risk_level] || RISK_COLORS.medium
          const coords = zone.polygon.map(([lat, lng]) => [lat, lng])
          
          const labelIcon = L.divIcon({
            className: 'zone-label',
            html: `<div style="font-size:10px;font-weight:700;color:${isStormZone ? '#ef4444' : '#94a3b8'};text-align:center;text-shadow:0 1px 3px rgba(0,0,0,0.8);white-space:nowrap;">${zone.name.split('(')[0].trim()}</div>`
          })

          return (
            <div key={zone.id}>
              <Polygon 
                positions={coords}
                pathOptions={{
                  color: colors.stroke,
                  fillColor: colors.fill,
                  fillOpacity: isStormZone ? 0.45 : 0.2,
                  weight: isStormZone ? 3 : 1.5,
                  dashArray: isStormZone ? '' : '4 4',
                  className: isStormZone ? 'storm-zone-pulse' : ''
                }}
              >
                <Tooltip sticky className="dark-tooltip">
                  <div style={{fontFamily: 'monospace', fontSize: '11px'}}>
                    <b>{zone.name}</b><br/>
                    Risk: {zone.risk_multiplier}x<br/>
                    Workers: {zone.workers}<br/>
                    {isStormZone ? <span style={{color: '#ef4444'}}>⚡ STORM ACTIVE</span> : '✅ Clear'}
                  </div>
                </Tooltip>
              </Polygon>
              <Marker position={zone.center} icon={labelIcon} interactive={false} />
            </div>
          )
        })}
      </MapContainer>
    </>
  )
}

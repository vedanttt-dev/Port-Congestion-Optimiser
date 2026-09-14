import { useMemo, useState, useEffect, useRef } from 'react';
import { Marker, Popup, Map as MapGL } from 'react-map-gl/maplibre';
import * as maplibregl from 'maplibre-gl';
import type { StyleSpecification } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { VesselPosition } from '../api';

// ---------------------------------------------------------------------------
// Satellite basemap
// ---------------------------------------------------------------------------
const SATELLITE_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution: 'Imagery © Esri, Maxar, Earthstar Geographics',
    },
    darkLabels: {
      type: 'raster',
      tiles: ['https://basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}@2x.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors © CARTO',
    },
  },
  layers: [
    { id: 'satellite', type: 'raster', source: 'satellite' },
    { id: 'dark-labels', type: 'raster', source: 'darkLabels' },
  ],
};

// Port grid must mirror backend/app/routers/live.py
export const BASE_LAT = 33.75;
export const BASE_LON = -118.25;
export const BERTH_SPACING = 0.005;

// ---------------------------------------------------------------------------
// Status → color / label
// ---------------------------------------------------------------------------
const STATUS_STYLE: Record<string, { color: string; label: string }> = {
  inbound: { color: '#38bdf8', label: 'Inbound' },
  anchorage: { color: '#eab308', label: 'Waiting (Anchorage)' },
  berthed: { color: '#10b981', label: 'Berthed' },
  outbound: { color: '#a855f7', label: 'Outbound' },
  diverted: { color: '#ec4899', label: 'Diverted' },
};

export const statusColor = (s: string) => STATUS_STYLE[s]?.color ?? '#94a3b8';
export const statusLabel = (s: string) => STATUS_STYLE[s]?.label ?? s;

// ---------------------------------------------------------------------------
// Ship SVG glyph — top-down, rotated by heading, colored by status
// ---------------------------------------------------------------------------
function ShipIcon({ v }: { v: VesselPosition }) {
  const color = statusColor(v.state);
  const size = v.teu_capacity >= 18000 ? 22 : v.teu_capacity >= 8000 ? 18 : 14;

  return (
    <div
      style={{
        width: size,
        height: size * 1.8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transform: `rotate(${v.heading}deg)`,
        filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.5))',
        willChange: 'transform',
      }}
    >
      <svg
        width={size}
        height={size * 1.8}
        viewBox="0 0 20 36"
        xmlns="http://www.w3.org/2000/svg"
        style={{ display: 'block', background: 'transparent' }}
      >
        {/* Wake effect when moving */}
        {v.speed_kn > 1 && (
          <>
            <line x1="10" y1="36" x2="7" y2="32" stroke="#7dd3fc" strokeWidth="1.2" opacity="0.5" />
            <line x1="10" y1="36" x2="13" y2="32" stroke="#7dd3fc" strokeWidth="1.2" opacity="0.5" />
            <line x1="10" y1="36" x2="10" y2="31" stroke="#7dd3fc" strokeWidth="1.2" opacity="0.5" />
          </>
        )}
        {/* Hull */}
        <path
          d="M10 1 C14 5, 17 12, 17 20 L17 28 C17 32, 14 35, 10 35 C6 35, 3 32, 3 28 L3 20 C3 12, 6 5, 10 1 Z"
          fill={color}
          stroke="#0f172a"
          strokeWidth="1.2"
        />
        {/* Bridge */}
        <rect x="6" y="10" width="8" height="8" rx="2" fill="#0f172a" opacity="0.5" />
        {/* Bridge windows */}
        <rect x="7" y="11" width="6" height="2" rx="1" fill={color} opacity="0.7" />
        {/* Stern detail */}
        <rect x="7" y="28" width="6" height="4" rx="1" fill="#0f172a" opacity="0.6" />
        {/* Bow highlight */}
        <circle cx="10" cy="4" r="1.5" fill="white" opacity="0.3" />
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Berth marker
// ---------------------------------------------------------------------------
function BerthIcon({ occupied }: { occupied: boolean }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg width="34" height="14" viewBox="0 0 34 14" style={{ display: 'block' }}>
        <rect
          x="1" y="1" width="32" height="12" rx="3"
          fill={occupied ? '#10b98120' : '#e2e8f0'}
          stroke={occupied ? '#10b981' : '#94a3b8'}
          strokeWidth="1.5"
        />
        {occupied && (
          <>
            <rect x="4" y="4" width="4" height="6" rx="1" fill="#10b981" opacity="0.4" />
            <rect x="10" y="3" width="4" height="7" rx="1" fill="#10b981" opacity="0.5" />
            <rect x="16" y="4" width="4" height="6" rx="1" fill="#10b981" opacity="0.4" />
            <rect x="22" y="3" width="4" height="7" rx="1" fill="#10b981" opacity="0.5" />
            <rect x="28" y="4" width="3" height="6" rx="1" fill="#10b981" opacity="0.4" />
          </>
        )}
      </svg>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Smooth vessel interpolation hook
// ---------------------------------------------------------------------------
function useSmoothVessels(target: VesselPosition[]) {
  const [smoothed, setSmoothed] = useState<VesselPosition[]>(target);
  const prevRef = useRef<Map<string, VesselPosition>>(new Map());
  const targetRef = useRef(target);

  targetRef.current = target;

  useEffect(() => {
    // Update targets
    for (const v of target) {
      prevRef.current.set(v.id, v);
    }
    // Remove departed vessels
    const ids = new Set(target.map((v) => v.id));
    for (const key of prevRef.current.keys()) {
      if (!ids.has(key)) prevRef.current.delete(key);
    }
    setSmoothed(target);
  }, [target]);

  return smoothed;
}


// ---------------------------------------------------------------------------
// Main map component
// ---------------------------------------------------------------------------
export interface PortMapProps {
  vessels: VesselPosition[];
  berthIds: string[];
}

export default function PortMap({ vessels, berthIds }: PortMapProps) {
  const [hovered, setHovered] = useState<VesselPosition | null>(null);

  // Smooth vessel positions to prevent jitter
  const smoothVessels = useSmoothVessels(vessels);

  const occupiedBerths = useMemo(
    () => new Set(smoothVessels.map((v) => v.berth_id).filter(Boolean) as string[]),
    [smoothVessels],
  );

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const v of smoothVessels) c[v.state] = (c[v.state] ?? 0) + 1;
    return c;
  }, [smoothVessels]);

  return (
    <div className="relative h-[520px] w-full overflow-hidden rounded-2xl border border-port-line shadow-card">
      <MapGL
        mapLib={maplibregl}
        initialViewState={{ latitude: BASE_LAT - 0.02, longitude: BASE_LON, zoom: 11.2 }}
        mapStyle={SATELLITE_STYLE}
        style={{ width: '100%', height: '100%' }}
      >
        {/* ---- Berths along the quay ---- */}
        {berthIds.map((id, i) => (
          <Marker
            key={id}
            latitude={BASE_LAT + i * BERTH_SPACING}
            longitude={BASE_LON + i * BERTH_SPACING * 0.5}
            anchor="center"
          >
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'default' }}>
              <span style={{
                marginBottom: 2,
                background: 'rgba(255,255,255,0.9)',
                borderRadius: 4,
                padding: '1px 5px',
                fontSize: 9,
                fontWeight: 600,
                color: '#334155',
                border: '1px solid #cbd5e1',
                whiteSpace: 'nowrap',
              }}>
                {id}
              </span>
              <BerthIcon occupied={occupiedBerths.has(id)} />
            </div>
          </Marker>
        ))}

        {/* ---- Vessels ---- */}
        {smoothVessels.map((v) => (
          <Marker
            key={v.id}
            latitude={v.lat}
            longitude={v.lon}
            anchor="center"
            onClick={() => setHovered(v)}
          >
            <div
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHovered(v)}
              onMouseLeave={() => setHovered((h) => (h?.id === v.id ? null : h))}
            >
              <ShipIcon v={v} />
            </div>
          </Marker>
        ))}

        {/* ---- Hover popup ---- */}
        {hovered && (
          <Popup
            latitude={hovered.lat}
            longitude={hovered.lon}
            anchor="bottom"
            offset={20}
            closeButton={false}
            closeOnClick={false}
          >
            <div style={{
              minWidth: 200,
              fontFamily: 'Inter, system-ui, sans-serif',
              fontSize: 12,
              padding: 2,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontWeight: 700, fontSize: 13, color: '#0f172a' }}>{hovered.name}</span>
                <span style={{
                  background: `${statusColor(hovered.state)}18`,
                  color: statusColor(hovered.state),
                  border: `1px solid ${statusColor(hovered.state)}40`,
                  borderRadius: 99,
                  padding: '1px 8px',
                  fontSize: 10,
                  fontWeight: 600,
                }}>
                  {statusLabel(hovered.state)}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2px 12px', color: '#475569' }}>
                <span style={{ color: '#94a3b8' }}>ID</span><span style={{ fontWeight: 600, color: '#1e293b' }}>{hovered.id}</span>
                <span style={{ color: '#94a3b8' }}>Type</span><span style={{ fontWeight: 600, color: '#1e293b', textTransform: 'capitalize' }}>{hovered.vessel_type}</span>
                <span style={{ color: '#94a3b8' }}>TEU</span><span style={{ fontWeight: 600, color: '#1e293b' }}>{hovered.teu_capacity.toLocaleString()}</span>
                <span style={{ color: '#94a3b8' }}>Speed</span><span style={{ fontWeight: 600, color: '#1e293b' }}>{hovered.speed_kn.toFixed(1)} kn</span>
                <span style={{ color: '#94a3b8' }}>Heading</span><span style={{ fontWeight: 600, color: '#1e293b' }}>{hovered.heading.toFixed(0)}°</span>
                {hovered.berth_id && (<><span style={{ color: '#94a3b8' }}>Berth</span><span style={{ fontWeight: 600, color: '#1e293b' }}>{hovered.berth_id}</span></>)}
              </div>
            </div>
          </Popup>
        )}
      </MapGL>

      {/* ---- HUD: legend ---- */}
      <div className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-xl bg-white/95 border border-slate-200 p-3 shadow-card backdrop-blur-sm">
        <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Vessel status</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {Object.entries(STATUS_STYLE).map(([key, s]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
              <span className="text-[11px] font-medium text-slate-700">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ---- HUD: live counters ---- */}
      <div className="absolute right-3 top-3 z-10 flex gap-2">
        {Object.entries(STATUS_STYLE).map(([s, st]) => (
          <div key={s} className="rounded-xl bg-white/95 border border-slate-200 px-2.5 py-1.5 text-center shadow-card backdrop-blur-sm">
            <p className="text-lg font-bold leading-none" style={{ color: st.color }}>{counts[s] ?? 0}</p>
            <p className="mt-0.5 text-[9px] font-medium uppercase tracking-wide text-slate-500">{st.label.split(' ')[0]}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

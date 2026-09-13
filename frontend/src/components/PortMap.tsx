import { useMemo, useState } from 'react';
import { Marker, Popup, Map as MapGL } from 'react-map-gl/maplibre';
import * as maplibregl from 'maplibre-gl';
import type { StyleSpecification } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { VesselPosition } from '../api';

// ---------------------------------------------------------------------------
// Satellite basemap (Esri World Imagery — free raster tiles, no API key)
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
// Top-down SVG ship glyph, rotated by heading, colored by status
// ---------------------------------------------------------------------------
function ShipIcon({ v }: { v: VesselPosition }) {
  const color = statusColor(v.state);
  const scale = v.teu_capacity >= 18000 ? 1.35 : v.teu_capacity >= 8000 ? 1.1 : 0.9;
  return (
    <svg
      width={16 * scale}
      height={30 * scale}
      viewBox="0 0 16 30"
      style={{ transform: `rotate(${v.heading}deg)` }}
      className="drop-shadow-[0_0_4px_rgba(0,0,0,0.8)]"
    >
      {v.speed_kn > 1 && (
        <path d="M8 30 L5 27 M8 30 L11 27 M8 30 L8 26" stroke="#7dd3fc" strokeWidth="1" opacity="0.6" fill="none" />
      )}
      <path
        d="M8 1 C12 5, 13 12, 13 18 L13 24 C13 27, 10 29, 8 29 C6 29, 3 27, 3 24 L3 18 C3 12, 4 5, 8 1 Z"
        fill={color}
        stroke="#0f172a"
        strokeWidth="1"
      />
      <rect x="5" y="9" width="6" height="7" rx="1" fill="#0f172a" opacity="0.55" />
      <rect x="6" y="24" width="4" height="3" rx="0.5" fill="#0f172a" opacity="0.7" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Berth marker (quay rectangle + label)
// ---------------------------------------------------------------------------
function BerthIcon({ occupied }: { occupied: boolean }) {
  return (
    <svg width="34" height="14" viewBox="0 0 34 14">
      <rect
        x="1" y="1" width="32" height="12" rx="2"
        fill={occupied ? '#10b98125' : '#e2e8f0'}
        stroke={occupied ? '#10b981' : '#94a3b8'}
        strokeWidth="1.5"
      />
    </svg>
  );
}


// ---------------------------------------------------------------------------
// Main map component
// ---------------------------------------------------------------------------
export interface PortMapProps {
  vessels: VesselPosition[];
  /** berth ids in scenario order (from /api/data/summary) */
  berthIds: string[];
}

export default function PortMap({ vessels, berthIds }: PortMapProps) {
  const [hovered, setHovered] = useState<VesselPosition | null>(null);

  const occupiedBerths = useMemo(
    () => new Set(vessels.map((v) => v.berth_id).filter(Boolean) as string[]),
    [vessels],
  );

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const v of vessels) c[v.state] = (c[v.state] ?? 0) + 1;
    return c;
  }, [vessels]);

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
          <Marker key={id} latitude={BASE_LAT + i * BERTH_SPACING} longitude={BASE_LON + i * BERTH_SPACING * 0.5} anchor="center">
            <div className="flex flex-col items-center">
                    <span className="mb-0.5 rounded bg-slate-300/90 px-1 text-[9px] font-medium text-slate-800">{id}</span>
              <BerthIcon occupied={occupiedBerths.has(id)} />
            </div>
          </Marker>
        ))}

        {/* ---- Vessels (hover for details) ---- */}
        {vessels.map((v) => (
          <Marker key={v.id} latitude={v.lat} longitude={v.lon} anchor="center" onClick={() => setHovered(v)}>
            <div
              className="cursor-pointer transition-transform hover:scale-110"
              onMouseEnter={() => setHovered(v)}
              onMouseLeave={() => setHovered((h) => (h?.id === v.id ? null : h))}
            >
              <ShipIcon v={v} />
            </div>
          </Marker>
        ))}

        {/* ---- Hover popup: ship details ---- */}
        {hovered && (
          <Popup latitude={hovered.lat} longitude={hovered.lon} anchor="bottom" offset={18} closeButton={false} closeOnClick={false}>
            <div className="min-w-[190px] space-y-1 text-xs font-sans">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-slate-900">{hovered.name}</span>
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] font-medium border"
                  style={{ backgroundColor: `${statusColor(hovered.state)}15`, color: statusColor(hovered.state), borderColor: `${statusColor(hovered.state)}30` }}
                >
                  {statusLabel(hovered.state)}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-slate-600">
                <span className="text-slate-400">ID</span><span className="font-medium text-slate-800">{hovered.id}</span>
                <span className="text-slate-400">Type</span><span className="capitalize font-medium text-slate-800">{hovered.vessel_type}</span>
                <span className="text-slate-400">TEU</span><span className="font-medium text-slate-800">{hovered.teu_capacity.toLocaleString()}</span>
                <span className="text-slate-400">Speed</span><span className="font-medium text-slate-800">{hovered.speed_kn.toFixed(1)} kn</span>
                <span className="text-slate-400">Heading</span><span className="font-medium text-slate-800">{hovered.heading.toFixed(0)}°</span>
                {hovered.berth_id && (<><span className="text-slate-400">Berth</span><span className="font-medium text-slate-800">{hovered.berth_id}</span></>)}
              </div>
            </div>
          </Popup>
        )}
      </MapGL>

      {/* ---- HUD: legend + live counters ---- */}
      <div className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-xl bg-white/95 border border-slate-200 p-3 shadow-card backdrop-blur">
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

      <div className="absolute right-3 top-3 z-10 flex gap-2">
        {Object.entries(STATUS_STYLE).map(([s, st]) => (
          <div key={s} className="rounded-xl bg-white/95 border border-slate-200 px-2.5 py-1.5 text-center shadow-card backdrop-blur">
            <p className="text-lg font-bold leading-none" style={{ color: st.color }}>{counts[s] ?? 0}</p>
            <p className="mt-0.5 text-[9px] font-medium uppercase tracking-wide text-slate-500">{st.label.split(' ')[0]}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

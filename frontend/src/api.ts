const API = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Health {
  status: string;
  simulator: string;
  version: string;
}

export interface VesselSummary {
  id: string;
  name: string;
  type: string;
  teu_capacity: number;
  eta_h: number;
  priority: number;
}

export interface DataSummary {
  meta: Record<string, unknown>;
  vessels: VesselSummary[];
  berths: { id: string; name: string; length_m: number; max_draft_m: number; crane_count: number }[];
  cranes: { id: string; max_moves_per_hr: number; compatible_berths: string[] }[];
  yard_zones: { id: string; name: string; teu_capacity: number; current_teu: number }[];
  alt_ports: { id: string; name: string }[];
}

export interface VesselForecast {
  vessel_id: string;
  name: string;
  type: string;
  predicted_wait_h: number;
  predicted_berth_h: number;
  status: string;
  eta_h: number;
  teu_capacity: number;
  priority: number;
}

export interface Hotspot {
  id: string;
  type: string;
  severity: string;
  message: string;
  lead_time_h: number;
  affected_berths: string[];
}

export interface QueueForecast {
  time_h: number;
  queue_length: number;
}

export interface BerthUtilForecast {
  time_h: number;
  util_pct: number;
}

export interface PredictResponse {
  vessel_forecasts: VesselForecast[];
  hotspots: Hotspot[];
  queue_forecast: QueueForecast[];
  berth_util_forecast: BerthUtilForecast[];
}

export interface Assignment {
  vessel_id: string;
  berth_id: string;
  start_h: number;
  end_h: number;
  crane_count: number;
  moves_planned: number;
}

export interface Reroute {
  vessel_id: string;
  alt_port_id: string;
  est_cost_usd: number;
  saving_usd: number;
  reason: string;
}

export interface KpiComparison {
  avg_wait_h: number;
  p95_wait_h: number;
  max_queue: number;
  berth_util_pct: number;
  crane_util_pct: number;
  yard_util_pct: number;
  demurrage_cost_usd: number;
  cost_saved_usd?: number;
}

export interface OptimizeResponse {
  assignments: Assignment[];
  reroutes: Reroute[];
  kpis: { baseline: KpiComparison; optimized: KpiComparison };
  solve_ms: number;
}

export interface WorkOrder {
  vessel_id: string;
  berth_id: string;
  crane_ids: string[];
  target_moves: number;
  priority: number;
  alert: string;
}

export interface ShiftBlock {
  id: string;
  window: string;
  alerts: string[];
  work_orders: WorkOrder[];
  contingency_notes: string[];
}

export interface PlanResponse {
  shifts: ShiftBlock[];
}

export interface KpisResponse {
  avg_wait_h: number;
  p95_wait_h: number;
  max_queue: number;
  berth_util_pct: number;
  crane_util_pct: number;
  yard_util_pct: number;
  demurrage_cost_usd: number;
}

export interface VesselPosition {
  id: string;
  name: string;
  lat: number;
  lon: number;
  state: string;
  speed_kn: number;
  heading: number;
  berth_id: string | null;
  vessel_type: string;
  teu_capacity: number;
}

export interface LiveEvent {
  time_h: number;
  vessel_id: string;
  event_type: string;
  detail: string;
}

export interface LiveResponse {
  timestamp: string;
  sim_h?: number;
  vessels: VesselPosition[];
  queue_size?: number;
  yard_util_pct?: number;
  recent_events: LiveEvent[];
  kpis: { avg_wait_h: number; demurrage_cost_usd: number };
}

// ---------------------------------------------------------------------------
// Scenario types
// ---------------------------------------------------------------------------

export interface ScenarioSummary {
  name: string;
  seed: number;
  weeks: number;
  num_vessels: number;
  num_berths: number;
  num_cranes: number;
  avg_wait_h: number | null;
  demurrage_usd: number | null;
}

export interface ScenarioGenerateRequest {
  name: string;
  seed: number;
  weeks: number;
  num_berths?: number;
  num_cranes?: number;
}

export interface ScenarioGenerateResponse {
  name: string;
  meta: Record<string, unknown>;
  num_vessels: number;
  num_berths: number;
  num_cranes: number;
  status: string;
}

export interface ScenarioCompareResponse {
  scenario_a: {
    name: string;
    meta: Record<string, unknown>;
    kpis: KpisResponse;
  };
  scenario_b: {
    name: string;
    meta: Record<string, unknown>;
    kpis: KpisResponse;
  };
  deltas_pct: Record<string, number>;
}

// ---------------------------------------------------------------------------
// WebSocket types
// ---------------------------------------------------------------------------

export interface WsUpdate {
  type: 'update';
  sim_h: number;
  vessels: VesselPosition[];
  events: LiveEvent[];
  queue_size: number;
  yard_util_pct: number;
  status_counts?: Record<string, number>;
  kpis: { avg_wait_h: number; demurrage_cost_usd: number };
}

export interface WsStatus {
  type: 'status';
  running: boolean;
  sim_h: number;
  horizon_h: number;
  speed?: number;
  message?: string;
  num_vessels?: number;
  num_berths?: number;
  num_cranes?: number;
}

export type WsMessage = WsUpdate | WsStatus;

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const api = {
  health: () => get<Health>('/health'),
  data: () => get<DataSummary>('/data/summary'),
  predict: (body?: unknown) => post<PredictResponse>('/predict', body),
  optimize: (body?: unknown) => post<OptimizeResponse>('/optimize', body),
  plan: (body?: unknown) => post<PlanResponse>('/plan', body),
  kpis: () => get<KpisResponse>('/kpis'),
  live: () => get<LiveResponse>('/live'),

  // Scenario management
  scenarioList: () => get<ScenarioSummary[]>('/scenario/list'),
  scenarioGenerate: (body: ScenarioGenerateRequest) => post<ScenarioGenerateResponse>('/scenario/generate', body),
  scenarioKpis: (name: string) => get<{ name: string; kpis: KpisResponse }>(`/scenario/${name}/kpis`),
  scenarioCompare: (a: string, b: string) => post<ScenarioCompareResponse>('/scenario/compare', { scenario_a: a, scenario_b: b }),
  scenarioSetActive: (name: string) => post<{ active: string }>('/scenario/set-active', { name }),
  scenarioDelete: (name: string) => del<{ deleted: boolean }>(`/scenario/${name}`),
};

// ---------------------------------------------------------------------------
// WebSocket helper
// ---------------------------------------------------------------------------

export function connectLiveSocket(onMessage: (msg: WsMessage) => void): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const ws = new WebSocket(`${protocol}//${host}/api/ws/live`);

  ws.onmessage = (event) => {
    try {
      const msg: WsMessage = JSON.parse(event.data);
      onMessage(msg);
    } catch { /* ignore parse errors */ }
  };

  return ws;
}

// ---------------------------------------------------------------------------
// Export helper
// ---------------------------------------------------------------------------

export async function downloadFile(path: string, filename: string) {
  try {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) throw new Error(`Download failed: ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Download error:', err);
  }
}

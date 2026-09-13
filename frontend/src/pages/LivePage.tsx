import { useEffect, useRef, useState, useCallback } from 'react';
import { api, DataSummary, VesselPosition, LiveEvent, connectLiveSocket, WsMessage } from '../api';
import PortMap from '../components/PortMap';
import { Play, Pause, Clock, MapPin, DollarSign, Activity, Wifi, WifiOff } from 'lucide-react';

export default function LivePage() {
  const [summary, setSummary] = useState<DataSummary | null>(null);
  const [loading, setLoading] = useState(true);

  // WebSocket state
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [running, setRunning] = useState(false);
  const [simH, setSimH] = useState(0);
  const [horizonH] = useState(672);
  const [speed, setSpeed] = useState(1);
  const [vessels, setVessels] = useState<VesselPosition[]>([]);
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [queueSize, setQueueSize] = useState(0);
  const [yardUtil, setYardUtil] = useState(0);
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({});
  const [kpis, setKpis] = useState({ avg_wait_h: 0, demurrage_cost_usd: 0 });

  const handleMessage = useCallback((msg: WsMessage) => {
    if (msg.type === 'update') {
      setSimH(msg.sim_h);
      setVessels(msg.vessels);
      setEvents(msg.events);
      setQueueSize(msg.queue_size);
      setYardUtil(msg.yard_util_pct);
      setKpis(msg.kpis);
      if (msg.status_counts) setStatusCounts(msg.status_counts);
    } else if (msg.type === 'status') {
      setRunning(msg.running);
      setSimH(msg.sim_h);
      if (msg.running === false && msg.message) {
        // Simulation complete
      }
    }
  }, []);

  useEffect(() => {
    api.data().then(setSummary).catch(console.error).finally(() => setLoading(false));

    // Connect WebSocket
    const ws = connectLiveSocket(handleMessage);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ action: 'status' }));
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [handleMessage]);

  const send = (cmd: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(cmd));
    }
  };

  const handlePlay = () => send({ action: 'start', speed });
  const handlePause = () => send({ action: 'stop' });
  const handleSpeed = (s: number) => { setSpeed(s); if (running) send({ action: 'start', speed: s }); };
  const handleSeek = (h: number) => send({ action: 'seek', sim_h: h });

  const progress = horizonH > 0 ? (simH / horizonH) * 100 : 0;

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="skeleton h-[520px] rounded-2xl" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-port-text">Live Port Simulation</h2>
          <p className="mt-1 text-sm text-port-muted">Real-time vessel movements via WebSocket streaming</p>
        </div>
        <div className="flex items-center gap-2">
          {connected ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
              <Wifi className="h-3 w-3" /> Connected
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-600">
              <WifiOff className="h-3 w-3" /> Disconnected
            </span>
          )}
        </div>
      </div>

      {/* Transport controls */}
      <div className="rounded-2xl border border-port-line bg-port-panel p-4 shadow-card">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <button
              onClick={running ? handlePause : handlePlay}
              className={`flex h-10 w-10 items-center justify-center rounded-xl transition-all ${
                running
                  ? 'bg-amber-500 text-white shadow-sm shadow-amber-500/20 hover:bg-amber-600'
                  : 'bg-brand-600 text-white shadow-sm shadow-brand-600/20 hover:bg-brand-700'
              }`}
            >
              {running ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </button>
          </div>

          {/* Speed buttons */}
          <div className="flex rounded-xl border border-port-line bg-port-bg overflow-hidden">
            {[1, 2, 5, 10].map((s) => (
              <button
                key={s}
                onClick={() => handleSpeed(s)}
                className={`px-3 py-1.5 text-xs font-semibold transition-all ${
                  speed === s ? 'bg-brand-600 text-white' : 'text-port-muted hover:bg-port-panelHover'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Time slider */}
          <div className="flex-1 flex items-center gap-3">
            <Clock className="h-4 w-4 text-port-muted shrink-0" />
            <input
              type="range"
              min={0}
              max={horizonH}
              step={1}
              value={simH}
              onChange={(e) => handleSeek(Number(e.target.value))}
              className="flex-1 accent-brand-600"
            />
            <span className="text-xs font-mono font-medium text-port-muted w-16 text-right">{simH.toFixed(0)}h</span>
          </div>

          {/* Progress */}
          <div className="w-32">
            <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${Math.min(100, progress)}%` }} />
            </div>
            <p className="mt-0.5 text-[10px] text-center text-port-muted">{progress.toFixed(0)}% of {horizonH}h</p>
          </div>
        </div>
      </div>

      <PortMap vessels={vessels} berthIds={(summary?.berths ?? []).map((b) => b.id)} />

      <div className="grid gap-5 md:grid-cols-4">
        <div className="rounded-2xl border border-port-line bg-port-panel p-4 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-brand-600" />
            <p className="text-[10px] font-semibold uppercase tracking-wider text-port-muted">Avg Wait</p>
          </div>
          <p className="text-xl font-bold text-port-text">{kpis.avg_wait_h.toFixed(1)}h</p>
        </div>
        <div className="rounded-2xl border border-port-line bg-port-panel p-4 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="h-4 w-4 text-brand-600" />
            <p className="text-[10px] font-semibold uppercase tracking-wider text-port-muted">Yard Util</p>
          </div>
          <p className="text-xl font-bold text-port-text">{yardUtil.toFixed(0)}%</p>
        </div>
        <div className="rounded-2xl border border-port-line bg-port-panel p-4 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="h-4 w-4 text-brand-600" />
            <p className="text-[10px] font-semibold uppercase tracking-wider text-port-muted">Demurrage</p>
          </div>
          <p className="text-xl font-bold text-port-text">${kpis.demurrage_cost_usd.toLocaleString()}</p>
        </div>
        <div className="rounded-2xl border border-port-line bg-port-panel p-4 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="h-4 w-4 text-brand-600" />
            <p className="text-[10px] font-semibold uppercase tracking-wider text-port-muted">Queue</p>
          </div>
          <p className="text-xl font-bold text-port-text">{queueSize} vessels</p>
        </div>
      </div>

      {/* Vessels table */}
      <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-port-line px-5 py-3.5">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-port-text">
            <Activity className="h-4 w-4 text-brand-600" />
            Vessels ({vessels.length})
          </h3>
          <div className="flex gap-2">
            {Object.entries(statusCounts).map(([state, count]) => (
              <span key={state} className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                state === 'berthed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                state === 'anchorage' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                state === 'inbound' ? 'bg-sky-50 text-sky-700 border border-sky-200' :
                state === 'diverted' ? 'bg-pink-50 text-pink-700 border border-pink-200' :
                'bg-slate-50 text-slate-600 border border-slate-200'
              }`}>{count} {state}</span>
            ))}
          </div>
        </div>
        <div className="max-h-64 overflow-y-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-port-line bg-slate-50/80">
                {['ID', 'Name', 'Status', 'Berth', 'Speed'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-port-line">
              {vessels.map((v) => (
                <tr key={v.id} className="hover:bg-port-panelHover transition-colors">
                  <td className="px-4 py-2 text-xs font-medium text-slate-500">{v.id}</td>
                  <td className="px-4 py-2 text-sm font-medium text-port-text">{v.name}</td>
                  <td className="px-4 py-2">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      v.state === 'berthed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      v.state === 'anchorage' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                      v.state === 'inbound' ? 'bg-sky-50 text-sky-700 border border-sky-200' :
                      v.state === 'diverted' ? 'bg-pink-50 text-pink-700 border border-pink-200' :
                      'bg-slate-50 text-slate-600 border border-slate-200'
                    }`}>{v.state}</span>
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500">{v.berth_id ?? '—'}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">{v.speed_kn.toFixed(1)} kn</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Events feed */}
      <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
        <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
          <Activity className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-port-text">Recent Events</h3>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {events.map((e, i) => (
            <div key={i} className="flex items-center gap-3 border-b border-port-line px-5 py-2 last:border-0 hover:bg-port-panelHover transition-colors">
              <span className="rounded-full bg-slate-100 border border-slate-200 px-2 py-0.5 text-[10px] font-mono font-medium text-slate-600">h{e.time_h.toFixed(1)}</span>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                e.event_type === 'arrival' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                e.event_type === 'berth' || e.event_type === 'berth_assign' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                e.event_type === 'departure' ? 'bg-purple-50 text-purple-700 border border-purple-200' :
                'bg-slate-50 text-slate-600 border border-slate-200'
              }`}>{e.event_type}</span>
              <span className="text-sm font-medium text-port-text">{e.vessel_id}</span>
              <span className="text-xs text-slate-500">{e.detail}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

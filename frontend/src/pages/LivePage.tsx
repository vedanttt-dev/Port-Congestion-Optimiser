import { useEffect, useState } from 'react';
import { api, DataSummary, LiveResponse } from '../api';
import PortMap from '../components/PortMap';
import { Clock, MapPin, DollarSign, Activity } from 'lucide-react';

export default function LivePage() {
  const [data, setData] = useState<LiveResponse | null>(null);
  const [summary, setSummary] = useState<DataSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.data().then(setSummary).catch(console.error);
    const poll = () => {
      api.live()
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    };
    poll();
    const id = setInterval(poll, 10000);
    return () => clearInterval(id);
  }, []);

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="skeleton h-[520px] rounded-2xl" />
    </div>
  );

  if (!data) return <p className="text-red-600 font-medium">Failed to load live data</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-port-text">Live Port Map</h2>
          <p className="mt-1 text-sm text-port-muted">Real-time vessel positions and port status</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="text-xs font-medium text-slate-500">Sim Hour: {data.sim_h?.toFixed(1) ?? data.timestamp ?? 'N/A'}</span>
        </div>
      </div>

      <PortMap vessels={data.vessels} berthIds={(summary?.berths ?? []).map((b) => b.id)} />

      <div className="grid gap-5 md:grid-cols-3">
        <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-brand-600" />
            <p className="text-xs font-semibold text-port-muted">Avg Wait</p>
          </div>
          <p className="text-2xl font-bold text-port-text">{data.kpis.avg_wait_h.toFixed(1)}h</p>
        </div>
        <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="h-4 w-4 text-brand-600" />
            <p className="text-xs font-semibold text-port-muted">Yard Utilisation</p>
          </div>
          <p className="text-2xl font-bold text-port-text">{(data.yard_util_pct ?? 0).toFixed(0)}%</p>
        </div>
        <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="h-4 w-4 text-brand-600" />
            <p className="text-xs font-semibold text-port-muted">Demurrage</p>
          </div>
          <p className="text-2xl font-bold text-port-text">${data.kpis.demurrage_cost_usd.toLocaleString()}</p>
        </div>
      </div>

      <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
        <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
          <Activity className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-port-text">Vessels ({data.vessels.length})</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-port-line bg-slate-50/80">
              {['ID', 'Name', 'Status', 'Berth', 'Speed'].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-port-line">
            {data.vessels.map((v) => (
              <tr key={v.id} className="hover:bg-port-panelHover transition-colors">
                <td className="px-4 py-2.5 text-xs font-medium text-slate-500">{v.id}</td>
                <td className="px-4 py-2.5 text-sm font-medium text-port-text">{v.name}</td>
                <td className="px-4 py-2.5">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    v.state === 'berthed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                    v.state === 'anchorage' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                    v.state === 'inbound' ? 'bg-sky-50 text-sky-700 border border-sky-200' :
                    v.state === 'diverted' ? 'bg-pink-50 text-pink-700 border border-pink-200' :
                    'bg-slate-50 text-slate-600 border border-slate-200'
                  }`}>{v.state}</span>
                </td>
                <td className="px-4 py-2.5 text-xs text-slate-500">{v.berth_id ?? '—'}</td>
                <td className="px-4 py-2.5 text-xs text-slate-500">{v.speed_kn.toFixed(1)} kn</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
        <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
          <Activity className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-port-text">Recent Events</h3>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {data.recent_events.map((e, i) => (
            <div key={i} className="flex items-center gap-3 border-b border-port-line px-5 py-2.5 last:border-0 hover:bg-port-panelHover transition-colors">
              <span className="rounded-full bg-slate-100 border border-slate-200 px-2 py-0.5 text-[10px] font-mono font-medium text-slate-600">h{e.time_h.toFixed(1)}</span>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                e.event_type === 'arrival' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                e.event_type === 'berth' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
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

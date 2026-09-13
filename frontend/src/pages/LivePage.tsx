import { useEffect, useState } from 'react';
import { api, LiveResponse } from '../api';

export default function LivePage() {
  const [data, setData] = useState<LiveResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load live data</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Live Port Map</h2>
        <span className="text-xs text-slate-400">Updated: {data.timestamp}</span>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-port-line bg-port-panel p-4">
          <p className="text-xs text-slate-400">Avg Wait</p>
          <p className="text-2xl font-semibold text-white">{data.kpis.avg_wait_h.toFixed(1)}h</p>
        </div>
        <div className="rounded-xl border border-port-line bg-port-panel p-4">
          <p className="text-xs text-slate-400">Berth Util</p>
          <p className="text-2xl font-semibold text-white">{data.kpis.berth_util_pct.toFixed(0)}%</p>
        </div>
        <div className="rounded-xl border border-port-line bg-port-panel p-4">
          <p className="text-xs text-slate-400">Demurrage</p>
          <p className="text-2xl font-semibold text-white">${data.kpis.demurrage_cost_usd.toLocaleString()}</p>
        </div>
      </div>

      <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
        <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">Vessels</h3>
        <table className="w-full">
          <thead>
            <tr className="border-b border-port-line">
              <th className="px-3 py-2 text-left text-xs text-slate-400">ID</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Name</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.vessels.map((v) => (
              <tr key={v.id} className="border-t border-port-line">
                <td className="px-3 py-2 text-xs text-slate-400">{v.id}</td>
                <td className="px-3 py-2 text-sm text-white">{v.name}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${
                    v.status === 'at_berth' ? 'bg-emerald-500/20 text-emerald-400' :
                    v.status === 'waiting' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-slate-500/20 text-slate-400'
                  }`}>{v.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
        <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">Recent Events</h3>
        <div className="max-h-64 overflow-y-auto">
          {data.recent_events.map((e, i) => (
            <div key={i} className="flex items-center gap-3 border-b border-port-line px-4 py-2">
              <span className="text-xs text-slate-500">h{e.time_h.toFixed(1)}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs ${
                e.type === 'arrival' ? 'bg-blue-500/20 text-blue-400' :
                e.type === 'berth' ? 'bg-emerald-500/20 text-emerald-400' :
                e.type === 'departure' ? 'bg-purple-500/20 text-purple-400' :
                'bg-slate-500/20 text-slate-400'
              }`}>{e.type}</span>
              <span className="text-sm text-white">{e.vessel_id}</span>
              <span className="text-xs text-slate-400">{e.detail}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

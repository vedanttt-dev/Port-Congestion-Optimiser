import { useEffect, useState } from 'react';
import { api, PredictResponse } from '../api';

export default function PredictPage() {
  const [data, setData] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.predict()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load predictions</p>;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Congestion Prediction</h2>

      {data.hotspots.length > 0 && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
          <h3 className="mb-3 font-medium text-red-400">⚠️ Hotspots Detected</h3>
          <div className="space-y-2">
            {data.hotspots.map((h) => (
              <div key={h.id} className="flex items-center gap-3 rounded-lg bg-port-bg/60 px-3 py-2 text-sm">
                <span className={`h-2 w-2 rounded-full ${h.severity === 'high' ? 'bg-red-400' : 'bg-amber-400'}`} />
                <span className="text-slate-300">{h.message}</span>
                <span className="ml-auto text-xs text-slate-500">Lead: {h.lead_time_h}h | Berths: {h.affected_berths.join(', ')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
        <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">Vessel Forecasts</h3>
        <table className="w-full">
          <thead>
            <tr className="border-b border-port-line">
              <th className="px-3 py-2 text-left text-xs text-slate-400">Vessel</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Type</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">ETA</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Wait (h)</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Berth (h)</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.vessel_forecasts.map((v) => (
              <tr key={v.vessel_id} className="border-t border-port-line">
                <td className="px-3 py-2 text-sm text-white">{v.name}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{v.type}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{v.eta_h.toFixed(1)}h</td>
                <td className="px-3 py-2 text-xs text-slate-300">{v.predicted_wait_h.toFixed(1)}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{v.predicted_berth_h.toFixed(1)}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${
                    v.status === 'congested' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
                  }`}>{v.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

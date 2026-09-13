import { useEffect, useState } from 'react';
import { api, PredictResponse } from '../api';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';

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

  const queueData = data.queue_forecast.map((q) => ({
    time: `h${q.time_h.toFixed(0)}`,
    queue: q.queue_length,
  }));

  const berthData = data.berth_util_forecast.map((b) => ({
    time: `h${b.time_h.toFixed(0)}`,
    util: b.util_pct,
  }));

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Congestion Prediction</h2>

      {/* Hotspots */}
      {data.hotspots.length > 0 && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
          <h3 className="mb-3 font-medium text-red-400">⚠️ Hotspots Detected ({data.hotspots.length})</h3>
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

      {/* Charts row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Queue Forecast Chart */}
        <div className="rounded-xl border border-port-line bg-port-panel p-4">
          <h3 className="mb-3 text-sm font-medium text-white">Queue Forecast</h3>
          {queueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={queueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2a44" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ background: '#111a2c', border: '1px solid #1e2a44', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Line type="monotone" dataKey="queue" stroke="#38bdf8" strokeWidth={2} dot={false} name="Queue Length" />
                <ReferenceLine y={5} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'Critical', fill: '#ef4444', fontSize: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-xs text-slate-500">No queue forecast data</p>
          )}
        </div>

        {/* Berth Utilisation Chart */}
        <div className="rounded-xl border border-port-line bg-port-panel p-4">
          <h3 className="mb-3 text-sm font-medium text-white">Berth Utilisation Forecast</h3>
          {berthData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={berthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2a44" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ background: '#111a2c', border: '1px solid #1e2a44', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#e2e8f0' }}
                  formatter={(value) => [`${Number(value).toFixed(0)}%`, 'Utilisation']}
                />
                <ReferenceLine y={85} stroke="#ef4444" strokeDasharray="5 5" label={{ value: '85%', fill: '#ef4444', fontSize: 10 }} />
                <Bar dataKey="util" fill="#38bdf8" radius={[2, 2, 0, 0]} name="Berth Util %" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-xs text-slate-500">No berth utilisation data</p>
          )}
        </div>
      </div>

      {/* Vessel forecasts table */}
      <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-port-line px-4 py-3">
          <h3 className="text-sm font-medium text-white">Vessel Forecasts</h3>
          <div className="flex gap-3 text-xs text-slate-400">
            <span>Forecast: {data.vessel_forecasts.length} vessels</span>
            <span className="text-red-400">Congested: {data.vessel_forecasts.filter((v) => v.status === 'congested').length}</span>
          </div>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-port-line">
              <th className="px-3 py-2 text-left text-xs text-slate-400">Vessel</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Type</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">ETA</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Wait (h)</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Berth (h)</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">TEU</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.vessel_forecasts
              .sort((a, b) => b.predicted_wait_h - a.predicted_wait_h)
              .map((v) => (
                <tr key={v.vessel_id} className="border-t border-port-line hover:bg-port-bg/40">
                  <td className="px-3 py-2 text-sm text-white">{v.name}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${
                      v.type === 'mega' ? 'bg-purple-500/20 text-purple-400' :
                      v.type === 'medium' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-slate-500/20 text-slate-400'
                    }`}>{v.type}</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-300">{v.eta_h.toFixed(1)}h</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs font-medium ${v.predicted_wait_h > 24 ? 'text-red-400' : v.predicted_wait_h > 12 ? 'text-amber-400' : 'text-slate-300'}`}>
                      {v.predicted_wait_h.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-300">{v.predicted_berth_h.toFixed(1)}</td>
                  <td className="px-3 py-2 text-xs text-slate-300">{v.teu_capacity.toLocaleString()}</td>
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

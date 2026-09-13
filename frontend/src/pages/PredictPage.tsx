import { useEffect, useState } from 'react';
import { api, PredictResponse, downloadFile } from '../api';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Download, AlertTriangle, TrendingUp } from 'lucide-react';

export default function PredictPage() {
  const [data, setData] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.predict().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="grid gap-5 md:grid-cols-2"><div className="skeleton h-72 rounded-2xl" /><div className="skeleton h-72 rounded-2xl" /></div>
      <div className="skeleton h-64 rounded-2xl" />
    </div>
  );
  if (!data) return <p className="text-red-600 font-medium">Failed to load predictions</p>;

  const queueData = data.queue_forecast.map((q: any) => ({
    time: `h${(q.time_h ?? q.h ?? 0).toFixed(0)}`,
    queue: q.queue_length ?? q.queue_size ?? 0,
  }));

  const berthTimeMap: Record<number, number[]> = {};
  for (const b of data.berth_util_forecast) {
    const buckets = (b as any).buckets ?? [b];
    for (const bucket of buckets) {
      const h = bucket.h ?? bucket.time_h ?? 0;
      const util = bucket.util_pct ?? 0;
      if (!berthTimeMap[h]) berthTimeMap[h] = [];
      berthTimeMap[h].push(util);
    }
  }
  const berthData = Object.entries(berthTimeMap)
    .map(([h, utils]) => ({ time: `h${Number(h).toFixed(0)}`, util: Math.max(...utils) }))
    .sort((a, b) => Number(a.time.slice(1)) - Number(b.time.slice(1)));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-port-text">Congestion Prediction</h2>
          <p className="mt-1 text-sm text-port-muted">Forward simulation forecast and hotspot detection</p>
        </div>
        <button
          onClick={() => downloadFile('/export/predict', 'predictions.csv')}
          className="inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 hover:shadow-md"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {data.hotspots.length > 0 && (
        <div className="rounded-2xl border border-red-200 bg-red-50/60 p-5">
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <h3 className="font-semibold text-red-800">Hotspots Detected ({data.hotspots.length})</h3>
          </div>
          <div className="space-y-2">
            {data.hotspots.map((h) => (
              <div key={h.id} className="flex items-center gap-3 rounded-xl bg-white/80 border border-red-100 px-4 py-2.5 text-sm">
                <span className={`h-2 w-2 shrink-0 rounded-full ${h.severity === 'high' ? 'bg-red-500' : 'bg-amber-500'}`} />
                <span className="text-slate-700">{h.message}</span>
                <span className="ml-auto text-xs text-slate-500">Lead: {h.lead_time_h}h</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-5 md:grid-cols-2">
        <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Queue Forecast</h3>
          </div>
          {queueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={queueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
                <Line type="monotone" dataKey="queue" stroke="#2563eb" strokeWidth={2.5} dot={false} activeDot={{ r: 5, fill: '#2563eb' }} />
                <ReferenceLine y={5} stroke="#ef4444" strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-port-muted">No queue data</p>}
        </div>

        <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Berth Utilisation</h3>
          </div>
          {berthData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={berthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} formatter={(value) => [`${Number(value).toFixed(0)}%`, 'Utilisation']} />
                <ReferenceLine y={85} stroke="#ef4444" strokeDasharray="5 5" />
                <Bar dataKey="util" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-port-muted">No berth data</p>}
        </div>
      </div>

      <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-port-line px-5 py-3.5">
          <h3 className="text-sm font-semibold text-port-text">Vessel Forecasts ({data.vessel_forecasts.length})</h3>
          <span className="rounded-full bg-red-50 border border-red-200 px-2.5 py-0.5 text-xs font-medium text-red-700">
            Congested: {data.vessel_forecasts.filter((v) => v.status === 'congested').length}
          </span>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-port-line bg-slate-50/80">
              {['Vessel', 'Type', 'ETA', 'Wait (h)', 'Berth (h)', 'Status'].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-port-line">
            {data.vessel_forecasts.sort((a, b) => b.predicted_wait_h - a.predicted_wait_h).map((v) => (
              <tr key={v.vessel_id} className="hover:bg-port-panelHover transition-colors">
                <td className="px-4 py-2.5 text-sm font-medium text-port-text">{v.name}</td>
                <td className="px-4 py-2.5">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    v.type === 'mega' ? 'bg-purple-50 text-purple-700 border border-purple-200' :
                    v.type === 'medium' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                    'bg-slate-50 text-slate-600 border border-slate-200'
                  }`}>{v.type}</span>
                </td>
                <td className="px-4 py-2.5 text-sm text-slate-600">{v.eta_h.toFixed(1)}h</td>
                <td className="px-4 py-2.5">
                  <span className={`text-sm font-semibold ${v.predicted_wait_h > 24 ? 'text-red-600' : v.predicted_wait_h > 12 ? 'text-amber-600' : 'text-slate-700'}`}>{v.predicted_wait_h.toFixed(1)}</span>
                </td>
                <td className="px-4 py-2.5 text-sm text-slate-600">{v.predicted_berth_h.toFixed(1)}</td>
                <td className="px-4 py-2.5">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    v.status === 'congested' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
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

import { useEffect, useState } from 'react';
import { api, OptimizeResponse, downloadFile } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Download, ArrowRight, Route, Ship } from 'lucide-react';

export default function OptimizePage() {
  const [data, setData] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.optimize().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="skeleton h-32 rounded-2xl" />
      <div className="skeleton h-72 rounded-2xl" />
    </div>
  );
  if (!data) return <p className="text-red-600 font-medium">Failed to load optimisation</p>;

  const { baseline, optimized } = data.kpis;
  const chartData = [
    { metric: 'Avg Wait', baseline: baseline.avg_wait_h, optimised: optimized.avg_wait_h },
    { metric: 'P95 Wait', baseline: baseline.p95_wait_h, optimised: optimized.p95_wait_h },
    { metric: 'Berth Util', baseline: baseline.berth_util_pct, optimised: optimized.berth_util_pct },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-port-text">Berth &amp; Crane Optimiser</h2>
          <p className="mt-1 text-sm text-port-muted">CP-SAT constrained optimisation with reroute recommendations</p>
        </div>
        <button
          onClick={() => downloadFile('/export/optimize', 'optimiser.csv')}
          className="inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 hover:shadow-md"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {optimized.cost_saved_usd !== undefined && optimized.cost_saved_usd > 0 && (
        <div className="rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50 p-6 text-center shadow-card">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-emerald-600">Total Estimated Savings</p>
          <span className="text-4xl font-extrabold text-emerald-700">${optimized.cost_saved_usd.toLocaleString()}</span>
          <p className="mt-1.5 text-xs text-emerald-600/80">CP-SAT reroutes + wait reduction ({data.solve_ms}ms solve time)</p>
        </div>
      )}

      <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
        <h3 className="mb-4 text-sm font-semibold text-port-text">Before vs After Comparison</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
            <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="baseline" fill="#94a3b8" name="Baseline (FCFS)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="optimised" fill="#2563eb" name="Optimised (CP-SAT)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        <KpiCompare label="Avg Wait (h)" baseline={baseline.avg_wait_h} optimized={optimized.avg_wait_h} unit="h" lower />
        <KpiCompare label="P95 Wait (h)" baseline={baseline.p95_wait_h} optimized={optimized.p95_wait_h} unit="h" lower />
        <KpiCompare label="Berth Util %" baseline={baseline.berth_util_pct} optimized={optimized.berth_util_pct} unit="%" />
        <KpiCompare label="Demurrage ($)" baseline={baseline.demurrage_cost_usd} optimized={optimized.demurrage_cost_usd} unit="$" lower />
      </div>

      {data.reroutes.length > 0 && (
        <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
            <Route className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Reroute Recommendations ({data.reroutes.length})</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-port-line bg-slate-50/80">
                {['Vessel', 'Alt Port', 'Saving', 'Reason'].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-port-line">
              {data.reroutes.map((r, i) => (
                <tr key={i} className="hover:bg-port-panelHover transition-colors">
                  <td className="px-4 py-2.5 text-sm font-medium text-port-text">{r.vessel_id}</td>
                  <td className="px-4 py-2.5 text-sm text-slate-600">{r.alt_port_id}</td>
                  <td className="px-4 py-2.5 text-sm font-semibold text-emerald-600">+${r.saving_usd.toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{r.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
        <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
          <Ship className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-port-text">Berth Assignments ({data.assignments.length})</h3>
        </div>
        <div className="p-5 space-y-2">
          {data.assignments.map((a, i) => {
            const maxEnd = Math.max(...data.assignments.map((x) => x.end_h), 1);
            return (
              <div key={i} className="flex items-center gap-3">
                <span className="w-24 shrink-0 truncate text-xs font-medium text-slate-500">{a.vessel_id}</span>
                <div className="relative h-7 flex-1 rounded-lg bg-slate-100 overflow-hidden">
                  <div
                    className="absolute inset-y-0 rounded-lg bg-gradient-to-r from-brand-500 to-brand-600 flex items-center justify-center text-[10px] font-semibold text-white shadow-sm"
                    style={{ left: `${(a.start_h / maxEnd) * 100}%`, width: `${Math.max(3, ((a.end_h - a.start_h) / maxEnd) * 100)}%` }}
                  >
                    {a.berth_id} ({a.crane_count}QC)
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function KpiCompare({ label, baseline, optimized, unit, lower }: { label: string; baseline: number; optimized: number; unit: string; lower?: boolean }) {
  const diff = optimized - baseline;
  const pct = baseline !== 0 ? (diff / baseline) * 100 : 0;
  const improved = lower ? diff < 0 : diff > 0;

  const cardBg = improved
    ? 'border-emerald-200 bg-emerald-50/50'
    : diff === 0
      ? 'border-port-line bg-port-panel'
      : 'border-red-200 bg-red-50/50';

  const valColor = improved ? 'text-emerald-700' : diff === 0 ? 'text-port-text' : 'text-red-700';
  const diffColor = improved ? 'text-emerald-600' : diff === 0 ? 'text-slate-500' : 'text-red-600';

  return (
    <div className={`rounded-2xl border p-5 shadow-card transition-all ${cardBg}`}>
      <p className="text-xs font-semibold text-port-muted">{label}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-sm text-slate-400 line-through">{unit === '$' ? `$${baseline.toLocaleString()}` : baseline.toFixed(1)}</span>
        <ArrowRight className="h-3 w-3 text-slate-400" />
        <span className={`text-xl font-bold ${valColor}`}>{unit === '$' ? `$${optimized.toLocaleString()}` : optimized.toFixed(1)}</span>
      </div>
      {diff !== 0 && (
        <p className={`mt-1.5 text-xs font-medium ${diffColor}`}>
          {diff > 0 ? '+' : ''}{unit === '$' ? `$${Math.abs(diff).toLocaleString()}` : diff.toFixed(1)} ({pct > 0 ? '+' : ''}{pct.toFixed(0)}%)
        </p>
      )}
    </div>
  );
}

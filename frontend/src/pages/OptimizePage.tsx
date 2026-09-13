import { useEffect, useState } from 'react';
import { api, OptimizeResponse } from '../api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';

export default function OptimizePage() {
  const [data, setData] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.optimize()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load optimisation</p>;

  const { baseline, optimized } = data.kpis;

  const comparisonData = [
    { metric: 'Avg Wait', baseline: baseline.avg_wait_h, optimised: optimized.avg_wait_h },
    { metric: 'P95 Wait', baseline: baseline.p95_wait_h, optimised: optimized.p95_wait_h },
    { metric: 'Berth Util', baseline: baseline.berth_util_pct, optimised: optimized.berth_util_pct },
    { metric: 'Crane Util', baseline: baseline.crane_util_pct, optimised: optimized.crane_util_pct },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Berth &amp; Crane Optimiser</h2>

      {/* Savings banner */}
      {optimized.cost_saved_usd !== undefined && optimized.cost_saved_usd > 0 && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 text-center">
          <p className="mb-1 text-xs uppercase tracking-wider text-slate-400">Total Estimated Savings</p>
          <span className="text-3xl font-bold text-emerald-400">${optimized.cost_saved_usd.toLocaleString()}</span>
          <p className="mt-1 text-xs text-slate-400">CP-SAT reroutes + wait reduction ({data.solve_ms}ms solve time)</p>
        </div>
      )}

      {/* KPI comparison chart */}
      <div className="rounded-xl border border-port-line bg-port-panel p-4">
        <h3 className="mb-3 text-sm font-medium text-white">Before vs After Comparison</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={comparisonData} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a44" />
            <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#94a3b8' }} />
            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <Tooltip
              contentStyle={{ background: '#111a2c', border: '1px solid #1e2a44', borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: '#e2e8f0' }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="baseline" fill="#64748b" name="Baseline (FCFS)" radius={[3, 3, 0, 0]} />
            <Bar dataKey="optimised" fill="#38bdf8" name="Optimised (CP-SAT)" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* KPI cards row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCompare label="Avg Wait (h)" baseline={baseline.avg_wait_h} optimized={optimized.avg_wait_h} unit="h" lower />
        <KpiCompare label="P95 Wait (h)" baseline={baseline.p95_wait_h} optimized={optimized.p95_wait_h} unit="h" lower />
        <KpiCompare label="Berth Util %" baseline={baseline.berth_util_pct} optimized={optimized.berth_util_pct} unit="%" />
        <KpiCompare label="Demurrage ($)" baseline={baseline.demurrage_cost_usd} optimized={optimized.demurrage_cost_usd} unit="$" lower />
      </div>

      {/* Reroutes */}
      {data.reroutes.length > 0 && (
        <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-port-line px-4 py-3">
            <h3 className="text-sm font-medium text-white">Reroute Recommendations</h3>
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
              {data.reroutes.length} vessel(s) rerouted
            </span>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-port-line">
                <th className="px-3 py-2 text-left text-xs text-slate-400">Vessel</th>
                <th className="px-3 py-2 text-left text-xs text-slate-400">Alt Port</th>
                <th className="px-3 py-2 text-left text-xs text-slate-400">Divert Cost</th>
                <th className="px-3 py-2 text-left text-xs text-slate-400">Saving</th>
                <th className="px-3 py-2 text-left text-xs text-slate-400">Reason</th>
              </tr>
            </thead>
            <tbody>
              {data.reroutes.map((r, i) => (
                <tr key={i} className="border-t border-port-line hover:bg-port-bg/40">
                  <td className="px-3 py-2 text-sm text-white">{r.vessel_id}</td>
                  <td className="px-3 py-2 text-xs text-slate-300">{r.alt_port_id}</td>
                  <td className="px-3 py-2 text-xs text-slate-300">${r.est_cost_usd.toLocaleString()}</td>
                  <td className="px-3 py-2 text-xs font-medium text-emerald-400">+${r.saving_usd.toLocaleString()}</td>
                  <td className="px-3 py-2 text-xs text-slate-400">{r.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Berth assignments Gantt-style */}
      <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-port-line px-4 py-3">
          <h3 className="text-sm font-medium text-white">Berth Assignments</h3>
          <span className="text-xs text-slate-400">{data.assignments.length} assignment(s)</span>
        </div>

        {/* Gantt-style visual */}
        <div className="p-4">
          <div className="space-y-1">
            {data.assignments.map((a, i) => {
              const maxEnd = Math.max(...data.assignments.map((x) => x.end_h), 1);
              const leftPct = (a.start_h / maxEnd) * 100;
              const widthPct = Math.max(2, ((a.end_h - a.start_h) / maxEnd) * 100);
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="w-24 shrink-0 truncate text-xs text-slate-400">{a.vessel_id}</span>
                  <div className="relative h-6 flex-1 rounded bg-port-bg">
                    <div
                      className="absolute inset-y-0 rounded bg-port-accent/60 flex items-center justify-center text-[10px] text-white font-medium"
                      style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                      title={`${a.berth_id} | ${a.crane_count} cranes | ${a.moves_planned} moves`}
                    >
                      {a.berth_id} ({a.crane_count}QC)
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Table */}
        <table className="w-full">
          <thead>
            <tr className="border-t border-port-line">
              <th className="px-3 py-2 text-left text-xs text-slate-400">Vessel</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Berth</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Window</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Cranes</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Moves</th>
            </tr>
          </thead>
          <tbody>
            {data.assignments.map((a, i) => (
              <tr key={i} className="border-t border-port-line hover:bg-port-bg/40">
                <td className="px-3 py-2 text-sm text-white">{a.vessel_id}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{a.berth_id}</td>
                <td className="px-3 py-2 text-xs text-slate-300">h{a.start_h.toFixed(0)}–h{a.end_h.toFixed(0)}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{a.crane_count}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{a.moves_planned}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KpiCompare({ label, baseline, optimized, unit, lower }: {
  label: string; baseline: number; optimized: number; unit: string; lower?: boolean;
}) {
  const diff = optimized - baseline;
  const pct = baseline !== 0 ? ((diff / baseline) * 100) : 0;
  const improved = lower ? diff < 0 : diff > 0;
  const color = improved ? 'text-emerald-400' : diff === 0 ? 'text-slate-400' : 'text-red-400';
  const bgColor = improved ? 'border-emerald-500/20 bg-emerald-500/5' : diff === 0 ? 'border-port-line bg-port-panel' : 'border-red-500/20 bg-red-500/5';

  return (
    <div className={`rounded-xl border p-4 ${bgColor}`}>
      <p className="text-xs text-slate-400">{label}</p>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-sm text-slate-500 line-through">{unit === '$' ? `$${baseline.toLocaleString()}` : `${baseline.toFixed(1)}`}</span>
        <span className="text-xs text-slate-600">→</span>
        <span className="text-lg font-semibold text-white">{unit === '$' ? `$${optimized.toLocaleString()}` : `${optimized.toFixed(1)}`}</span>
      </div>
      {diff !== 0 && (
        <p className={`mt-1 text-xs ${color}`}>
          {diff > 0 ? '+' : ''}{unit === '$' ? `$${Math.abs(diff).toLocaleString()}` : `${diff.toFixed(1)}`}
          {pct !== 0 && ` (${pct > 0 ? '+' : ''}${pct.toFixed(0)}%)`}
        </p>
      )}
    </div>
  );
}

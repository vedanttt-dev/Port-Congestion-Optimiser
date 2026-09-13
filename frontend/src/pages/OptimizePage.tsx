import { useEffect, useState } from 'react';
import { api, OptimizeResponse } from '../api';

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

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Berth &amp; Crane Optimiser</h2>

      <div className="grid gap-4 md:grid-cols-2">
        <KpiCompare label="Avg Wait (h)" baseline={baseline.avg_wait_h} optimized={optimized.avg_wait_h} unit="h" lower />
        <KpiCompare label="P95 Wait (h)" baseline={baseline.p95_wait_h} optimized={optimized.p95_wait_h} unit="h" lower />
        <KpiCompare label="Berth Util %" baseline={baseline.berth_util_pct} optimized={optimized.berth_util_pct} unit="%" />
        <KpiCompare label="Demurrage ($)" baseline={baseline.demurrage_cost_usd} optimized={optimized.demurrage_cost_usd} unit="$" lower />
      </div>

      {optimized.cost_saved_usd !== undefined && optimized.cost_saved_usd > 0 && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4 text-center">
          <span className="text-2xl font-bold text-emerald-400">${optimized.cost_saved_usd.toLocaleString()}</span>
          <p className="text-xs text-slate-400">Total savings (reroutes + wait reduction)</p>
        </div>
      )}

      {data.reroutes.length > 0 && (
        <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
          <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">Reroute Recommendations</h3>
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
                <tr key={i} className="border-t border-port-line">
                  <td className="px-3 py-2 text-sm text-white">{r.vessel_id}</td>
                  <td className="px-3 py-2 text-xs text-slate-300">{r.alt_port_id}</td>
                  <td className="px-3 py-2 text-xs text-slate-300">${r.est_cost_usd.toLocaleString()}</td>
                  <td className="px-3 py-2 text-xs text-emerald-400">${r.saving_usd.toLocaleString()}</td>
                  <td className="px-3 py-2 text-xs text-slate-400">{r.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
        <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">Berth Assignments</h3>
        <table className="w-full">
          <thead>
            <tr className="border-b border-port-line">
              <th className="px-3 py-2 text-left text-xs text-slate-400">Vessel</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Berth</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Window</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Cranes</th>
              <th className="px-3 py-2 text-left text-xs text-slate-400">Moves</th>
            </tr>
          </thead>
          <tbody>
            {data.assignments.map((a, i) => (
              <tr key={i} className="border-t border-port-line">
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
  const improved = lower ? diff < 0 : diff > 0;
  const color = improved ? 'text-emerald-400' : diff === 0 ? 'text-slate-400' : 'text-red-400';

  return (
    <div className="rounded-xl border border-port-line bg-port-panel p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <div className="mt-1 flex items-baseline gap-3">
        <span className="text-lg text-slate-500">{unit === '$' ? `$${baseline.toLocaleString()}` : `${baseline.toFixed(1)}${unit}`}</span>
        <span className="text-xs text-slate-600">→</span>
        <span className="text-lg font-semibold text-white">{unit === '$' ? `$${optimized.toLocaleString()}` : `${optimized.toFixed(1)}${unit}`}</span>
        {diff !== 0 && <span className={`text-xs ${color}`}>{diff > 0 ? '+' : ''}{unit === '$' ? `$${Math.abs(diff).toLocaleString()}` : `${diff.toFixed(1)}${unit}`}</span>}
      </div>
    </div>
  );
}

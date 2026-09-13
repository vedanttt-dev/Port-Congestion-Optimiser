import { useEffect, useState } from 'react';
import { api, PlanResponse } from '../api';

export default function PlanPage() {
  const [data, setData] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.plan()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleExport = () => {
    window.open('/api/plan/export', '_blank');
  };

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load plan</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">72-Hour Shift Plan</h2>
        <button
          onClick={handleExport}
          className="rounded-lg bg-port-accent/10 px-4 py-2 text-sm text-port-accent hover:bg-port-accent/20 transition-colors"
        >
          📥 Export CSV
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {data.shifts.map((shift) => (
          <div key={shift.id} className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
            <div className="flex items-center justify-between border-b border-port-line px-4 py-3">
              <span className="font-medium text-white">{shift.id}</span>
              <span className="text-xs text-slate-400">{shift.window}</span>
            </div>

            {shift.alerts.length > 0 && (
              <div className="border-b border-port-line bg-amber-500/5 px-4 py-2">
                {shift.alerts.map((a, i) => (
                  <p key={i} className="text-xs text-amber-400">⚠️ {a}</p>
                ))}
              </div>
            )}

            <div className="p-4">
              {shift.work_orders.length === 0 ? (
                <p className="text-xs text-slate-500">No work orders</p>
              ) : (
                <div className="space-y-2">
                  {shift.work_orders.map((wo, i) => (
                    <div key={i} className="rounded-lg bg-port-bg/60 px-3 py-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-white">{wo.vessel_id}</span>
                        <span className="text-xs text-slate-400">{wo.berth_id}</span>
                      </div>
                      <div className="mt-1 flex gap-3 text-xs text-slate-400">
                        <span>Cranes: {wo.crane_ids.length}</span>
                        <span>Moves: {wo.target_moves}</span>
                        {wo.priority === 1 && <span className="text-red-400">P1</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {shift.contingency_notes.length > 0 && (
              <div className="border-t border-port-line px-4 py-3">
                <p className="mb-1 text-xs font-medium text-slate-400">Contingencies</p>
                {shift.contingency_notes.map((n, i) => (
                  <p key={i} className="text-xs text-slate-500">• {n}</p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

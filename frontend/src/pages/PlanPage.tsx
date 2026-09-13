import { useEffect, useState } from 'react';
import { api, PlanResponse, ShiftBlock } from '../api';

export default function PlanPage() {
  const [data, setData] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [view, setView] = useState<'cards' | 'timeline'>('cards');

  useEffect(() => {
    api.plan()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    if (data && expanded.size === data.shifts.length) {
      setExpanded(new Set());
    } else if (data) {
      setExpanded(new Set(data.shifts.map((s) => s.id)));
    }
  };

  const handleExport = () => {
    window.open('/api/plan/export', '_blank');
  };

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load plan</p>;

  const totalOrders = data.shifts.reduce((s, sh) => s + sh.work_orders.length, 0);
  const totalAlerts = data.shifts.reduce((s, sh) => s + sh.alerts.length, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">72-Hour Shift Plan</h2>
          <p className="text-xs text-slate-400">
            {data.shifts.length} shifts · {totalOrders} work orders · {totalAlerts} alerts
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="rounded-lg border border-port-line px-3 py-1.5 text-xs text-slate-400 hover:bg-port-panel transition-colors"
          >
            {data && expanded.size === data.shifts.length ? 'Collapse All' : 'Expand All'}
          </button>
          <div className="flex rounded-lg border border-port-line overflow-hidden">
            <button
              onClick={() => setView('cards')}
              className={`px-3 py-1.5 text-xs ${view === 'cards' ? 'bg-port-accent/10 text-port-accent' : 'text-slate-400 hover:bg-port-panel'}`}
            >
              Cards
            </button>
            <button
              onClick={() => setView('timeline')}
              className={`px-3 py-1.5 text-xs ${view === 'timeline' ? 'bg-port-accent/10 text-port-accent' : 'text-slate-400 hover:bg-port-panel'}`}
            >
              Timeline
            </button>
          </div>
          <button
            onClick={handleExport}
            className="rounded-lg bg-port-accent/10 px-3 py-1.5 text-xs text-port-accent hover:bg-port-accent/20 transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Day headers */}
      {view === 'timeline' && (
        <TimelineView shifts={data.shifts} expanded={expanded} toggleExpand={toggleExpand} />
      )}

      {view === 'cards' && (
        <div className="grid gap-4 md:grid-cols-3">
          {data.shifts.map((shift) => (
            <ShiftCard
              key={shift.id}
              shift={shift}
              isExpanded={expanded.has(shift.id)}
              onToggle={() => toggleExpand(shift.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ShiftCard({ shift, isExpanded, onToggle }: {
  shift: ShiftBlock;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const hasAlerts = shift.alerts.length > 0;
  const orderCount = shift.work_orders.length;

  return (
    <div className={`rounded-xl border overflow-hidden transition-colors ${
      hasAlerts ? 'border-amber-500/30 bg-amber-500/5' : 'border-port-line bg-port-panel'
    }`}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-port-bg/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`text-lg font-semibold ${hasAlerts ? 'text-amber-400' : 'text-white'}`}>
            {shift.id}
          </span>
          {hasAlerts && (
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] text-amber-400">
              {shift.alerts.length} alert(s)
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">{orderCount} order(s)</span>
          <span className="text-slate-500">{isExpanded ? '▼' : '▶'}</span>
        </div>
      </button>

      {/* Window bar */}
      <div className="px-4 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500">{shift.window}</span>
          <div className="h-1 flex-1 rounded-full bg-port-bg">
            <div className="h-full rounded-full bg-port-accent/40" style={{ width: `${Math.min(100, orderCount * 20)}%` }} />
          </div>
        </div>
      </div>

      {/* Alerts */}
      {hasAlerts && isExpanded && (
        <div className="border-t border-amber-500/20 px-4 py-2">
          {shift.alerts.map((a, i) => (
            <p key={i} className="text-xs text-amber-400">⚠️ {a}</p>
          ))}
        </div>
      )}

      {/* Work orders */}
      {isExpanded && (
        <div className="border-t border-port-line px-4 py-3">
          {shift.work_orders.length === 0 ? (
            <p className="text-xs text-slate-500">No work orders</p>
          ) : (
            <div className="space-y-2">
              {shift.work_orders.map((wo, i) => (
                <div key={i} className="rounded-lg bg-port-bg/60 px-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">{wo.vessel_id}</span>
                    <div className="flex items-center gap-2">
                      {wo.priority === 1 && (
                        <span className="rounded-full bg-red-500/20 px-1.5 py-0.5 text-[10px] text-red-400">P1</span>
                      )}
                      <span className="text-xs text-slate-400">{wo.berth_id}</span>
                    </div>
                  </div>
                  <div className="mt-1 flex gap-3 text-xs text-slate-400">
                    <span>{wo.crane_ids.length} crane(s)</span>
                    <span>{wo.target_moves} moves</span>
                  </div>
                  {wo.alert && (
                    <p className="mt-1 text-[10px] text-amber-400">{wo.alert}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Contingencies */}
      {isExpanded && shift.contingency_notes.length > 0 && (
        <div className="border-t border-port-line px-4 py-3">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-slate-500">Contingencies</p>
          {shift.contingency_notes.map((n, i) => (
            <p key={i} className="text-xs text-slate-400">• {n}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function TimelineView({ shifts, expanded, toggleExpand }: {
  shifts: ShiftBlock[];
  expanded: Set<string>;
  toggleExpand: (id: string) => void;
}) {
  const days = [1, 2, 3];

  return (
    <div className="space-y-4">
      {days.map((day) => {
        const dayShifts = shifts.filter((s) => s.id.startsWith(`D${day}`));
        return (
          <div key={day} className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
            <div className="border-b border-port-line px-4 py-3">
              <h3 className="text-sm font-medium text-white">Day {day}</h3>
            </div>

            {/* Timeline bar */}
            <div className="px-4 py-3">
              <div className="flex h-12 gap-0.5">
                {dayShifts.map((shift) => {
                  const workCount = shift.work_orders.length;
                  const hasAlerts = shift.alerts.length > 0;
                  return (
                    <button
                      key={shift.id}
                      onClick={() => toggleExpand(shift.id)}
                      className={`flex flex-col items-center justify-center rounded transition-colors ${
                        expanded.has(shift.id) ? 'ring-1 ring-port-accent' : ''
                      } ${
                        hasAlerts ? 'bg-amber-500/20 hover:bg-amber-500/30' :
                        workCount > 0 ? 'bg-port-accent/20 hover:bg-port-accent/30' :
                        'bg-port-bg hover:bg-port-bg/80'
                      }`}
                      style={{ flex: 1 }}
                    >
                      <span className="text-[10px] font-medium text-white">{shift.id}</span>
                      <span className="text-[10px] text-slate-400">{workCount} orders</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Expanded details */}
            {dayShifts.some((s) => expanded.has(s.id)) && (
              <div className="border-t border-port-line divide-y divide-port-line">
                {dayShifts.filter((s) => expanded.has(s.id)).map((shift) => (
                  <div key={shift.id} className="px-4 py-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-medium text-white">{shift.id}</span>
                      <span className="text-xs text-slate-400">{shift.window}</span>
                    </div>

                    {shift.work_orders.length === 0 ? (
                      <p className="text-xs text-slate-500">No work orders</p>
                    ) : (
                      <div className="space-y-1">
                        {shift.work_orders.map((wo, i) => (
                          <div key={i} className="flex items-center gap-3 rounded bg-port-bg/60 px-3 py-1.5 text-xs">
                            <span className="text-white">{wo.vessel_id}</span>
                            <span className="text-slate-400">{wo.berth_id}</span>
                            <span className="text-slate-500">{wo.crane_ids.length} cranes</span>
                            <span className="text-slate-500">{wo.target_moves} moves</span>
                            {wo.priority === 1 && <span className="text-red-400">P1</span>}
                          </div>
                        ))}
                      </div>
                    )}

                    {shift.contingency_notes.length > 0 && (
                      <div className="mt-2">
                        <p className="mb-0.5 text-[10px] text-slate-500">Contingencies:</p>
                        {shift.contingency_notes.map((n, i) => (
                          <p key={i} className="text-[10px] text-slate-400">• {n}</p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { api, PlanResponse, ShiftBlock, downloadFile } from '../api';
import { Download, ChevronDown, ChevronRight, AlertTriangle, LayoutGrid, GanttChart } from 'lucide-react';

export default function PlanPage() {
  const [data, setData] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [view, setView] = useState<'cards' | 'timeline'>('cards');

  useEffect(() => { api.plan().then(setData).catch(console.error).finally(() => setLoading(false)); }, []);

  const toggle = (id: string) => setExpanded((p) => { const n = new Set(p); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const expandAll = () => { if (data) setExpanded(expanded.size === data.shifts.length ? new Set() : new Set(data.shifts.map((s) => s.id))); };

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="grid gap-5 md:grid-cols-3">{[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="skeleton h-40 rounded-2xl" />)}</div>
    </div>
  );
  if (!data) return <p className="text-red-600 font-medium">Failed to load plan</p>;

  const totalOrders = data.shifts.reduce((s, sh) => s + sh.work_orders.length, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-port-text">72-Hour Shift Plan</h2>
          <p className="mt-1 text-sm text-port-muted">{data.shifts.length} shifts, {totalOrders} work orders across 3 days</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={expandAll} className="rounded-xl border border-port-line bg-port-panel px-3 py-2 text-xs font-medium text-port-muted shadow-card hover:bg-port-panelHover transition-all">
            {expanded.size === data.shifts.length ? 'Collapse All' : 'Expand All'}
          </button>
          <div className="flex rounded-xl border border-port-line bg-port-panel shadow-card overflow-hidden">
            <button onClick={() => setView('cards')} className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-all ${view === 'cards' ? 'bg-brand-600 text-white' : 'text-port-muted hover:bg-port-panelHover'}`}>
              <LayoutGrid className="h-3.5 w-3.5" /> Cards
            </button>
            <button onClick={() => setView('timeline')} className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-all ${view === 'timeline' ? 'bg-brand-600 text-white' : 'text-port-muted hover:bg-port-panelHover'}`}>
              <GanttChart className="h-3.5 w-3.5" /> Timeline
            </button>
          </div>
          <button onClick={() => downloadFile('/export/plan', 'shift_plan.csv')} className="inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-600 px-4 py-2 text-xs font-medium text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 hover:shadow-md">
            <Download className="h-3.5 w-3.5" /> Export CSV
          </button>
        </div>
      </div>

      {view === 'timeline' && (
        <div className="space-y-4">
          {[1, 2, 3].map((day) => (
            <div key={day} className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
              <div className="border-b border-port-line px-5 py-3.5 bg-slate-50/80">
                <h3 className="text-sm font-semibold text-port-text">Day {day}</h3>
              </div>
              <div className="flex h-14 gap-1 p-4">
                {data.shifts.filter((s) => s.id.startsWith(`D${day}`)).map((shift) => (
                  <button key={shift.id} onClick={() => toggle(shift.id)}
                    className={`flex flex-col items-center justify-center rounded-xl transition-all flex-1 ${
                      expanded.has(shift.id) ? 'ring-2 ring-brand-400 shadow-glow' : ''
                    } ${shift.alerts.length > 0 ? 'bg-amber-50 border border-amber-200' : shift.work_orders.length > 0 ? 'bg-brand-50 border border-brand-200' : 'bg-slate-50 border border-slate-200'}`}>
                    <span className="text-[10px] font-bold text-port-text">{shift.id}</span>
                    <span className="text-[10px] text-port-muted">{shift.work_orders.length} orders</span>
                  </button>
                ))}
              </div>
              {dayShiftsExpanded(data.shifts, day, expanded) && (
                <div className="border-t border-port-line divide-y divide-port-line">
                  {data.shifts.filter((s) => s.id.startsWith(`D${day}`) && expanded.has(s.id)).map((shift) => (
                    <div key={shift.id} className="px-5 py-4">
                      <div className="mb-2.5 flex items-center justify-between">
                        <span className="font-semibold text-port-text">{shift.id}</span>
                        <span className="rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-600">{shift.window}</span>
                      </div>
                      {shift.work_orders.length === 0 ? <p className="text-xs text-port-muted">No work orders</p> : (
                        <div className="space-y-1.5">
                          {shift.work_orders.map((wo, i) => (
                            <div key={i} className="flex items-center gap-3 rounded-xl bg-slate-50 border border-slate-200 px-3 py-2 text-xs">
                              <span className="font-medium text-port-text">{wo.vessel_id}</span>
                              <span className="text-slate-500">{wo.berth_id}</span>
                              <span className="text-slate-500">{wo.crane_ids.length} cranes</span>
                              <span className="text-slate-500">{wo.target_moves} moves</span>
                              {wo.priority === 1 && <span className="rounded-full bg-red-50 text-red-700 border border-red-200 px-1.5 py-0.5 font-medium">P1</span>}
                            </div>
                          ))}
                        </div>
                      )}
                      {shift.contingency_notes.length > 0 && (
                        <div className="mt-2.5 space-y-0.5">
                          {shift.contingency_notes.map((n, i) => <p key={i} className="text-[11px] text-slate-500">&bull; {n}</p>)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {view === 'cards' && (
        <div className="grid gap-5 md:grid-cols-3">
          {data.shifts.map((shift) => {
            const isExpanded = expanded.has(shift.id);
            const hasAlerts = shift.alerts.length > 0;
            return (
              <div key={shift.id} className={`rounded-2xl border overflow-hidden shadow-card transition-all ${
                hasAlerts ? 'border-amber-200 bg-amber-50/30' : 'border-port-line bg-port-panel'
              }`}>
                <button onClick={() => toggle(shift.id)} className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-port-panelHover/50 transition-colors">
                  <div className="flex items-center gap-2">
                    {hasAlerts && <AlertTriangle className="h-4 w-4 text-amber-500" />}
                    <span className={`font-semibold ${hasAlerts ? 'text-amber-700' : 'text-port-text'}`}>{shift.id}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-slate-100 border border-slate-200 px-2 py-0.5 text-[10px] font-medium text-slate-600">{shift.work_orders.length} orders</span>
                    {isExpanded ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
                  </div>
                </button>
                {isExpanded && (
                  <>
                    {shift.alerts.length > 0 && (
                      <div className="border-t border-amber-200 px-5 py-2.5 bg-amber-50/50">
                        {shift.alerts.map((a, i) => <p key={i} className="text-xs text-amber-700">{a}</p>)}
                      </div>
                    )}
                    <div className="border-t border-port-line px-5 py-4">
                      {shift.work_orders.length === 0 ? <p className="text-xs text-port-muted">No work orders</p> : (
                        <div className="space-y-2">
                          {shift.work_orders.map((wo, i) => (
                            <div key={i} className="rounded-xl bg-slate-50 border border-slate-200 px-3.5 py-2.5">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-port-text">{wo.vessel_id}</span>
                                <span className="text-xs text-slate-500">{wo.berth_id}</span>
                              </div>
                              <div className="mt-1.5 flex gap-3 text-xs text-slate-500">
                                <span>{wo.crane_ids.length} crane(s)</span>
                                <span>{wo.target_moves} moves</span>
                                {wo.priority === 1 && <span className="font-medium text-red-600">P1</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    {shift.contingency_notes.length > 0 && (
                      <div className="border-t border-port-line px-5 py-4 bg-slate-50/50">
                        <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Contingencies</p>
                        {shift.contingency_notes.map((n, i) => <p key={i} className="text-xs text-slate-600">&bull; {n}</p>)}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function dayShiftsExpanded(shifts: ShiftBlock[], day: number, expanded: Set<string>) {
  return shifts.some((s) => s.id.startsWith(`D${day}`) && expanded.has(s.id));
}

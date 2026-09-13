import { useEffect, useState } from 'react';
import { api, KpisResponse, PredictResponse, downloadFile } from '../api';
import { Download, Clock, BarChart3, Ship, DollarSign, AlertTriangle } from 'lucide-react';

export default function OverviewPage() {
  const [kpis, setKpis] = useState<KpisResponse | null>(null);
  const [predict, setPredict] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.kpis(), api.predict()])
      .then(([k, p]) => { setKpis(k); setPredict(p); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-28 rounded-2xl" />)}
      </div>
      <div className="skeleton h-40 rounded-2xl" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-port-text">Dashboard Overview</h2>
          <p className="mt-1 text-sm text-port-muted">Key performance indicators at a glance</p>
        </div>
        <button
          onClick={() => downloadFile('/export/report', 'port_congestion_report.txt')}
          className="inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 hover:shadow-md"
        >
          <Download className="h-4 w-4" />
          Export Report
        </button>
      </div>

      {kpis && (
        <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
          <KpiCard icon={Clock} label="Avg Wait" value={`${kpis.avg_wait_h.toFixed(1)}h`} color="text-brand-600" bg="bg-brand-50" />
          <KpiCard icon={BarChart3} label="P95 Wait" value={`${kpis.p95_wait_h.toFixed(1)}h`} color="text-amber-600" bg="bg-amber-50" />
          <KpiCard icon={Ship} label="Berth Utilisation" value={`${kpis.berth_util_pct.toFixed(0)}%`} color="text-emerald-600" bg="bg-emerald-50" />
          <KpiCard icon={DollarSign} label="Demurrage Cost" value={`$${kpis.demurrage_cost_usd.toLocaleString()}`} color="text-red-600" bg="bg-red-50" />
        </div>
      )}

      {predict && predict.hotspots.length > 0 && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-5">
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <h3 className="font-semibold text-amber-800">Active Hotspots ({predict.hotspots.length})</h3>
          </div>
          <div className="space-y-2">
            {predict.hotspots.map((h) => (
              <div key={h.id} className="flex items-center gap-3 rounded-xl bg-white/80 border border-amber-100 px-4 py-2.5 text-sm">
                <span className={`h-2 w-2 shrink-0 rounded-full ${h.severity === 'high' ? 'bg-red-500' : 'bg-amber-500'}`} />
                <span className="text-slate-700">{h.message}</span>
                <span className="ml-auto text-xs text-slate-500">Lead: {h.lead_time_h}h</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, color, bg }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  color: string;
  bg: string;
}) {
  return (
    <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card transition-shadow hover:shadow-card-hover">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${bg}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
        <div>
          <p className="text-xs font-medium text-port-muted">{label}</p>
          <p className="mt-0.5 text-2xl font-bold text-port-text">{value}</p>
        </div>
      </div>
    </div>
  );
}

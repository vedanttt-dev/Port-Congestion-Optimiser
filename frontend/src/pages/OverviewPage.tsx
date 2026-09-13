import { useEffect, useState } from 'react';
import { api, KpisResponse, PredictResponse } from '../api';

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

  if (loading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Dashboard Overview</h2>

      {kpis && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <KpiCard label="Avg Wait" value={`${kpis.avg_wait_h.toFixed(1)}h`} />
          <KpiCard label="P95 Wait" value={`${kpis.p95_wait_h.toFixed(1)}h`} />
          <KpiCard label="Berth Util" value={`${kpis.berth_util_pct.toFixed(0)}%`} />
          <KpiCard label="Demurrage" value={`$${kpis.demurrage_cost_usd.toLocaleString()}`} />
        </div>
      )}

      {predict && predict.hotspots.length > 0 && (
        <div className="rounded-xl border border-port-line bg-port-panel p-4">
          <h3 className="mb-3 font-medium text-white">Active Hotspots</h3>
          <div className="space-y-2">
            {predict.hotspots.map((h) => (
              <div key={h.id} className="flex items-center gap-3 rounded-lg bg-port-bg/60 px-3 py-2 text-sm">
                <span className={`h-2 w-2 rounded-full ${h.severity === 'high' ? 'bg-red-400' : 'bg-amber-400'}`} />
                <span className="text-slate-300">{h.message}</span>
                <span className="ml-auto text-xs text-slate-500">Lead: {h.lead_time_h}h</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-port-line bg-port-panel p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-8 w-48 animate-pulse rounded bg-port-panel" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-port-panel" />
        ))}
      </div>
    </div>
  );
}

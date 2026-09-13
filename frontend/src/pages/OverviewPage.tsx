import { useEffect, useState } from 'react';
import { api, KpisResponse, downloadFile } from '../api';
import { FileText, Clock, BarChart3, Ship, DollarSign } from 'lucide-react';

export default function OverviewPage() {
  const [kpis, setKpis] = useState<KpisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.kpis()
      .then(setKpis)
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
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-port-text sm:text-2xl">Dashboard Overview</h2>
          <p className="mt-1 text-sm text-white/80">Key performance indicators at a glance</p>
        </div>
        <button
          onClick={() => downloadFile('/export/report-pdf', 'port_congestion_report.pdf')}
          className="inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 hover:shadow-md"
        >
          <FileText className="h-4 w-4" />
          Download PDF
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
    <div className="rounded-2xl border border-white/20 bg-white/50 p-5 shadow-card backdrop-blur-sm transition-shadow hover:shadow-card-hover">
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

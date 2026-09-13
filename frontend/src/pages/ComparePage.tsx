import { useEffect, useState } from 'react';
import { api, ScenarioSummary, ScenarioCompareResponse } from '../api';
import {
  GitCompareArrows,
  ArrowRight,
  ArrowLeft,
  BarChart3,
  Clock,
  Ship,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Minus,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export default function ComparePage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectA, setSelectA] = useState('');
  const [selectB, setSelectB] = useState('');
  const [result, setResult] = useState<ScenarioCompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.scenarioList()
      .then((list) => {
        setScenarios(list);
        if (list.length >= 2) {
          const aName = list.find((s) => s.name === 'default')?.name ?? list[0].name;
          const bName = list.find((s) => s.name === 'light_traffic')?.name ?? list[1].name;
          setSelectA(aName);
          setSelectB(bName);
          // Auto-compare default vs light_traffic
          if (aName && bName && aName !== bName) {
            api.scenarioCompare(aName, bName).then(setResult).catch(console.error);
          }
        } else if (list.length === 1) {
          setSelectA(list[0].name);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleCompare = async () => {
    if (!selectA || !selectB || selectA === selectB) {
      setError('Select two different scenarios to compare');
      return;
    }
    setComparing(true);
    setError('');
    try {
      const res = await api.scenarioCompare(selectA, selectB);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to compare');
    } finally {
      setComparing(false);
    }
  };

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="skeleton h-32 rounded-2xl" />
      <div className="skeleton h-72 rounded-2xl" />
    </div>
  );

  const chartData = result ? [
    { metric: 'Avg Wait (h)', a: result.scenario_a.kpis.avg_wait_h, b: result.scenario_b.kpis.avg_wait_h },
    { metric: 'P95 Wait (h)', a: result.scenario_a.kpis.p95_wait_h, b: result.scenario_b.kpis.p95_wait_h },
    { metric: 'Berth Util (%)', a: result.scenario_a.kpis.berth_util_pct, b: result.scenario_b.kpis.berth_util_pct },
    { metric: 'Yard Util (%)', a: result.scenario_a.kpis.yard_util_pct, b: result.scenario_b.kpis.yard_util_pct },
  ] : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-port-text">What-If Comparison</h2>
        <p className="mt-1 text-sm text-port-muted">Compare two scenarios side by side to see the impact of changes</p>
      </div>

      {/* Selector bar */}
      <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="mb-1 block text-xs font-semibold text-port-muted">Scenario A</label>
            <select
              value={selectA}
              onChange={(e) => setSelectA(e.target.value)}
              className="w-full rounded-xl border border-port-line bg-port-bg px-3.5 py-2.5 text-sm text-port-text focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            >
              {scenarios.map((s) => <option key={s.name} value={s.name}>{s.name} ({s.num_vessels} vessels)</option>)}
            </select>
          </div>

          <div className="flex flex-col items-center gap-1 pt-5">
            <ArrowRight className="h-5 w-5 text-slate-400" />
            <ArrowLeft className="h-5 w-5 text-slate-400" />
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="mb-1 block text-xs font-semibold text-port-muted">Scenario B</label>
            <select
              value={selectB}
              onChange={(e) => setSelectB(e.target.value)}
              className="w-full rounded-xl border border-port-line bg-port-bg px-3.5 py-2.5 text-sm text-port-text focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            >
              {scenarios.map((s) => <option key={s.name} value={s.name}>{s.name} ({s.num_vessels} vessels)</option>)}
            </select>
          </div>

          <button
            onClick={handleCompare}
            disabled={comparing || !selectA || !selectB || selectA === selectB}
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 disabled:opacity-50 mt-5"
          >
            <GitCompareArrows className="h-4 w-4" />
            {comparing ? 'Comparing...' : 'Compare'}
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-600">{error}</div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* KPI cards */}
          <div className="grid gap-5 md:grid-cols-2">
            <ScenarioCard
              label="A"
              name={result.scenario_a.name}
              kpis={result.scenario_a.kpis}
              meta={result.scenario_a.meta}
              color="brand"
            />
            <ScenarioCard
              label="B"
              name={result.scenario_b.name}
              kpis={result.scenario_b.kpis}
              meta={result.scenario_b.meta}
              color="emerald"
            />
          </div>

          {/* Delta summary */}
          <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-port-text">
              <TrendingDown className="h-4 w-4 text-brand-600" />
              Impact Summary (A → B)
            </h3>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {Object.entries(result.deltas_pct).map(([key, delta]) => {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                const isLowerBetter = key.includes('wait') || key.includes('cost') || key.includes('demurrage') || key.includes('queue');
                const improved = isLowerBetter ? delta < 0 : delta > 0;
                const Icon = delta < 0 ? TrendingDown : delta > 0 ? TrendingUp : Minus;
                return (
                  <div key={key} className={`rounded-xl border p-4 ${
                    delta === 0 ? 'border-port-line bg-port-bg' :
                    improved ? 'border-emerald-200 bg-emerald-50/50' : 'border-red-200 bg-red-50/50'
                  }`}>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-port-muted">{label}</p>
                    <div className="mt-1 flex items-center gap-2">
                      <Icon className={`h-4 w-4 ${delta === 0 ? 'text-slate-400' : improved ? 'text-emerald-600' : 'text-red-600'}`} />
                      <span className={`text-lg font-bold ${delta === 0 ? 'text-slate-500' : improved ? 'text-emerald-700' : 'text-red-700'}`}>
                        {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chart */}
          <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-port-text">
              <BarChart3 className="h-4 w-4 text-brand-600" />
              KPI Comparison
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="a" fill="#64748b" name={result.scenario_a.name} radius={[4, 4, 0, 0]} />
                <Bar dataKey="b" fill="#2563eb" name={result.scenario_b.name} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

function ScenarioCard({ label, name, kpis, meta, color }: {
  label: string;
  name: string;
  kpis: { avg_wait_h: number; p95_wait_h: number; berth_util_pct: number; demurrage_cost_usd: number; yard_util_pct: number };
  meta: Record<string, unknown>;
  color: string;
}) {
  const borderColor = color === 'brand' ? 'border-brand-200' : 'border-emerald-200';
  const bgColor = color === 'brand' ? 'bg-brand-50/50' : 'bg-emerald-50/50';
  const labelBg = color === 'brand' ? 'bg-brand-600' : 'bg-emerald-600';

  return (
    <div className={`rounded-2xl border ${borderColor} ${bgColor} p-5 shadow-card`}>
      <div className="flex items-center gap-3 mb-4">
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${labelBg} text-sm font-bold text-white`}>{label}</span>
        <div>
          <h4 className="text-sm font-bold text-port-text">{name}</h4>
          <p className="text-xs text-port-muted">{String(meta.num_vessels ?? '?')} vessels, {String(meta.num_berths ?? '?')} berths, seed={String(meta.seed ?? '?')}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <MiniKpi icon={Clock} label="Avg Wait" value={`${kpis.avg_wait_h}h`} />
        <MiniKpi icon={BarChart3} label="P95 Wait" value={`${kpis.p95_wait_h}h`} />
        <MiniKpi icon={Ship} label="Berth Util" value={`${kpis.berth_util_pct}%`} />
        <MiniKpi icon={DollarSign} label="Demurrage" value={`$${kpis.demurrage_cost_usd.toLocaleString()}`} />
      </div>
    </div>
  );
}

function MiniKpi({ icon: Icon, label, value }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-white/80 border border-port-line px-3 py-2">
      <div className="flex items-center gap-1.5">
        <Icon className="h-3 w-3 text-port-muted" />
        <span className="text-[10px] font-semibold text-port-muted">{label}</span>
      </div>
      <span className="text-sm font-bold text-port-text">{value}</span>
    </div>
  );
}

import { useEffect, useState } from 'react';
import {
  api,
  ScenarioSummary,
  ScenarioGenerateRequest,
  KpisResponse,
} from '../api';
import {
  Beaker,
  Play,
  RotateCcw,
  Trash2,
  BarChart3,
  Clock,
  Ship,
  DollarSign,
  Settings2,
  Zap,
  AlertCircle,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function ScenarioPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [active, setActive] = useState<string>('default');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeKpis, setActiveKpis] = useState<KpisResponse | null>(null);

  // Form state
  const [form, setForm] = useState<ScenarioGenerateRequest>({
    name: '',
    seed: 42,
    weeks: 4,
    num_berths: 8,
    num_cranes: 25,
  });
  const [formError, setFormError] = useState('');

  const loadScenarios = () => {
    api.scenarioList().then(setScenarios).catch(console.error);
  };

  useEffect(() => {
    Promise.all([api.scenarioList(), api.kpis()])
      .then(([list, kpis]) => {
        setScenarios(list);
        setActiveKpis(kpis);
        if (list.length > 0) setActive(list[0].name);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleGenerate = async () => {
    if (!form.name.trim()) {
      setFormError('Scenario name is required');
      return;
    }
    setGenerating(true);
    setFormError('');
    try {
      await api.scenarioGenerate(form);
      const list = await api.scenarioList();
      setScenarios(list);
      setActive(form.name);
      // Load KPIs for the new scenario
      const result = await api.scenarioKpis(form.name);
      setActiveKpis(result.kpis);
      setForm({ name: '', seed: Math.floor(Math.random() * 999999), weeks: 4, num_berths: 8, num_cranes: 25 });
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : 'Failed to generate scenario');
    } finally {
      setGenerating(false);
    }
  };

  const handleActivate = async (name: string) => {
    try {
      await api.scenarioSetActive(name);
      setActive(name);
      const result = await api.scenarioKpis(name);
      setActiveKpis(result.kpis);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (name: string) => {
    if (name === 'default') return;
    try {
      await api.scenarioDelete(name);
      loadScenarios();
      if (active === name) setActive('default');
    } catch (e) {
      console.error(e);
    }
  };

  const presetScenarios = [
    { label: 'Light Traffic', desc: '2 weeks, 6 berths', seed: 123, weeks: 2, num_berths: 6, num_cranes: 18 },
    { label: 'Normal Ops', desc: '4 weeks, 8 berths (default)', seed: 42, weeks: 4, num_berths: 8, num_cranes: 25 },
    { label: 'Heavy Surge', desc: '6 weeks, 8 berths', seed: 777, weeks: 6, num_berths: 8, num_cranes: 25 },
    { label: 'Crane Shortage', desc: '4 weeks, 8 berths, 12 cranes', seed: 42, weeks: 4, num_berths: 8, num_cranes: 12 },
    { label: 'Capacity Crunch', desc: '4 weeks, 5 berths', seed: 42, weeks: 4, num_berths: 5, num_cranes: 15 },
  ];

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="grid gap-5 md:grid-cols-2"><div className="skeleton h-96 rounded-2xl" /><div className="skeleton h-96 rounded-2xl" /></div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-port-text">Scenario Builder</h2>
        <p className="mt-1 text-sm text-port-muted">Generate what-if scenarios with custom parameters and compare results</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Form */}
        <div className="space-y-5 lg:col-span-1">
          {/* Quick presets */}
          <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-port-text">
              <Zap className="h-4 w-4 text-amber-500" />
              Quick Presets
            </h3>
            <div className="space-y-2">
              {presetScenarios.map((p) => (
                <button
                  key={p.label}
                  onClick={() => setForm({ ...form, name: p.label.toLowerCase().replace(/\s+/g, '_'), seed: p.seed, weeks: p.weeks, num_berths: p.num_berths, num_cranes: p.num_cranes })}
                  className="w-full rounded-xl border border-port-line px-3 py-2.5 text-left transition-all hover:border-brand-300 hover:bg-brand-50"
                >
                  <span className="text-sm font-medium text-port-text">{p.label}</span>
                  <span className="ml-2 text-xs text-port-muted">{p.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Custom form */}
          <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-port-text">
              <Settings2 className="h-4 w-4 text-brand-600" />
              Custom Scenario
            </h3>

            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-port-muted">Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. stress_test_q4"
                  className="w-full rounded-xl border border-port-line bg-port-bg px-3.5 py-2.5 text-sm text-port-text placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-port-muted">Random Seed</label>
                <input
                  type="number"
                  value={form.seed}
                  onChange={(e) => setForm({ ...form, seed: Number(e.target.value) })}
                  className="w-full rounded-xl border border-port-line bg-port-bg px-3.5 py-2.5 text-sm text-port-text focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-port-muted">Weeks: {form.weeks}</label>
                <input
                  type="range"
                  min={1}
                  max={12}
                  value={form.weeks}
                  onChange={(e) => setForm({ ...form, weeks: Number(e.target.value) })}
                  className="w-full accent-brand-600"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-port-muted">Berths: {form.num_berths}</label>
                <input
                  type="range"
                  min={3}
                  max={16}
                  value={form.num_berths ?? 8}
                  onChange={(e) => setForm({ ...form, num_berths: Number(e.target.value) })}
                  className="w-full accent-brand-600"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-port-muted">Cranes: {form.num_cranes}</label>
                <input
                  type="range"
                  min={4}
                  max={40}
                  value={form.num_cranes ?? 25}
                  onChange={(e) => setForm({ ...form, num_cranes: Number(e.target.value) })}
                  className="w-full accent-brand-600"
                />
              </div>

              {formError && (
                <div className="flex items-center gap-2 rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-600">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {formError}
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <RotateCcw className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Beaker className="h-4 w-4" />
                    Generate Scenario
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Results */}
        <div className="space-y-5 lg:col-span-2">
          {/* Scenario list */}
          <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
            <div className="flex items-center justify-between border-b border-port-line px-5 py-3.5">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-port-text">
                <Beaker className="h-4 w-4 text-brand-600" />
                Saved Scenarios ({scenarios.length})
              </h3>
            </div>
            <div className="divide-y divide-port-line max-h-[400px] overflow-y-auto">
              {scenarios.map((s) => (
                <div
                  key={s.name}
                  className={`flex items-center gap-4 px-5 py-3 transition-colors ${
                    active === s.name ? 'bg-brand-50 border-l-4 border-l-brand-600' : 'hover:bg-port-panelHover border-l-4 border-l-transparent'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-port-text">{s.name}</span>
                      {active === s.name && (
                        <span className="rounded-full bg-brand-100 border border-brand-200 px-2 py-0.5 text-[10px] font-semibold text-brand-700">ACTIVE</span>
                      )}
                    </div>
                    <div className="mt-0.5 flex gap-4 text-xs text-port-muted">
                      <span>{s.num_vessels} vessels</span>
                      <span>{s.num_berths} berths</span>
                      <span>{s.num_cranes} cranes</span>
                      <span>seed={s.seed}</span>
                    </div>
                    {s.avg_wait_h != null && (
                      <div className="mt-1 flex gap-4 text-xs">
                        <span className="text-slate-600">Wait: <strong className="text-port-text">{s.avg_wait_h}h</strong></span>
                        <span className="text-slate-600">Demurrage: <strong className="text-port-text">${(s.demurrage_usd ?? 0).toLocaleString()}</strong></span>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleActivate(s.name)}
                      className="rounded-lg border border-port-line bg-port-panel px-3 py-1.5 text-xs font-medium text-port-muted hover:bg-brand-50 hover:text-brand-600 hover:border-brand-200 transition-all"
                    >
                      <Play className="h-3.5 w-3.5" />
                    </button>
                    {s.name !== 'default' && (
                      <button
                        onClick={() => handleDelete(s.name)}
                        className="rounded-lg border border-port-line bg-port-panel px-3 py-1.5 text-xs font-medium text-port-muted hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active scenario KPIs */}
          {activeKpis && (
            <div className="rounded-2xl border border-port-line bg-port-panel p-5 shadow-card">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-port-text">
                <BarChart3 className="h-4 w-4 text-brand-600" />
                Active Scenario KPIs
              </h3>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <KpiMini icon={Clock} label="Avg Wait" value={`${activeKpis.avg_wait_h.toFixed(1)}h`} color="text-brand-600" />
                <KpiMini icon={Ship} label="Berth Util" value={`${activeKpis.berth_util_pct.toFixed(0)}%`} color="text-emerald-600" />
                <KpiMini icon={BarChart3} label="P95 Wait" value={`${activeKpis.p95_wait_h.toFixed(1)}h`} color="text-amber-600" />
                <KpiMini icon={DollarSign} label="Demurrage" value={`$${activeKpis.demurrage_cost_usd.toLocaleString()}`} color="text-red-600" />
              </div>

              <ResponsiveContainer width="100%" height={200} className="mt-4">
                <BarChart data={[
                  { name: 'Avg Wait', value: activeKpis.avg_wait_h },
                  { name: 'P95 Wait', value: activeKpis.p95_wait_h },
                  { name: 'Berth Util', value: activeKpis.berth_util_pct },
                  { name: 'Yard Util', value: activeKpis.yard_util_pct },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
                  <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiMini({ icon: Icon, label, value, color }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-port-line bg-port-bg p-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon className={`h-3.5 w-3.5 ${color}`} />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-port-muted">{label}</span>
      </div>
      <span className="text-lg font-bold text-port-text">{value}</span>
    </div>
  );
}

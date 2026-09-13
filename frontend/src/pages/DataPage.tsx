import { useEffect, useState } from 'react';
import { api, DataSummary, downloadFile } from '../api';
import { Search, Download, ArrowUpDown, Container, Anchor, Truck, Globe } from 'lucide-react';

type SortDir = 'asc' | 'desc';

export default function DataPage() {
  const [data, setData] = useState<DataSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  useEffect(() => {
    api.data().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleSort = (col: string) => {
    if (sortCol === col) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortCol(col); setSortDir('asc'); }
  };

  const match = (text: string) => search === '' || text.toLowerCase().includes(search.toLowerCase());

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48 rounded-lg" />
      <div className="skeleton h-12 rounded-xl" />
      <div className="grid gap-5 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-64 rounded-2xl" />)}
      </div>
    </div>
  );

  if (!data) return <p className="text-red-600 font-medium">Failed to load data</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-port-text sm:text-2xl">Scenario Data</h2>
          <p className="mt-1 text-sm text-port-muted">Vessels, berths, cranes and yard inventory</p>
        </div>
        <button
          onClick={() => downloadFile('/export/data', 'vessels.csv')}
          className="inline-flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-700 hover:shadow-md"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-port-muted" />
        <input
          type="text"
          placeholder="Search vessels, berths, cranes, zones..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-port-line bg-port-panel py-3 pl-10 pr-4 text-sm text-port-text shadow-card placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 transition-all"
        />
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {/* Vessels */}
        <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
            <Container className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Vessels ({data.vessels.length})</h3>
          </div>
          <div className="max-h-80 overflow-x-auto overflow-y-auto">
            <table className="w-full min-w-[400px]">
              <thead>
                <tr className="border-b border-port-line bg-slate-50/80">
                  {['id', 'name', 'type', 'teu', 'priority'].map((c) => (
                    <th key={c} onClick={() => handleSort(c)} className="cursor-pointer px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 hover:text-port-text transition-colors">
                      <span className="inline-flex items-center gap-1">
                        {c}
                        <ArrowUpDown className="h-3 w-3" />
                        {sortCol === c ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-port-line">
                {data.vessels.filter((v) => match(`${v.id} ${v.name} ${v.type}`)).map((v) => (
                  <tr key={v.id} className="hover:bg-port-panelHover transition-colors">
                    <td className="px-4 py-2.5 text-xs font-medium text-slate-500">{v.id}</td>
                    <td className="px-4 py-2.5 text-sm font-medium text-port-text">{v.name}</td>
                    <td className="px-4 py-2.5">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        v.type === 'mega' ? 'bg-purple-50 text-purple-700 border border-purple-200' :
                        v.type === 'medium' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                        'bg-slate-50 text-slate-600 border border-slate-200'
                      }`}>{v.type}</span>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-600">{v.teu_capacity.toLocaleString()}</td>
                    <td className="px-4 py-2.5">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        v.priority === 1 ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-50 text-slate-600 border border-slate-200'
                      }`}>P{v.priority}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Berths */}
        <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
            <Anchor className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Berths ({data.berths.length})</h3>
          </div>
          <div className="max-h-80 overflow-x-auto overflow-y-auto">
            <table className="w-full min-w-[350px]">
              <thead>
                <tr className="border-b border-port-line bg-slate-50/80">
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">ID</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Length</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Draft</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Cranes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-port-line">
                {data.berths.map((b) => (
                  <tr key={b.id} className="hover:bg-port-panelHover transition-colors">
                    <td className="px-4 py-2.5 text-xs font-medium text-slate-500">{b.id}</td>
                    <td className="px-4 py-2.5 text-sm text-port-text">{b.length_m}m</td>
                    <td className="px-4 py-2.5 text-sm text-port-text">{b.max_draft_m}m</td>
                    <td className="px-4 py-2.5 text-sm text-port-text">{b.crane_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Cranes */}
        <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
            <Truck className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Cranes ({data.cranes.length})</h3>
          </div>
          <div className="max-h-80 overflow-x-auto overflow-y-auto">
            <table className="w-full min-w-[400px]">
              <thead>
                <tr className="border-b border-port-line bg-slate-50/80">
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">ID</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Moves/h</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Compatible Berths</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-port-line">
                {data.cranes.map((c) => (
                  <tr key={c.id} className="hover:bg-port-panelHover transition-colors">
                    <td className="px-4 py-2.5 text-xs font-medium text-slate-500">{c.id}</td>
                    <td className="px-4 py-2.5 text-sm text-port-text">{c.max_moves_per_hr}</td>
                    <td className="px-4 py-2.5 text-xs text-slate-500">{c.compatible_berths.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alt Ports */}
        <div className="rounded-2xl border border-port-line bg-port-panel shadow-card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-port-line px-5 py-3.5">
            <Globe className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-port-text">Alternative Ports ({data.alt_ports.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[300px]">
              <thead>
                <tr className="border-b border-port-line bg-slate-50/80">
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">ID</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Name</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-port-line">
                {data.alt_ports.map((p) => (
                  <tr key={p.id} className="hover:bg-port-panelHover transition-colors">
                    <td className="px-4 py-2.5 text-xs font-medium text-slate-500">{p.id}</td>
                    <td className="px-4 py-2.5 text-sm font-medium text-port-text">{p.name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

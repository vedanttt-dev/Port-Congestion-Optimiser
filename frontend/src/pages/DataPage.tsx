import { useEffect, useState } from 'react';
import { api, DataSummary } from '../api';

type SortDir = 'asc' | 'desc';

export default function DataPage() {
  const [data, setData] = useState<DataSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  useEffect(() => {
    api.data()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortCol(col);
      setSortDir('asc');
    }
  };

  const filterMatch = (text: string) =>
    search === '' || text.toLowerCase().includes(search.toLowerCase());

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-10 w-full rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load data</p>;

  const totalYardCapacity = data.yard_zones.reduce((s, z) => s + z.teu_capacity, 0);
  const totalYardCurrent = data.yard_zones.reduce((s, z) => s + z.current_teu, 0);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Scenario Data</h2>

      {/* Search bar */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search vessels, berths, cranes, zones…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-port-line bg-port-panel px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-port-accent focus:outline-none focus:ring-1 focus:ring-port-accent"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
          >
            Clear
          </button>
        )}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="Vessels" value={data.vessels.length} />
        <Stat label="Berths" value={data.berths.length} />
        <Stat label="Cranes" value={data.cranes.length} />
        <Stat label="Yard Zones" value={data.yard_zones.length} />
        <Stat label="Alt Ports" value={data.alt_ports.length} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Vessels */}
        <SortableTable
          title={`Vessels (${data.vessels.length})`}
          headers={[
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
            { key: 'type', label: 'Type' },
            { key: 'teu', label: 'TEU' },
            { key: 'priority', label: 'Priority' },
          ]}
          sortCol={sortCol}
          sortDir={sortDir}
          onSort={handleSort}
        >
          {data.vessels
            .filter((v) => filterMatch(`${v.id} ${v.name} ${v.type}`))
            .sort((a, b) => {
              if (!sortCol) return 0;
              const dir = sortDir === 'asc' ? 1 : -1;
              switch (sortCol) {
                case 'id': return a.id.localeCompare(b.id) * dir;
                case 'name': return a.name.localeCompare(b.name) * dir;
                case 'type': return a.type.localeCompare(b.type) * dir;
                case 'teu': return (a.teu_capacity - b.teu_capacity) * dir;
                case 'priority': return (a.priority_class - b.priority_class) * dir;
                default: return 0;
              }
            })
            .map((v) => (
              <tr key={v.id} className="border-t border-port-line hover:bg-port-bg/40">
                <td className="px-3 py-2 text-xs text-slate-400">{v.id}</td>
                <td className="px-3 py-2 text-sm text-white">{v.name}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${
                    v.type === 'mega' ? 'bg-purple-500/20 text-purple-400' :
                    v.type === 'medium' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-slate-500/20 text-slate-400'
                  }`}>{v.type}</span>
                </td>
                <td className="px-3 py-2 text-xs text-slate-300">{v.teu_capacity.toLocaleString()}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${
                    v.priority_class === 1 ? 'bg-red-500/20 text-red-400' :
                    v.priority_class === 2 ? 'bg-amber-500/20 text-amber-400' :
                    'bg-slate-500/20 text-slate-400'
                  }`}>P{v.priority_class}</span>
                </td>
              </tr>
            ))}
        </SortableTable>

        {/* Berths */}
        <SortableTable
          title={`Berths (${data.berths.length})`}
          headers={[
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
            { key: 'length', label: 'Length' },
            { key: 'draft', label: 'Draft' },
          ]}
          sortCol={sortCol}
          sortDir={sortDir}
          onSort={handleSort}
        >
          {data.berths
            .filter((b) => filterMatch(`${b.id} ${b.name}`))
            .sort((a, b) => {
              if (!sortCol) return 0;
              const dir = sortDir === 'asc' ? 1 : -1;
              switch (sortCol) {
                case 'id': return a.id.localeCompare(b.id) * dir;
                case 'name': return a.name.localeCompare(b.name) * dir;
                case 'length': return (a.length_m - b.length_m) * dir;
                case 'draft': return (a.max_draft_m - b.max_draft_m) * dir;
                default: return 0;
              }
            })
            .map((b) => (
              <tr key={b.id} className="border-t border-port-line hover:bg-port-bg/40">
                <td className="px-3 py-2 text-xs text-slate-400">{b.id}</td>
                <td className="px-3 py-2 text-sm text-white">{b.name}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{b.length_m}m</td>
                <td className="px-3 py-2 text-xs text-slate-300">{b.max_draft_m}m</td>
              </tr>
            ))}
        </SortableTable>

        {/* Cranes */}
        <SortableTable
          title={`Cranes (${data.cranes.length})`}
          headers={[
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
            { key: 'moves', label: 'Moves/h' },
          ]}
          sortCol={sortCol}
          sortDir={sortDir}
          onSort={handleSort}
        >
          {data.cranes
            .filter((c) => filterMatch(`${c.id} ${c.name}`))
            .sort((a, b) => {
              if (!sortCol) return 0;
              const dir = sortDir === 'asc' ? 1 : -1;
              switch (sortCol) {
                case 'id': return a.id.localeCompare(b.id) * dir;
                case 'name': return a.name.localeCompare(b.name) * dir;
                case 'moves': return (a.moves_per_h - b.moves_per_h) * dir;
                default: return 0;
              }
            })
            .map((c) => (
              <tr key={c.id} className="border-t border-port-line hover:bg-port-bg/40">
                <td className="px-3 py-2 text-xs text-slate-400">{c.id}</td>
                <td className="px-3 py-2 text-sm text-white">{c.name}</td>
                <td className="px-3 py-2 text-xs text-slate-300">{c.moves_per_h}</td>
              </tr>
            ))}
        </SortableTable>

        {/* Yard Zones with capacity bars */}
        <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-port-line px-4 py-3">
            <h3 className="text-sm font-medium text-white">
              Yard Zones ({data.yard_zones.length})
            </h3>
            <span className="text-xs text-slate-400">
              Total: {totalYardCurrent.toLocaleString()} / {totalYardCapacity.toLocaleString()} TEU
            </span>
          </div>

          {/* Overall yard bar */}
          <div className="border-b border-port-line px-4 py-3">
            <div className="mb-1 flex justify-between text-xs text-slate-400">
              <span>Overall Utilisation</span>
              <span>{totalYardCapacity > 0 ? ((totalYardCurrent / totalYardCapacity) * 100).toFixed(0) : 0}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-port-bg">
              <div
                className={`h-full rounded-full transition-all ${
                  (totalYardCurrent / totalYardCapacity) > 0.85 ? 'bg-red-500' :
                  (totalYardCurrent / totalYardCapacity) > 0.70 ? 'bg-amber-500' :
                  'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, (totalYardCurrent / totalYardCapacity) * 100)}%` }}
              />
            </div>
          </div>

          <div className="divide-y divide-port-line">
            {data.yard_zones
              .filter((z) => filterMatch(`${z.id} ${z.name}`))
              .sort((a, b) => {
                if (sortCol === 'util') return ((a.current_teu / a.teu_capacity) - (b.current_teu / b.teu_capacity)) * (sortDir === 'asc' ? 1 : -1);
                if (sortCol === 'capacity') return (a.teu_capacity - b.teu_capacity) * (sortDir === 'asc' ? 1 : -1);
                return 0;
              })
              .map((z) => {
                const util = z.teu_capacity > 0 ? (z.current_teu / z.teu_capacity) * 100 : 0;
                return (
                  <div key={z.id} className="px-4 py-3 hover:bg-port-bg/40">
                    <div className="flex items-center justify-between mb-1">
                      <div>
                        <span className="text-sm text-white">{z.name}</span>
                        <span className="ml-2 text-xs text-slate-500">{z.id}</span>
                      </div>
                      <span className="text-xs text-slate-400">
                        {z.current_teu.toLocaleString()} / {z.teu_capacity.toLocaleString()} TEU
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-port-bg">
                        <div
                          className={`h-full rounded-full transition-all ${
                            util > 85 ? 'bg-red-500' : util > 70 ? 'bg-amber-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, util)}%` }}
                        />
                      </div>
                      <span className={`text-xs font-medium ${
                        util > 85 ? 'text-red-400' : util > 70 ? 'text-amber-400' : 'text-emerald-400'
                      }`}>{util.toFixed(0)}%</span>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Alt Ports */}
        <SortableTable
          title={`Alt Ports (${data.alt_ports.length})`}
          headers={[
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Name' },
          ]}
          sortCol={sortCol}
          sortDir={sortDir}
          onSort={handleSort}
        >
          {data.alt_ports
            .filter((p) => filterMatch(`${p.id} ${p.name}`))
            .map((p) => (
              <tr key={p.id} className="border-t border-port-line hover:bg-port-bg/40">
                <td className="px-3 py-2 text-xs text-slate-400">{p.id}</td>
                <td className="px-3 py-2 text-sm text-white">{p.name}</td>
              </tr>
            ))}
        </SortableTable>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-port-line bg-port-panel px-3 py-2">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function SortableTable({
  title,
  headers,
  sortCol,
  sortDir,
  onSort,
  children,
}: {
  title: string;
  headers: { key: string; label: string }[];
  sortCol: string | null;
  sortDir: SortDir;
  onSort: (col: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
      <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">{title}</h3>
      <table className="w-full">
        <thead>
          <tr className="border-b border-port-line">
            {headers.map((h) => (
              <th
                key={h.key}
                onClick={() => onSort(h.key)}
                className="cursor-pointer px-3 py-2 text-left text-xs font-medium text-slate-400 hover:text-white select-none"
              >
                {h.label}
                {sortCol === h.key && (
                  <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

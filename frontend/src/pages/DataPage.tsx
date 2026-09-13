import { useEffect, useState } from 'react';
import { api, DataSummary } from '../api';

export default function DataPage() {
  const [data, setData] = useState<DataSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.data()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse space-y-4">
    <div className="h-8 w-48 rounded bg-port-panel" />
    <div className="h-64 rounded-xl bg-port-panel" />
  </div>;

  if (!data) return <p className="text-red-400">Failed to load data</p>;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Scenario Data</h2>

      <div className="grid gap-4 md:grid-cols-2">
        <Table title={`Vessels (${data.vessels.length})`} headers={['ID', 'Name', 'Type', 'TEU', 'Priority']}>
          {data.vessels.map((v) => (
            <tr key={v.id} className="border-t border-port-line">
              <td className="px-3 py-2 text-xs text-slate-400">{v.id}</td>
              <td className="px-3 py-2 text-sm text-white">{v.name}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{v.type}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{v.teu_capacity}</td>
              <td className="px-3 py-2 text-xs text-slate-300">P{v.priority_class}</td>
            </tr>
          ))}
        </Table>

        <Table title={`Berths (${data.berths.length})`} headers={['ID', 'Name', 'Length', 'Draft']}>
          {data.berths.map((b) => (
            <tr key={b.id} className="border-t border-port-line">
              <td className="px-3 py-2 text-xs text-slate-400">{b.id}</td>
              <td className="px-3 py-2 text-sm text-white">{b.name}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{b.length_m}m</td>
              <td className="px-3 py-2 text-xs text-slate-300">{b.max_draft_m}m</td>
            </tr>
          ))}
        </Table>

        <Table title={`Cranes (${data.cranes.length})`} headers={['ID', 'Name', 'Moves/h']}>
          {data.cranes.map((c) => (
            <tr key={c.id} className="border-t border-port-line">
              <td className="px-3 py-2 text-xs text-slate-400">{c.id}</td>
              <td className="px-3 py-2 text-sm text-white">{c.name}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{c.moves_per_h}</td>
            </tr>
          ))}
        </Table>

        <Table title={`Yard Zones (${data.yard_zones.length})`} headers={['ID', 'Name', 'Capacity', 'Current', 'Util%']}>
          {data.yard_zones.map((z) => (
            <tr key={z.id} className="border-t border-port-line">
              <td className="px-3 py-2 text-xs text-slate-400">{z.id}</td>
              <td className="px-3 py-2 text-sm text-white">{z.name}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{z.teu_capacity}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{z.current_teu}</td>
              <td className="px-3 py-2 text-xs text-slate-300">{(z.current_teu / z.teu_capacity * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </Table>
      </div>
    </div>
  );
}

function Table({ title, headers, children }: { title: string; headers: string[]; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-port-line bg-port-panel overflow-hidden">
      <h3 className="border-b border-port-line px-4 py-3 text-sm font-medium text-white">{title}</h3>
      <table className="w-full">
        <thead>
          <tr className="border-b border-port-line">
            {headers.map((h) => (
              <th key={h} className="px-3 py-2 text-left text-xs font-medium text-slate-400">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

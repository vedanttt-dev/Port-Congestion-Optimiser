import { useEffect, useState } from 'react';
import { api, Health } from '../api';

export default function StatusBadge() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const poll = () => {
      api.health()
        .then(setHealth)
        .catch((e) => setError(String(e)));
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => clearInterval(id);
  }, []);

  const badge = health
    ? health.status === 'ok'
      ? { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', label: 'API online' }
      : { color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', label: health.status }
    : error
      ? { color: 'bg-red-500/20 text-red-400 border-red-500/30', label: 'API offline' }
      : { color: 'bg-slate-500/20 text-slate-400 border-slate-500/30', label: 'connecting…' };

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${badge.color}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {badge.label}
    </span>
  );
}

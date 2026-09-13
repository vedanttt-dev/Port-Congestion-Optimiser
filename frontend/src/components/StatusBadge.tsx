import { useEffect, useState } from 'react';
import { api, Health } from '../api';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';

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
      ? {
          bg: 'bg-emerald-50 border-emerald-200',
          dot: 'bg-emerald-500',
          text: 'text-emerald-700',
          icon: Wifi,
          label: 'API Online',
        }
      : {
          bg: 'bg-amber-50 border-amber-200',
          dot: 'bg-amber-500',
          text: 'text-amber-700',
          icon: Wifi,
          label: health.status,
        }
    : error
      ? {
          bg: 'bg-red-50 border-red-200',
          dot: 'bg-red-500',
          text: 'text-red-600',
          icon: WifiOff,
          label: 'Offline',
        }
      : {
          bg: 'bg-slate-50 border-slate-200',
          dot: 'bg-slate-400',
          text: 'text-slate-500',
          icon: Loader2,
          label: 'Connecting',
        };

  const Icon = badge.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${badge.bg} ${badge.text}`}
    >
      <Icon className={`h-3 w-3 ${!health && !error ? 'animate-spin' : ''}`} />
      {badge.label}
    </span>
  );
}

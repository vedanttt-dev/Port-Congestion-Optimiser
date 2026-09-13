import { Anchor } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Header() {
  return (
    <header className="flex items-center gap-4 border-b border-port-line bg-port-panel px-8 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 shadow-sm shadow-brand-600/20">
          <Anchor className="h-5 w-5 text-white" strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-port-text">
            Port Congestion Optimiser
          </h1>
          <p className="text-xs text-port-muted">
            Container Congestion Predictor &amp; Port Operations Optimiser
          </p>
        </div>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <StatusBadge />
      </div>
    </header>
  );
}

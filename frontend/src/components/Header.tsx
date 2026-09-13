import { Anchor, Menu } from 'lucide-react';
import { useSidebar } from './Layout';
import StatusBadge from './StatusBadge';

export default function Header() {
  const { toggle } = useSidebar();

  return (
    <header className="flex items-center gap-3 border-b border-port-line bg-port-panel px-4 py-3 sm:px-6 lg:px-8">
      <button
        onClick={toggle}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-port-muted hover:bg-port-panelHover lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 shadow-sm shadow-brand-600/20">
          <Anchor className="h-5 w-5 text-white" strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-port-text sm:text-base">
            Port Congestion Optimiser
          </h1>
          <p className="hidden text-xs text-port-muted sm:block">
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

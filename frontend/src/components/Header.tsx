import StatusBadge from './StatusBadge';

export default function Header() {
  return (
    <header className="flex items-center gap-4 border-b border-port-line bg-port-panel/60 px-6 py-4">
      <span className="text-2xl">🚢</span>
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-white">
          Port Congestion Optimiser
        </h1>
        <p className="text-xs text-slate-400">
          Container Congestion Predictor &amp; Port Operations Optimiser
        </p>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <StatusBadge />
      </div>
    </header>
  );
}

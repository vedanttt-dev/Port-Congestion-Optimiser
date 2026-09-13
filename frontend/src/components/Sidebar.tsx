import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  BrainCircuit,
  Settings2,
  CalendarClock,
  Radar,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/data', label: 'Data', icon: Database },
  { to: '/predict', label: 'Prediction', icon: BrainCircuit },
  { to: '/optimize', label: 'Optimiser', icon: Settings2 },
  { to: '/plan', label: 'Shift Plan', icon: CalendarClock },
  { to: '/live', label: 'Live Map', icon: Radar },
] as const;

export default function Sidebar() {
  return (
    <aside className="flex w-60 flex-col border-r border-port-line bg-port-panel py-5">
      <nav className="flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-brand-600/10 text-brand-600 shadow-sm shadow-brand-600/5'
                  : 'text-port-muted hover:bg-port-panelHover hover:text-port-text'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={`h-4.5 w-4.5 shrink-0 transition-colors ${
                    isActive ? 'text-brand-600' : 'text-port-muted group-hover:text-port-text'
                  }`}
                  strokeWidth={isActive ? 2.2 : 1.8}
                />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto px-3">
        <div className="rounded-lg border border-port-line bg-port-bg px-3 py-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-port-muted">
            System Status
          </p>
          <p className="mt-1 text-xs text-port-text">
            Sim engine ready
          </p>
        </div>
      </div>
    </aside>
  );
}

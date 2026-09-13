import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: '📊' },
  { to: '/data', label: 'Data', icon: '📦' },
  { to: '/predict', label: 'Prediction', icon: '🔮' },
  { to: '/optimize', label: 'Optimiser', icon: '⚙️' },
  { to: '/plan', label: 'Shift Plan', icon: '📋' },
  { to: '/live', label: 'Live Map', icon: '🗺️' },
];

export default function Sidebar() {
  return (
    <aside className="flex w-56 flex-col border-r border-port-line bg-port-panel/40 py-4">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) =>
            `flex items-center gap-3 px-5 py-2.5 text-sm transition-colors ${
              isActive
                ? 'bg-port-accent/10 text-port-accent border-r-2 border-port-accent'
                : 'text-slate-400 hover:bg-port-panel/60 hover:text-slate-200'
            }`
          }
        >
          <span className="text-base">{item.icon}</span>
          {item.label}
        </NavLink>
      ))}
    </aside>
  );
}

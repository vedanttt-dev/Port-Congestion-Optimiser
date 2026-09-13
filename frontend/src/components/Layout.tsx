import { useState, createContext, useContext } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

const SidebarCtx = createContext({ open: false, toggle: () => {} });
export const useSidebar = () => useContext(SidebarCtx);

export default function Layout() {
  const { pathname } = useLocation();
  const isOverview = pathname === '/';
  const [open, setOpen] = useState(false);

  return (
    <SidebarCtx.Provider value={{ open, toggle: () => setOpen((v) => !v) }}>
      <div className="flex h-screen flex-col bg-port-bg font-sans">
        <div className="h-1 w-full bg-gradient-to-r from-brand-600 via-brand-400 to-blue-300" />
        <Header />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          {open && (
            <div
              className="fixed inset-0 z-40 bg-black/40 lg:hidden"
              onClick={() => setOpen(false)}
            />
          )}
          <main className={`flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8${isOverview ? ' main-overview-bg' : ''}`}>
            <div className="mx-auto max-w-[1400px]">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </SidebarCtx.Provider>
  );
}

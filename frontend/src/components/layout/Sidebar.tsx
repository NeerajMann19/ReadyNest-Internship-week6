import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BarChart3,
  Sparkles,
  FileText,
  Compass,
  Sun,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Predictions', path: '/predictions', icon: Sparkles },
  { name: 'Report', path: '/report', icon: FileText },
  { name: 'Decision Center', path: '/decision', icon: Compass },
];

/**
 * Sidebar Component
 * Presentational fixed navigation sidebar with responsive structural classes.
 */
export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-surface border-r border-border h-screen flex flex-col justify-between fixed left-0 top-0 z-30 transition-all duration-200 hidden md:flex">
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center px-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-sm">
              AS
            </div>
            <span className="font-semibold text-text-primary text-base tracking-tight">
              Analytics Studio
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-elevated text-text-primary font-semibold border border-border'
                      : 'text-text-secondary hover:text-text-primary hover:bg-elevated/50'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Non-functional Theme Toggle Placeholder */}
      <div className="p-4 border-t border-border space-y-3">
        <div className="flex items-center justify-between px-2 text-xs text-text-muted">
          <span>Version</span>
          <span className="font-mono bg-elevated px-1.5 py-0.5 rounded border border-border">
            v1.0.0
          </span>
        </div>

        {/* Visual Theme Toggle Placeholder (Non-functional by requirement) */}
        <button
          type="button"
          disabled
          className="w-full flex items-center justify-between px-3 py-2 text-xs text-text-muted bg-elevated/40 border border-border rounded-lg opacity-70 cursor-not-allowed"
        >
          <span className="flex items-center gap-2">
            <Sun className="w-3.5 h-3.5" />
            <span>Dark Theme</span>
          </span>
          <span className="text-[10px] uppercase font-mono px-1 bg-border rounded">Default</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;

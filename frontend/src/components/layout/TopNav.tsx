import React from 'react';
import { useLocation } from 'react-router-dom';
import { Moon, Database } from 'lucide-react';
import { useSession } from '../../context/SessionContext';

const ROUTE_TITLES: Record<string, string> = {
  '/': 'Overview',
  '/analytics': 'Analytics',
  '/predictions': 'Predictions',
  '/report': 'Executive Report',
  '/decision': 'Decision Center',
};

/**
 * TopNav Component
 * Presentational top header bar displaying route title, active dataset, and session status indicator.
 */
export const TopNav: React.FC = () => {
  const location = useLocation();
  const { dataset, sessionId } = useSession();
  const pageTitle = ROUTE_TITLES[location.pathname] || 'Analytics Studio';

  return (
    <header className="h-16 bg-surface border-b border-border px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left Title & Active Dataset Indicator */}
      <div className="flex items-center gap-4">
        <h2 className="text-base font-semibold text-text-primary tracking-tight">
          {pageTitle}
        </h2>
        <div className="h-4 w-[1px] bg-border hidden sm:block" />
        <div className="hidden sm:flex items-center gap-2 text-xs text-text-muted">
          <Database className="w-3.5 h-3.5 text-text-secondary" />
          <span className="font-medium text-text-secondary">
            {dataset ? dataset.filename : 'No dataset loaded'}
          </span>
        </div>
      </div>

      {/* Right Action Placeholders */}
      <div className="flex items-center gap-3">
        {/* Upload Dataset Indicator / Quick Badge */}
        {dataset && (
          <div className="hidden md:flex items-center gap-2 px-2.5 py-1 text-xs font-mono bg-elevated border border-border rounded-md text-text-secondary">
            <span>{dataset.rows} rows</span>
            <span>•</span>
            <span>{dataset.columns} cols</span>
          </div>
        )}

        {/* Session Status Badge */}
        <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-text-muted bg-elevated border border-border rounded-full">
          <span
            className={`w-2 h-2 rounded-full ${
              sessionId ? 'bg-success' : 'bg-text-muted'
            }`}
          />
          <span>{sessionId ? 'Active Session' : 'Idle Session'}</span>
        </span>

        {/* Visual Theme Toggle Placeholder */}
        <button
          type="button"
          disabled
          className="p-1.5 text-text-muted bg-elevated border border-border rounded-md opacity-60 cursor-not-allowed"
          title="Dark Theme (Default)"
        >
          <Moon className="w-4 h-4 text-text-secondary" />
        </button>
      </div>
    </header>
  );
};

export default TopNav;

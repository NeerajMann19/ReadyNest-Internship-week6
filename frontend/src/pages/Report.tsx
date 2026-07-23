import React from 'react';
import { useSession } from '../context/SessionContext';

/**
 * Report Page Placeholder
 * Displays prompt to upload a dataset if no active session exists.
 */
export const Report: React.FC = () => {
  const { dataset } = useSession();

  if (!dataset) {
    return (
      <div className="p-8 text-center border border-dashed border-border rounded-xl bg-surface space-y-2">
        <h2 className="text-xl font-semibold text-text-primary">No Dataset Uploaded</h2>
        <p className="text-text-secondary text-sm">
          No dataset uploaded — upload one from Overview to generate executive reports.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h1 className="text-3xl font-bold tracking-tight text-text-primary">Executive Report</h1>
      <p className="text-text-secondary text-sm">
        Active Dataset: <span className="font-mono text-text-primary">{dataset.filename}</span> ({dataset.rows} rows, {dataset.columns} columns).
      </p>
    </div>
  );
};

export default Report;

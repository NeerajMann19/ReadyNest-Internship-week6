import React, { useState, useRef } from 'react';
import { Upload, CheckCircle2, AlertTriangle, X, RefreshCw, Layers, Hash, Sparkles } from 'lucide-react';
import { useSession } from '../context/SessionContext';

export const Overview: React.FC = () => {
  const { dataset, loading, error, uploadDataset, clearSession, clearError } = useSession();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelected = (file: File) => {
    if (!file) return;
    uploadDataset(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (loading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!loading) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">Overview</h1>
          <p className="text-text-secondary text-sm">
            {dataset ? `Dataset Summary for ${dataset.filename}` : 'Upload your dataset to begin analysis.'}
          </p>
        </div>
        {dataset && (
          <button
            type="button"
            onClick={clearSession}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-text-secondary bg-elevated hover:bg-border border border-border rounded-lg transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Upload New Dataset</span>
          </button>
        )}
      </div>

      {/* Dismissible Error Banner */}
      {error && (
        <div className="p-4 bg-danger/10 border border-danger/30 rounded-lg flex items-start justify-between text-danger text-sm">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
          <button type="button" onClick={clearError} className="text-danger/70 hover:text-danger">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Empty / Upload State */}
      {!dataset && (
        <div className="space-y-6">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`p-12 border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-center transition-all ${
              isDragging
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-text-muted bg-surface'
            } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
            />

            {loading ? (
              <div className="space-y-3 flex flex-col items-center">
                <RefreshCw className="w-10 h-10 text-primary animate-spin" />
                <p className="text-sm font-medium text-text-primary">Processing CSV dataset...</p>
                <p className="text-xs text-text-muted">Cleaning duplicates and scoring quality</p>
              </div>
            ) : (
              <div className="space-y-4 max-w-md">
                <div className="w-12 h-12 rounded-full bg-elevated border border-border flex items-center justify-center mx-auto text-primary">
                  <Upload className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">Upload CSV Dataset</h3>
                  <p className="text-xs text-text-secondary mt-1">
                    Drag and drop your file here, or click browse (UTF-8 encoded CSV, max 25MB).
                  </p>
                </div>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors shadow-sm disabled:opacity-50"
                >
                  Browse Files
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Active Dataset Dashboard */}
      {dataset && (
        <div className="space-y-6">
          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Rows Card */}
            <div className="p-5 bg-card border border-border rounded-xl space-y-2">
              <div className="flex items-center justify-between text-text-muted">
                <span className="text-xs font-medium uppercase tracking-wider">Total Rows</span>
                <Hash className="w-4 h-4 text-text-secondary" />
              </div>
              <p className="text-2xl font-bold text-text-primary">{dataset.rows.toLocaleString()}</p>
              <p className="text-xs text-text-secondary">Cleaned rows</p>
            </div>

            {/* Total Columns Card */}
            <div className="p-5 bg-card border border-border rounded-xl space-y-2">
              <div className="flex items-center justify-between text-text-muted">
                <span className="text-xs font-medium uppercase tracking-wider">Total Columns</span>
                <Layers className="w-4 h-4 text-text-secondary" />
              </div>
              <p className="text-2xl font-bold text-text-primary">{dataset.columns}</p>
              <p className="text-xs text-text-secondary">Inferred schemas</p>
            </div>

            {/* Quality Score Card */}
            <div className="p-5 bg-card border border-border rounded-xl space-y-2">
              <div className="flex items-center justify-between text-text-muted">
                <span className="text-xs font-medium uppercase tracking-wider">Quality Score</span>
                <Sparkles className="w-4 h-4 text-primary" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{dataset.quality.quality_score}%</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    dataset.quality.quality_score >= 90
                      ? 'bg-success/20 text-success'
                      : dataset.quality.quality_score >= 70
                      ? 'bg-warning/20 text-warning'
                      : 'bg-danger/20 text-danger'
                  }`}
                >
                  {dataset.quality.quality_score >= 90 ? 'Excellent' : 'Needs Review'}
                </span>
              </div>
              <p className="text-xs text-text-secondary">Data completeness score</p>
            </div>

            {/* Duplicates Removed Card */}
            <div className="p-5 bg-card border border-border rounded-xl space-y-2">
              <div className="flex items-center justify-between text-text-muted">
                <span className="text-xs font-medium uppercase tracking-wider">Duplicates Removed</span>
                <CheckCircle2 className="w-4 h-4 text-success" />
              </div>
              <p className="text-2xl font-bold text-text-primary">{dataset.quality.duplicate_rows_count}</p>
              <p className="text-xs text-text-secondary">{dataset.quality.missing_values_count} missing cells</p>
            </div>
          </div>

          {/* Column Schema Preview Table (First 10 columns) */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Column Schema Preview</h3>
                <p className="text-xs text-text-secondary">
                  Showing first {Math.min(10, dataset.schema.length)} of {dataset.columns} columns
                </p>
              </div>
              {dataset.schema.length > 10 && (
                <span className="text-xs font-mono bg-elevated px-2 py-1 rounded border border-border text-text-secondary">
                  +{dataset.schema.length - 10} more columns
                </span>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-border text-text-muted uppercase tracking-wider bg-surface">
                  <tr>
                    <th className="py-3 px-4">Column Name</th>
                    <th className="py-3 px-4">Inferred Type</th>
                    <th className="py-3 px-4">Missing Count</th>
                    <th className="py-3 px-4">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {dataset.schema.slice(0, 10).map((col) => (
                    <tr key={col.name} className="hover:bg-elevated/40">
                      <td className="py-3 px-4 font-mono font-medium text-text-primary">{col.name}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-elevated border border-border text-text-secondary uppercase">
                          {col.data_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text-secondary">{col.missing_count}</td>
                      <td className="py-3 px-4 text-text-muted font-mono truncate max-w-xs">
                        {col.sample_values.length > 0 ? col.sample_values.join(', ') : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Overview;
